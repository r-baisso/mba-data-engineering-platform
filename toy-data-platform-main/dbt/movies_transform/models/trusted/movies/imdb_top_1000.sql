WITH source AS (
    SELECT
        TRIM(series_title) AS title,
        CAST(
            CASE
                WHEN regexp_like(TRIM(released_year), '^\d{4}$')
                    THEN TRIM(released_year)
            END AS integer
        ) AS released_year,
        TRIM(certificate) AS certificate,
        TRIM(runtime) AS runtime,
        TRIM(genre) AS genre,
        CAST(imdb_rating AS double) AS imdb_rating,
        CAST(meta_score AS double) AS meta_score,
        TRIM(director) AS director,
        CAST(no_of_votes AS bigint) AS imdb_votes,
        CAST(NULLIF(REPLACE(TRIM(gross), ',', ''), '') AS bigint) AS gross_usd
    FROM {{ source('raw', 'imdb_top_1000') }}
)

SELECT * FROM source
