"""Liga o Superset à camada semântica (Cube) e cria o dashboard de exemplo.

O Superset é a segunda superfície de consumo da camada semântica: ele fala com
o Cube pela SQL API (protocolo Postgres), então enxerga `titles_overview` como
uma tabela e as medidas/dimensões governadas como colunas. Nenhum SQL ad-hoc é
escrito em gráfico nenhum — as definições vivem no Cube (cube/model).

Este script usa a REST API pública do Superset (a mesma que o `curl` do aluno
usa) em vez das models internas do Flask, que mudam a cada versão. É
idempotente: rodar de novo só atualiza o que já existe.

Roda dentro do container do Superset (ver o serviço `superset-bootstrap` no
docker-compose.yml).
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import requests

SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://superset:8088")
SUPERSET_ADMIN_USER = os.environ.get("SUPERSET_ADMIN_USER", "admin")
SUPERSET_ADMIN_PASSWORD = os.environ.get("SUPERSET_ADMIN_PASSWORD", "secret")

# A credencial da SQL API do Cube é a mesma que o Cube lê (cube/.env), para não
# existirem duas verdades sobre a mesma senha.
CUBE_SQL_USER = os.environ["CUBEJS_SQL_USER"]
CUBE_SQL_PASSWORD = os.environ["CUBEJS_SQL_PASSWORD"]
CUBE_SQL_PORT = os.environ["CUBEJS_PG_SQL_PORT"]

DATABASE_NAME = "Cube — camada semântica"
DATASET_TABLE = "titles_overview"
DATASET_SCHEMA = "public"

# Medidas do Cube vistas pelo Superset. A forma canônica na SQL API é envolver a
# medida com `MEASURE(...)`: funciona com medida de qualquer tipo e deixa o Cube
# escolher a agregação. (As alternativas `AVG(...)`/`COUNT(DISTINCT ...)` também
# existem, mas precisam casar com o tipo da medida — ver
# docs.cube.dev/reference/core-data-apis/sql-api/query-format.)
METRICS = [
    {
        "metric_name": "count_titles",
        "verbose_name": "Títulos",
        "expression": "MEASURE(count_titles)",
        "metric_type": "count_distinct",
        "description": "Quantidade de títulos distintos.",
    },
    {
        "metric_name": "avg_rating",
        "verbose_name": "Nota média",
        "expression": "MEASURE(avg_rating)",
        "metric_type": "avg",
        "description": "Nota média da crítica.",
    },
    {
        "metric_name": "total_votes",
        "verbose_name": "Total de votos",
        "expression": "MEASURE(total_votes)",
        "metric_type": "sum",
        "description": "Soma dos votos recebidos.",
    },
    {
        "metric_name": "count_imdb_top_1000",
        "verbose_name": "Títulos no IMDB Top 1000",
        "expression": "MEASURE(count_imdb_top_1000)",
        "metric_type": "sum",
        "description": "Quantidade de títulos presentes no Top 1000 do IMDB.",
    },
    {
        "metric_name": "avg_imdb_rating",
        "verbose_name": "Nota média IMDB",
        "expression": "MEASURE(avg_imdb_rating)",
        "metric_type": "avg",
        "description": "Nota média do público no IMDB Top 1000.",
    },
]

DASHBOARD_TITLE = "Camada semântica — títulos"


def cube_sqlalchemy_uri() -> str:
    user = quote_plus(CUBE_SQL_USER)
    password = quote_plus(CUBE_SQL_PASSWORD)
    return f"postgresql+psycopg2://{user}:{password}@cube:{CUBE_SQL_PORT}/cube"


@dataclass(frozen=True)
class ChartSpec:
    name: str
    description: str
    viz_type: str
    form_data: dict


CHARTS = [
    ChartSpec(
        name="Nota média por país",
        description="Top 10 países por nota média (medida avg_rating do Cube).",
        viz_type="echarts_timeseries_bar",
        form_data={
            "viz_type": "echarts_timeseries_bar",
            "x_axis": "country",
            "metrics": ["avg_rating"],
            "groupby": [],
            "adhoc_filters": [],
            "row_limit": 10,
            "order_desc": True,
            "timeseries_limit_metric": "avg_rating",
            "y_axis_format": ".2f",
            # barras ordenadas pela própria medida, da maior para a menor
            "x_axis_sort": "avg_rating",
            "x_axis_sort_asc": False,
            "x_axis_label": "País",
            "y_axis_label": "Nota média",
            "show_legend": False,
            "rich_tooltip": True,
        },
    ),
    ChartSpec(
        name="Medidas por tipo de título",
        description="Medidas governadas (títulos, nota média, votos) por tipo.",
        viz_type="table",
        form_data={
            "viz_type": "table",
            "query_mode": "aggregate",
            "groupby": ["title_type"],
            "metrics": ["count_titles", "avg_rating", "total_votes"],
            "adhoc_filters": [],
            "row_limit": 100,
            "order_desc": True,
            "timeseries_limit_metric": "count_titles",
        },
    ),
    ChartSpec(
        name="Top 10 Gêneros no IMDB Top 1000",
        description="Volume de títulos presentes no IMDB Top 1000 por gênero.",
        viz_type="echarts_timeseries_bar",
        form_data={
            "viz_type": "echarts_timeseries_bar",
            "orientation": "horizontal",
            "x_axis": "genre",
            "metrics": ["count_imdb_top_1000"],
            "groupby": [],
            "adhoc_filters": [
                {
                    "expressionType": "SIMPLE",
                    "subject": "count_imdb_top_1000",
                    "operator": ">",
                    "comparator": "0",
                    "clause": "HAVING",
                }
            ],
            "row_limit": 10,
            "order_desc": True,
            "timeseries_limit_metric": "count_imdb_top_1000",
            "x_axis_sort": "count_imdb_top_1000",
            "x_axis_sort_asc": True,
            "x_axis_label": "Gênero",
            "y_axis_label": "Títulos no IMDB Top 1000",
            "show_legend": False,
            "show_value": True,
            "rich_tooltip": True,
        },
    ),
    ChartSpec(
        name="Nota IMDB vs. Crítica por Gênero",
        description="Comparação entre nota média do público (IMDB) e da crítica (Metacritic) nos gêneros com mais títulos no Top 1000.",
        viz_type="echarts_timeseries_bar",
        form_data={
            "viz_type": "echarts_timeseries_bar",
            "orientation": "vertical",
            "x_axis": "genre",
            "metrics": ["avg_imdb_rating", "avg_rating"],
            "groupby": [],
            "adhoc_filters": [
                {
                    "expressionType": "SIMPLE",
                    "subject": "count_imdb_top_1000",
                    "operator": ">",
                    "comparator": "0",
                    "clause": "HAVING",
                }
            ],
            "row_limit": 10,
            "order_desc": True,
            "timeseries_limit_metric": "avg_imdb_rating",
            "x_axis_sort": "avg_imdb_rating",
            "x_axis_sort_asc": False,
            "y_axis_bounds": [0, 10],
            "y_axis_format": ".2f",
            "x_axis_label": "Gênero",
            "y_axis_label": "Nota média (0–10)",
            "show_legend": True,
            "show_value": True,
            "rich_tooltip": True,
        },
    ),
]


class SupersetApi:
    """Cliente mínimo da REST API do Superset (login, CSRF e CRUD)."""

    def __init__(self, base_url: str, user: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.user = user
        self.password = password
        self.access_token = ""
        self.csrf_token = ""

    def wait_until_ready(self, timeout: int = 300) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.session.get(f"{self.base_url}/health", timeout=5).ok:
                    return
            except requests.RequestException:
                pass
            time.sleep(3)
        raise SystemExit(f"Superset não respondeu em {self.base_url} a tempo")

    def login(self) -> None:
        response = self.session.post(
            f"{self.base_url}/api/v1/security/login",
            json={
                "username": self.user,
                "password": self.password,
                "provider": "db",
                "refresh": True,
            },
        )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]
        csrf = self.session.get(
            f"{self.base_url}/api/v1/security/csrf_token/", headers=self.headers()
        )
        csrf.raise_for_status()
        self.csrf_token = csrf.json()["result"]

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    def write_headers(self) -> dict:
        return {
            **self.headers(),
            "X-CSRFToken": self.csrf_token,
            "Referer": self.base_url,
        }

    def list(self, resource: str) -> list[dict]:
        response = self.session.get(
            f"{self.base_url}/api/v1/{resource}/",
            params={"q": "(page_size:200)"},
            headers=self.headers(),
        )
        response.raise_for_status()
        return response.json().get("result", [])

    def get(self, resource: str, pk: int) -> dict:
        response = self.session.get(
            f"{self.base_url}/api/v1/{resource}/{pk}", headers=self.headers()
        )
        response.raise_for_status()
        return response.json()["result"]

    def create(self, resource: str, payload: dict) -> int:
        response = self.session.post(
            f"{self.base_url}/api/v1/{resource}/",
            json=payload,
            headers=self.write_headers(),
        )
        if not response.ok:
            raise SystemExit(f"Falha ao criar {resource}: {response.text}")
        return response.json()["id"]

    def update(self, resource: str, pk: int, payload: dict) -> None:
        response = self.session.put(
            f"{self.base_url}/api/v1/{resource}/{pk}",
            json=payload,
            headers=self.write_headers(),
        )
        if not response.ok:
            raise SystemExit(f"Falha ao atualizar {resource}/{pk}: {response.text}")

    def delete(self, resource: str) -> None:
        response = self.session.delete(
            f"{self.base_url}/api/v1/{resource}", headers=self.write_headers()
        )
        if not response.ok:
            raise SystemExit(f"Falha ao remover {resource}: {response.text}")


def ensure_database(api: SupersetApi) -> int:
    uri = cube_sqlalchemy_uri()
    for database in api.list("database"):
        if database["database_name"] == DATABASE_NAME:
            print(f"database: usando a existente ({uri})")
            return database["id"]
    database_id = api.create(
        "database",
        {
            "database_name": DATABASE_NAME,
            "sqlalchemy_uri": uri,
            "expose_in_sqllab": True,
            "allow_file_upload": False,
        },
    )
    print(f"database: criada id={database_id} ({uri})")
    return database_id


def ensure_dataset(api: SupersetApi, database_id: int) -> int:
    for dataset in api.list("dataset"):
        if (
            dataset["table_name"] == DATASET_TABLE
            and dataset["database"]["id"] == database_id
        ):
            dataset_id = dataset["id"]
            print(f"dataset: usando o existente id={dataset_id}")
            break
    else:
        dataset_id = api.create(
            "dataset",
            {
                "database": database_id,
                "schema": DATASET_SCHEMA,
                "table_name": DATASET_TABLE,
            },
        )
        print(f"dataset: criado id={dataset_id}")
        trim_internal_columns(api, dataset_id)
    metrics = with_existing_metric_ids(api, dataset_id)
    api.update("dataset", dataset_id, {"metrics": metrics})
    return dataset_id


def with_existing_metric_ids(api: SupersetApi, dataset_id: int) -> list[dict]:
    """A API recusa criar uma métrica com nome já usado; mandar o `id` faz o
    PUT atualizar a métrica em vez de tentar criá-la de novo."""
    existing = {
        metric["metric_name"]: metric["id"]
        for metric in api.get("dataset", dataset_id)["metrics"]
    }
    return [
        {**metric, "id": existing[metric["metric_name"]]}
        if metric["metric_name"] in existing
        else metric
        for metric in METRICS
    ]


def trim_internal_columns(api: SupersetApi, dataset_id: int) -> None:
    """Remove as colunas internas que o Cube anexa a toda tabela da SQL API
    (`__user`, `__cubeJoinField`): não são dimensões governadas."""
    dataset = api.get("dataset", dataset_id)
    for column in dataset["columns"]:
        if column["column_name"].startswith("__"):
            api.delete(f"dataset/{dataset_id}/column/{column['id']}")
            print(f"dataset: coluna interna removida ({column['column_name']})")


def chart_payload(spec: ChartSpec, dataset_id: int, dashboard_id: int) -> dict:
    return {
        "slice_name": spec.name,
        "description": spec.description,
        "viz_type": spec.viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps({**spec.form_data, "datasource": f"{dataset_id}__table"}),
        # É este campo que popula o vínculo dashboard↔gráfico (`dashboard_slices`).
        "dashboards": [dashboard_id],
    }


def ensure_charts(api: SupersetApi, dataset_id: int, dashboard_id: int) -> list[int]:
    existing = {chart["slice_name"]: chart["id"] for chart in api.list("chart")}
    chart_ids: list[int] = []
    for spec in CHARTS:
        payload = chart_payload(spec, dataset_id, dashboard_id)
        if spec.name in existing:
            chart_id = existing[spec.name]
            api.update("chart", chart_id, payload)
            print(f"chart: atualizado id={chart_id} ({spec.name})")
        else:
            chart_id = api.create("chart", payload)
            print(f"chart: criado id={chart_id} ({spec.name})")
        chart_ids.append(chart_id)
    desired_names = {spec.name for spec in CHARTS}
    for chart in api.list("chart"):
        if chart["slice_name"] not in desired_names and any(
            d.get("id") == dashboard_id for d in chart.get("dashboards", [])
        ):
            remaining = [
                d["id"] for d in chart.get("dashboards", []) if d.get("id") != dashboard_id
            ]
            api.update("chart", chart["id"], {"dashboards": remaining})
            print(f"chart: desvinculado do dashboard id={chart['id']} ({chart['slice_name']})")
    return chart_ids


def dashboard_position(chart_ids: list[int], title: str) -> str:
    """Layout do dashboard no formato do `position_json` do Superset (2 colunas)."""
    pairs = [chart_ids[i : i + 2] for i in range(0, len(chart_ids), 2)]
    row_ids = [f"ROW-{idx}" for idx in range(len(pairs))]
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
        "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": title}},
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "children": row_ids,
            "parents": ["ROOT_ID"],
        },
    }
    for idx, pair in enumerate(pairs):
        row_id = f"ROW-{idx}"
        col_width = 12 // len(pair)
        position[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": [f"CHART-{cid}" for cid in pair],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        for cid in pair:
            position[f"CHART-{cid}"] = {
                "id": f"CHART-{cid}",
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {"chartId": cid, "height": 50, "width": col_width},
            }
    return json.dumps(position)


def ensure_dashboard(api: SupersetApi) -> int:
    for dashboard in api.list("dashboard"):
        if dashboard["dashboard_title"] == DASHBOARD_TITLE:
            print(f"dashboard: usando o existente id={dashboard['id']}")
            return dashboard["id"]
    dashboard_id = api.create(
        "dashboard", {"dashboard_title": DASHBOARD_TITLE, "published": True}
    )
    print(f"dashboard: criado id={dashboard_id}")
    return dashboard_id


def layout_dashboard(api: SupersetApi, dashboard_id: int, chart_ids: list[int]) -> None:
    """Grava o layout. Sem `json_metadata` no payload: mandar metadata dispara o
    `set_dash_metadata`, que reescreve chaves de estilo que não temos opinião."""
    api.update(
        "dashboard",
        dashboard_id,
        {"position_json": dashboard_position(chart_ids, DASHBOARD_TITLE)},
    )
    print(f"dashboard: layout atualizado (id={dashboard_id})")


def main() -> None:
    api = SupersetApi(SUPERSET_URL, SUPERSET_ADMIN_USER, SUPERSET_ADMIN_PASSWORD)
    api.wait_until_ready()
    api.login()
    database_id = ensure_database(api)
    dataset_id = ensure_dataset(api, database_id)
    dashboard_id = ensure_dashboard(api)
    chart_ids = ensure_charts(api, dataset_id, dashboard_id)
    layout_dashboard(api, dashboard_id, chart_ids)
    print(
        f"pronto: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/ "
        f"(login: {SUPERSET_ADMIN_USER})"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyError as error:
        raise SystemExit(f"variável de ambiente ausente: {error}") from error
    sys.exit(0)
