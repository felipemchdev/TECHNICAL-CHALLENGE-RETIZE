WITH silver_count AS (
    SELECT COUNT(*) AS n FROM {{ ref('titkok') }}
),
gold_count AS (
    SELECT COUNT(*) AS n
    FROM {{ ref('perfomance') }}
    WHERE platform = 'tiktok'
)
SELECT 1
FROM silver_count s
CROSS JOIN gold_count g
WHERE g.n > s.n
