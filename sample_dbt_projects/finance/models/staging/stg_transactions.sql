WITH source_data AS (
    SELECT
        transaction_id,
        order_id,
        transaction_date,
        payment_method,
        amount,
        status
    FROM {{ source('finance', 'raw_transactions') }}
)

SELECT
    transaction_id,
    order_id,
    transaction_date,
    payment_method,
    amount,
    status
FROM source_data