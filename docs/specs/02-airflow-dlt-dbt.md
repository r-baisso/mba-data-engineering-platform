# Spec 02 — Orquestração Paralela `dlt → dbt` no Apache Airflow

## 1. Objetivo
Evoluir a DAG `extract_movies` no Apache Airflow para aplicar os padrões da **Aula 02**:
1. Substituir o encadeamento sequencial `chain(*tasks)` pela **execução paralela** das 3 fontes independentes (`imdb_top_1000`, `meta_critic`, `netflix_titles`).
2. Encadear a tarefa `transform-dbt-build` (`DockerOperator` com a imagem `movies_transform:latest`) após a conclusão com sucesso de todas as ingestões (`ingestion_tasks >> transform_task`), criando uma barreira de segurança para que falhas parciais de ingestão não contaminem a camada analítica.

## 2. Escopo da Mudança (Arquivos)
- `toy-data-platform-main/dbt/Dockerfile`
  - Empacotar `COPY movies_transform /usr/app/movies_transform` e `WORKDIR /usr/app/movies_transform` na imagem `movies_transform:latest` (mantendo compatibilidade com o `Makefile`, mas permitindo que o `DockerOperator` rode sem depender de caminhos de *bind mount* do host Windows/WSL2).
- `toy-data-platform-main/airflow/dags/extract_movies.py`
  - Remover `chain(*tasks)`.
  - Executar os 3 `DockerOperator` de `dlt` em paralelo (`ingestion_tasks`).
  - Adicionar `dbt_build_task = DockerOperator(...)` executando `dbt build --no-partial-parse --target-path target/prod`.
  - Definir `ingestion_tasks >> dbt_build_task`.

## 3. Especificação Técnica

### 3.1 Imagem `movies_transform:latest`
- Adicionar ao `dbt/Dockerfile`:
  ```dockerfile
  WORKDIR /usr/app/movies_transform
  COPY movies_transform /usr/app/movies_transform
  ```
- Reconstruir a imagem com `docker build -t movies_transform:latest dbt/`.

### 3.2 DAG `extract_movies`
- **Schedule:** manter `@once` (ou `catchup=False`, para disparo manual/idempotente sob demanda no ambiente local).
- **Tarefas de ingestão (`ingestion_tasks`):**
  - `ingestion-movies-imdb_top_1000`
  - `ingestion-movies-meta_critic`
  - `ingestion-movies-netflix_titles`
  - Todas rodam em paralelo com `image="my-dlt-pipeline:latest"`, `network_mode="container:airflow_scheduler"`, `auto_remove="force"`.
- **Tarefa de transformação (`transform-dbt-build`):**
  - `image="movies_transform:latest"`
  - `command=["dbt", "build", "--no-partial-parse", "--target-path", "target/prod"]`
  - `environment={"DBT_PARTIAL_PARSE": "false"}` *(evita alocação excessiva de memória no WSL2)*
  - `network_mode="container:airflow_scheduler"`
  - `auto_remove="force"`
  - `retries=1`
- **Dependência:** `ingestion_tasks >> dbt_build_task`

## 4. Critérios de Aceite (Validação da Parte 2)
1. O Airflow reconhece a DAG `extract_movies` sem erros de importação (`airflow dags list` / API).
2. Disparar a DAG `extract_movies` via Airflow (`airflow dags trigger extract_movies`) e confirmar que:
   - As 3 tarefas de ingestão `dlt` executam em paralelo e concluem com estado `success`.
   - A tarefa `transform-dbt-build` executa somente após as 3 ingestões e conclui com estado `success`.
3. Verificar **idempotência**: reexecutar ou conferir `refined.ml.fct_titles` após a DAG e confirmar `1813` linhas = `1813` chaves distintas e `134` matches no IMDB Top 1000 (sem duplicatas).
