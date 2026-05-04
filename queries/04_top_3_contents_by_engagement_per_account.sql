WITH ranked AS (
    SELECT
        account_id,
        platform,
        content_id,
        post_date,
        format,
        engagement_rate,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY engagement_rate DESC
        ) AS rn
    FROM mart_content_performance
    WHERE engagement_rate IS NOT NULL
)
SELECT
    account_id,
    platform,
    content_id,
    post_date,
    format,
    engagement_rate
FROM ranked
WHERE rn <= 3
ORDER BY account_id, rn;
