SELECT c.post_id
FROM {{ source('public', 'raw_instagram_comments') }} c
LEFT JOIN {{ source('public', 'raw_instagram_media') }} m
    ON c.post_id = m.id
WHERE c.post_id IS NOT NULL
  AND m.id IS NULL
