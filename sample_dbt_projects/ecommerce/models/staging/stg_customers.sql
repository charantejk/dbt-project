WITH source_data AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        registration_date,
        segment
    FROM {{ source('ecommerce', 'raw_customers') }}
)

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    registration_date,
    segment
FROM source_data