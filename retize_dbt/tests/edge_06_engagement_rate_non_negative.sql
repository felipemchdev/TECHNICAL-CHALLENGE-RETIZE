SELECT content_id, platform, engagement_rate
FROM {{ ref('performance') }}
WHERE engagement_rate < 0
