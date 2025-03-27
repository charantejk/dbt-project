WITH source_data AS (
    SELECT
        campaign_id,
        campaign_name,
        channel,
        start_date,
        end_date,
        budget,
        target_segment
    FROM {{ source('marketing', 'raw_campaigns') }}
)

SELECT
    campaign_id,
    campaign_name,
    channel,
    start_date,
    end_date,
    budget,
    target_segment
FROM source_data