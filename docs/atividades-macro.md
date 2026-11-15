# Atividades Macro Planejadas — Atividade Final (Data Engineering & Architecture)

- **Disciplina:** Data Engineering & Architecture (MBA em Arquitetura de Sistemas Digitais — Faculdade Impacta)
- **Referência do enunciado:** [README.md](../README.md)
- **Prazo de entrega:** 18/11/2026 (relatório técnico em PDF ou DOCX no Classroom)
- **Skill de apoio:** [data-engineering-platform](../.agents/skills/data-engineering-platform/SKILL.md)

---

## Fase 1 — Setup do Ambiente
- [x] Extrair `data/toy-data-platform-main.zip` e inspecionar a estrutura do projeto (Makefile, `docker-compose`, `dlt/`, `airflow/`, `dbt/`, `cube/`, `superset/`, `mcp/`).
- [x] Subir a stack original e validar que tudo funciona antes de qualquer alteração (ingestão, DAG, `dbt build`, Cube, Superset e servidor MCP).
- [ ] *(Opcional)* Inicializar repositório Git para versionar as mudanças e facilitar a extração de diffs/trechos de código para o relatório.

## Fase 2 — Definição do Escopo e da Pergunta de Negócio
- [x] Definir **1 pergunta concreta sobre os dados** que a plataforma atual ainda não responde (ou que exija evoluir uma ou mais camadas).
  - **Pergunta definida:** *"Quais gêneros da Netflix têm mais títulos no Top 1000 do IMDB, e como a nota do público (IMDB) se compara à nota da crítica (Metacritic)?"*
- [x] Escolher **onde evoluir a plataforma** para responder à pergunta (em modelo SDD — Spec-Driven Development, em 3 partes):
  - **Parte 1 (`docs/specs/01-dbt-imdb-top-1000.md`):** Transformação/Modelagem & Qualidade (`dbt` — `trusted.movies.imdb_top_1000`, enriquecimento de `refined.ml.fct_titles`, testes de contrato e simulação de falha).
  - **Parte 2 (`docs/specs/02-airflow-dlt-dbt.md`):** Orquestração (`Airflow` — DAG `extract_movies` com ingestões `dlt` em paralelo encadeadas para `dbt build` via `DockerOperator`).
  - **Parte 3 (`docs/specs/03-cube-superset-mcp.md`):** Camada Semântica & Consumo (`Cube` com novas medidas `count_imdb_top_1000` e `avg_imdb_rating`, sincronização no `Superset` e validação de paridade no servidor `MCP`).

## Fase 3 — Implementação e Validação Técnica
- [x] Implementar as alterações seguindo os padrões da plataforma ([SKILL.md](../.agents/skills/data-engineering-platform/SKILL.md)) — Specs `01`, `02` e `03` concluídas.
- [x] Testar a **idempotência** (reexecutar o pipeline/DAG para a mesma entrada e confirmar ausência de duplicatas: `1813` linhas = `1813` chaves distintas, `134` matches IMDB).
- [x] Rodar `dbt build` e validar os testes — incluindo **simular um erro real** (`imdb_rating = 15.0` capturado por `assert_fct_titles_imdb_rating_range`) antes de restaurar o estado válido.
- [x] Validar que a mesma métrica retorna **exatamente o mesmo número** no Cube, no Superset e no agente via MCP (`Dramas: 89 títulos, IMDB 7.952 vs. crítica 6.773`).

## Fase 4 — Coleta de Evidências e Relatório Técnico (Entrega até 18/11)
- [x] Coletar prints e logs reais (DAG rodando, logs do Airflow/dlt/dbt, teste pegando erro, query no Cube, gráfico no Superset, resposta do agente MCP).
- [x] Redigir o relatório cobrindo os 6 tópicos exigidos no [README.md](../README.md) (`docs/relatorio-final.md`).
- [x] Exportar para **PDF** (`docs/relatorio-final.pdf`) e validar na avaliação adversarial (`professor-avaliador`: **APROVADO / CONCLUÍDO**).
- [ ] Enviar `docs/relatorio-final.pdf` no Classroom até **18/11**.
