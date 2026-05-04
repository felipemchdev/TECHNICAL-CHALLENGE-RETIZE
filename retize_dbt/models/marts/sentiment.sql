{{ config(alias='mart_content_sentiment') }}

WITH valid_content AS (
    SELECT DISTINCT content_id, platform
    FROM {{ ref('performance') }}
),
base_comments AS (
    SELECT c.content_id, c.platform, c.sentiment
    FROM {{ ref('platform') }} c
    INNER JOIN valid_content vc
        ON vc.content_id = c.content_id
       AND vc.platform = c.platform
)

SELECT
    content_id,
    platform,
    COUNT(*) AS total_comments,

    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END)
        AS negative_comments,

    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END)::float
        / NULLIF(COUNT(*), 0) AS negative_ratio

FROM base_comments
GROUP BY content_id, platform
