SELECT s.content_id, s.platform
FROM {{ ref('sentiment') }} s
LEFT JOIN {{ ref('performance') }} p
    ON s.content_id = p.content_id
   AND s.platform = p.platform
WHERE p.content_id IS NULL
