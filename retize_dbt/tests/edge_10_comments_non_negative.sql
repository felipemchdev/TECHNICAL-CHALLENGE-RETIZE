SELECT content_id, platform, total_comments, negative_comments
FROM {{ ref('sentiment') }}
WHERE total_comments < 0
   OR negative_comments < 0
   OR negative_comments > total_comments
