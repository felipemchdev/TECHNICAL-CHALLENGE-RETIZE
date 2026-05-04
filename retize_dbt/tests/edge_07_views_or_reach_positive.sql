SELECT content_id, platform, views_or_reach
FROM {{ ref('perfomance') }}
WHERE views_or_reach < 0
