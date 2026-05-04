{{ config(alias='mart_content_performance') }}

WITH unioned AS (
    SELECT * FROM {{ ref('instagram') }}
    UNION ALL
    SELECT * FROM {{ ref('titkok') }}
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY platform, content_id
            ORDER BY post_date DESC NULLS LAST
        ) AS rn
    FROM unioned
)

SELECT
    account_id,
    platform,
    content_id,
    post_date,
    CASE EXTRACT(DOW FROM post_date)
        WHEN 0 THEN 'sunday'
        WHEN 1 THEN 'monday'
        WHEN 2 THEN 'tuesday'
        WHEN 3 THEN 'wednesday'
        WHEN 4 THEN 'thursday'
        WHEN 5 THEN 'friday'
        WHEN 6 THEN 'saturday'
    END AS day_of_week,
    LOWER(format) AS format,

    likes,
    comments_count,

    reach,
    views,
    GREATEST(COALESCE(reach, 0), COALESCE(views, 0)) AS views_or_reach,

    (COALESCE(likes, 0) + COALESCE(comments_count, 0))::float
    / NULLIF(GREATEST(COALESCE(reach, 0), COALESCE(views, 0)), 0) AS engagement_rate

FROM ranked
WHERE rn = 1
