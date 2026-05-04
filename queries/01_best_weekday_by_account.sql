WITH base AS (
    SELECT
        account_id,
        day_of_week,
        engagement_rate
    FROM mart_content_performance
    WHERE engagement_rate IS NOT NULL
),
avg_by_day AS (
    SELECT
        account_id,
        day_of_week,
        AVG(engagement_rate) AS avg_engagement_rate
    FROM base
    GROUP BY account_id, day_of_week
),
ranked AS (
    SELECT
        account_id,
        day_of_week,
        avg_engagement_rate,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY avg_engagement_rate DESC
        ) AS rn
    FROM avg_by_day
)
SELECT
    account_id,
    day_of_week AS best_day_of_week,
    avg_engagement_rate
FROM ranked
WHERE rn = 1
ORDER BY account_id;
