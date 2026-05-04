{{ config(alias='silver_tiktok_content') }}

SELECT
    item_id::text AS content_id,
    LOWER(business_username) AS account_id,
    'tiktok' AS platform,
    to_timestamp(create_time) AS post_date,
    'video' AS format,
    likes,
    comments AS comments_count,
    reach,
    video_views AS views
FROM raw_tiktok_posts
WHERE item_id IS NOT NULL
