WITH avg_format AS (
    SELECT
        account_id,
        format,
        AVG(engagement_rate) AS avg_engagement_rate
    FROM mart_content_performance
    WHERE engagement_rate IS NOT NULL
    GROUP BY account_id, format
),
ranked AS (
    SELECT
        account_id,
        format,
        avg_engagement_rate,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY avg_engagement_rate DESC
        ) AS rn
    FROM avg_format
)
SELECT
    account_id,
    format AS best_format,
    avg_engagement_rate
FROM ranked
WHERE rn = 1
ORDER BY account_id;
