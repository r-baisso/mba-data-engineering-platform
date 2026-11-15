-- Fato de títulos: grão de exatamente um título (title_key).
--
-- Medidas: nota da crítica (`rating`), total de votos (`votes`) e duração em
-- minutos para filmes (`duration_minutes`; TV Show não tem duração, tem temporadas).
--
-- Regra de deduplicação: vem de `int_titles_attributes`, que mantém um único registro
-- representativo por título (menor `show_id` no Netflix) — a mesma regra das tabelas de
-- ponte de gênero e país, para que o grão seja "um título" e a contagem não infle ao
-- fatiar por qualquer dimensão. Na origem da crítica o desempate é a menor `release_date`.

with critic as (

    select
        lower(trim(title)) as title_key,
        rating,
        no_of_persons_voted,
        row_number() over (
            partition by lower(trim(title)) order by release_date
        ) as rn
    from {{ ref('meta_critic') }}

),

imdb as (

    select
        lower(trim(title)) as title_key,
        imdb_rating,
        imdb_votes,
        row_number() over (
            partition by lower(trim(title))
            order by imdb_votes desc, released_year desc
        ) as rn
    from {{ ref('imdb_top_1000') }}

)

select
    n.title_key,
    n.title,
    n.release_year as year_key,
    n.type as type_key,
    c.rating,
    c.no_of_persons_voted as votes,
    try_cast(
        nullif(regexp_extract(n.duration, '(\d+)\s*min', 1), '') as integer
    ) as duration_minutes,
    i.imdb_rating,
    i.imdb_votes,
    case when i.title_key is not null then 1 else 0 end as is_imdb_top_1000
from {{ ref('int_titles_attributes') }} n
inner join critic c on n.title_key = c.title_key and c.rn = 1
left join imdb i on n.title_key = i.title_key and i.rn = 1
