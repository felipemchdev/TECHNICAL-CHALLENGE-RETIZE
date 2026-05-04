{{ config(alias='silver_instagram_content') }}

SELECT
    m.id::text AS content_id,
    LOWER(m.username) AS account_id,
    'instagram' AS platform,
    m.timestamp::timestamp AS post_date,

    LOWER(m.media_type) AS format,

    COALESCE(i.likes, m.like_count) AS likes,
    COALESCE(i.comments, m.comments_count) AS comments_count,

    i.reach,
    i.views

FROM raw_instagram_media m
LEFT JOIN raw_instagram_media_insights i
    ON m.id = i.id
