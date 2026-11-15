-- Garante que notas do IMDB presentes em fct_titles estejam dentro da escala [0, 10].
select
    title_key,
    imdb_rating
from {{ ref('fct_titles') }}
where imdb_rating is not null
  and (imdb_rating < 0 or imdb_rating > 10)
