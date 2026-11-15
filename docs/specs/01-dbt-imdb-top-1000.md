# Spec 01 — Transformação, Modelagem e Qualidade: IMDB Top 1000 no dbt

## 1. Objetivo e Pergunta de Negócio
Habilitar na camada analítica (`trusted` e `refined`) os dados do dataset `raw.raw_movies.imdb_top_1000` (já ingerido pelo `dlt`, porém não transformado) para responder:
> *"Quais gêneros da Netflix têm mais títulos no Top 1000 do IMDB, e como a nota do público (IMDB) se compara à nota da crítica (Metacritic)?"*

## 2. Escopo da Mudança (Arquivos)
- `toy-data-platform-main/dbt/movies_transform/models/trusted/movies/schema.yml`
  - Declarar `imdb_top_1000` em `sources` (`raw.raw_movies`).
  - Declarar o modelo `imdb_top_1000` e seus testes de coluna.
- `toy-data-platform-main/dbt/movies_transform/models/trusted/movies/imdb_top_1000.sql` *(novo)*
- `toy-data-platform-main/dbt/movies_transform/models/refined/ml/fct_titles.sql`
  - Enriquecer o fato existente mantendo exatamente o grão atual (`1 linha = 1 title_key`).
- `toy-data-platform-main/dbt/movies_transform/models/refined/ml/schema.yml`
  - Documentar e testar as novas colunas (`imdb_rating`, `imdb_votes`, `is_imdb_top_1000`).
- `toy-data-platform-main/dbt/movies_transform/tests/assert_fct_titles_grain.sql` *(novo, ou reforço dos testes singulares)*
  - Garantir que o `LEFT JOIN` com o IMDB nunca duplique `title_key` nem altere o grão de `fct_titles`.

## 3. Especificação Técnica

### 3.1 Camada `trusted` (`trusted.movies.imdb_top_1000`)
- **Grão:** 1 linha por linha da origem `raw.raw_movies.imdb_top_1000` (sem filtros ou agregações).
- **Padronizações:**
  - `TRIM(series_title) AS title`
  - `CAST(CASE WHEN regexp_like(TRIM(released_year), '^\d{4}$') THEN TRIM(released_year) END AS integer) AS released_year` *(evita `TRY_CAST` silencioso em formatos inesperados, tratando apenas o caso conhecido de ano não-numérico)*
  - `CAST(imdb_rating AS double) AS imdb_rating`
  - `CAST(no_of_votes AS bigint) AS imdb_votes`
  - `CAST(NULLIF(REPLACE(TRIM(gross), ',', ''), '') AS bigint) AS gross_usd`
  - `TRIM(certificate) AS certificate`, `TRIM(genre) AS genre`, `TRIM(director) AS director`

### 3.2 Camada `refined` (`refined.ml.fct_titles`)
- **Grão preservado:** `1 linha = 1 title_key` (`1813` linhas esperadas).
- **Deduplicação determinística no IMDB:** Como dois filmes podem ter o mesmo título em anos diferentes, desempate explícito por `row_number() over (partition by lower(trim(title)) order by imdb_votes desc, released_year desc) = 1`.
- **Join:** `LEFT JOIN imdb` por `n.title_key = i.title_key` (para não descartar títulos da Netflix+Metacritic que não estão no Top 1000 do IMDB).
- **Novas colunas em `fct_titles`:**
  - `i.imdb_rating` (`double`, `NULL` quando não está no Top 1000)
  - `i.imdb_votes` (`bigint`, `NULL` quando não está no Top 1000)
  - `CASE WHEN i.title_key IS NOT NULL THEN 1 ELSE 0 END AS is_imdb_top_1000` (permite `SUM` ou `COUNT` direto no Cube sem risco de contagem errada)

### 3.3 Contratos e Testes de Qualidade
- **Em `trusted.movies.imdb_top_1000`:**
  - `title`: `not_null`
  - `imdb_rating`: `not_null`
  - `imdb_votes`: `not_null`
- **Em `refined.ml.fct_titles`:**
  - `title_key`: `unique` e `not_null` (mantido)
  - `is_imdb_top_1000`: `not_null` + `accepted_values: [0, 1]`
- **Teste singular (`assert_fct_titles_imdb_rating_range.sql`):**
  - Falha (retorna linhas) se `imdb_rating < 0 OR imdb_rating > 10` (quando não nulo).
- **Teste singular (`assert_fct_titles_grain.sql`):**
  - Falha se `count(*) != count(distinct title_key)` em `fct_titles`.

## 4. Critérios de Aceite (Validação da Parte 1)
1. `dbt build --target-path target/prod` executa com `ERROR=0` e `WARN=0`.
2. `SELECT count(*), count(DISTINCT title_key), sum(is_imdb_top_1000) FROM refined.ml.fct_titles` retorna `count(*) = 1813`, `count(DISTINCT title_key) = 1813` e `sum(is_imdb_top_1000) > 0`.
3. **Evidência de teste pegando erro real:** Simular temporariamente um dado inválido (ex.: nota fora de `[0, 10]` ou duplicata) e comprovar que o teste do dbt falha antes de restaurar o estado válido.
