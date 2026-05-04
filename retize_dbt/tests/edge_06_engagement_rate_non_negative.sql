SELECT content_id, platform, engagement_rate
FROM {{ ref('perfomance') }}
WHERE engagement_rate < 0
