SELECT m.content_id
FROM {{ ref('instagram') }} m
LEFT JOIN {{ source('public', 'raw_instagram_media_insights') }} i
    ON m.content_id = i.id::text
WHERE i.id IS NULL
