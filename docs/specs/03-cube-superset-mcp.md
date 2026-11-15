# Spec 03 — Camada Semântica (Cube) + Consumo Governado (Superset & MCP)

## 1. Objetivo
Expor na camada semântica (`Cube`) as novas métricas derivadas do IMDB Top 1000 em `refined.ml.fct_titles` e servi-las simultaneamente no **Apache Superset** e no **servidor MCP**, respondendo à pergunta de negócio com **paridade numérica exata**:
> *"Quais gêneros da Netflix têm mais títulos no Top 1000 do IMDB, e como a nota do público (IMDB) se compara à nota da crítica (Metacritic)?"*

## 2. Escopo da Mudança (Arquivos)
- `toy-data-platform-main/cube/model/cubes/titles.yml`
  - Adicionar medidas `count_imdb_top_1000` (`type: sum`, `sql: is_imdb_top_1000`) e `avg_imdb_rating` (`type: avg`, `sql: imdb_rating`).
  - *(Como `titles.title_key` já é `primary_key: true` e o join com `title_genre` é `one_to_many`, o Cube deduplica por `title_key` antes de somar/tirar média, evitando *fan trap*.)*
- `toy-data-platform-main/cube/model/views/titles_overview.yml`
  - Expor `count_imdb_top_1000` e `avg_imdb_rating` na fachada `titles_overview`.
- `toy-data-platform-main/superset/bootstrap_semantic_layer.py`
  - Registrar as novas medidas no array `METRICS` usando `MEASURE(count_imdb_top_1000)` e `MEASURE(avg_imdb_rating)`.
  - Adicionar um novo gráfico em `CHARTS` ("IMDB Top 1000 vs. Nota da Crítica por Gênero") no dashboard *Camada semântica — títulos*.
- `toy-data-platform-main/mcp/demo.py`
  - Adicionar a pergunta de negócio ao roteiro `QUESTIONS` usando as novas medidas governadas descobertas via `list_measures()`.

## 3. Critérios de Aceite (Validação da Parte 3)
1. **Cube REST & SQL API:** `titles_overview.count_imdb_top_1000` e `titles_overview.avg_imdb_rating` retornam valores válidos (`134` e `~7.967` no total global) e fatiados por `genre` sem *fan trap*.
2. **Superset:** `superset-bootstrap` conclui com código `0`, registrando as novas métricas e o novo gráfico no dashboard.
3. **MCP:** `unittest` (`mcp/tests`) continua passando 100% e `mcp/demo.py` responde à pergunta de negócio com **paridade numérica exata** frente ao Cube e ao Superset.
