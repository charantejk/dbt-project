WITH customers AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        segment
    FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        status,
        amount
    FROM {{ ref('stg_orders') }}
),

customer_orders AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.segment,
        COUNT(o.order_id) AS order_count,
        SUM(o.amount) AS total_spend,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS most_recent_order_date
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY 1, 2, 3, 4, 5
)

SELECT * FROM customer_orders