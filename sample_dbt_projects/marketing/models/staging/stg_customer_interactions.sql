WITH source_data AS (
    SELECT
        interaction_id,
        customer_id,
        campaign_id,
        interaction_date,
        channel,
        interaction_type,
        conversion_flag
    FROM {{ source('marketing', 'raw_customer_interactions') }}
)

SELECT
    interaction_id,
    customer_id,
    campaign_id,
    interaction_date,
    channel,
    interaction_type,
    conversion_flag
FROM source_data