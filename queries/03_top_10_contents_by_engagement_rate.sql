SELECT
    account_id,
    platform,
    content_id,
    post_date,
    format,
    engagement_rate
FROM mart_content_performance
WHERE engagement_rate IS NOT NULL
ORDER BY engagement_rate DESC
LIMIT 10;
