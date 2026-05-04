SELECT c.post_id
FROM {{ source('public', 'raw_tiktok_comments') }} c
LEFT JOIN {{ source('public', 'raw_tiktok_posts') }} p
    ON c.post_id = p.item_id
WHERE c.post_id IS NOT NULL
  AND p.item_id IS NULL
