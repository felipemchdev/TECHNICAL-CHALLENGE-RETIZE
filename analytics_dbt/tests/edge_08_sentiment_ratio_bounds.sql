SELECT content_id, platform, negative_ratio
FROM {{ ref('sentiment') }}
WHERE negative_ratio < 0
   OR negative_ratio > 1
