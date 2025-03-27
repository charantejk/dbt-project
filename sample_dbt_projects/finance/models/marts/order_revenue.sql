-- This model links with data from ecommerce project using order_id as the common key

WITH transactions AS (
    SELECT
        transaction_id,
        order_id,
        transaction_date,
        payment_method,
        amount,
        status
    FROM {{ ref('stg_transactions') }}
    WHERE status = 'completed'
),

-- Cross-project reference
ecommerce_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date
    FROM {{ ref('stg_orders', 'ecommerce') }}
),

order_revenue AS (
    SELECT
        t.order_id,
        eo.customer_id,
        eo.order_date,
        t.transaction_date,
        SUM(t.amount) AS revenue,
        COUNT(t.transaction_id) AS transaction_count,
        MAX(t.payment_method) AS payment_method
    FROM transactions t
    LEFT JOIN ecommerce_orders eo ON t.order_id = eo.order_id
    GROUP BY 1, 2, 3, 4
)

SELECT * FROM order_revenue