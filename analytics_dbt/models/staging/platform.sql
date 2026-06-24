{{ config(alias='silver_comments') }}

SELECT
    post_id::text AS content_id,
    'instagram' AS platform,
    CASE
        WHEN predicted_sentiment = 'positivo' THEN 'positive'
        WHEN predicted_sentiment = 'negativo' THEN 'negative'
        ELSE 'neutral'
    END AS sentiment
FROM raw_instagram_comments

UNION ALL

SELECT
    post_id::text AS content_id,
    'tiktok' AS platform,
    CASE
        WHEN predicted_sentiment = 'positivo' THEN 'positive'
        WHEN predicted_sentiment = 'negativo' THEN 'negative'
        ELSE 'neutral'
    END AS sentiment
FROM raw_tiktok_comments
