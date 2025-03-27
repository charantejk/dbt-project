WITH source_data AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        status,
        amount
    FROM {{ source('ecommerce', 'raw_orders') }}
)

SELECT
    order_id,
    customer_id,
    order_date,
    status,
    amount
FROM source_data