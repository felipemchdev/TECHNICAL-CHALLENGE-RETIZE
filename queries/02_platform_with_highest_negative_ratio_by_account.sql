WITH perf_accounts AS (
    SELECT DISTINCT
        account_id,
        platform,
        content_id
    FROM mart_content_performance
),
joined AS (
    SELECT
        p.account_id,
        s.platform,
        s.negative_comments,
        s.total_comments
    FROM mart_content_sentiment s
    JOIN perf_accounts p
      ON p.content_id = s.content_id
     AND p.platform = s.platform
),
agg AS (
    SELECT
        account_id,
        platform,
        SUM(negative_comments)::float / NULLIF(SUM(total_comments), 0) AS negative_ratio
    FROM joined
    GROUP BY account_id, platform
),
ranked AS (
    SELECT
        account_id,
        platform,
        negative_ratio,
        RANK() OVER (
            PARTITION BY account_id
            ORDER BY negative_ratio DESC
        ) AS rn
    FROM agg
)
SELECT
    account_id,
    platform AS worst_platform_by_negative_ratio,
    negative_ratio
FROM ranked
WHERE rn = 1
ORDER BY account_id;
