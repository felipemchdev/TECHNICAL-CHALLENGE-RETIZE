SELECT platform, content_id, COUNT(*) AS n
FROM {{ ref('performance') }}
GROUP BY platform, content_id
HAVING COUNT(*) > 1
