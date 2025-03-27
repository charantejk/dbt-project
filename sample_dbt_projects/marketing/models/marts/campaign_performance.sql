-- This model links with data from ecommerce and finance projects

WITH campaigns AS (
    SELECT
        campaign_id,
        campaign_name,
        channel,
        start_date,
        end_date,
        budget,
        target_segment
    FROM {{ ref('stg_campaigns') }}
),

interactions AS (
    SELECT
        interaction_id,
        customer_id,
        campaign_id,
        interaction_date,
        channel,
        interaction_type,
        conversion_flag
    FROM {{ ref('stg_customer_interactions') }}
),

-- Cross-project reference to ecommerce
customer_data AS (
    SELECT
        customer_id,
        segment,
        order_count,
        total_spend
    FROM {{ ref('customer_orders', 'ecommerce') }}
),

-- Cross-project reference to finance
revenue_data AS (
    SELECT
        customer_id,
        SUM(revenue) as total_revenue
    FROM {{ ref('order_revenue', 'finance') }}
    GROUP BY 1
),

campaign_performance AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.channel,
        c.start_date,
        c.end_date,
        c.budget,
        c.target_segment,
        COUNT(DISTINCT i.customer_id) AS reached_customers,
        COUNT(DISTINCT CASE WHEN i.conversion_flag = true THEN i.customer_id END) AS converted_customers,
        SUM(CASE WHEN i.conversion_flag = true THEN cd.order_count ELSE 0 END) AS attributed_orders,
        SUM(CASE WHEN i.conversion_flag = true THEN rd.total_revenue ELSE 0 END) AS attributed_revenue,
        CASE 
            WHEN c.budget > 0 THEN SUM(CASE WHEN i.conversion_flag = true THEN rd.total_revenue ELSE 0 END) / c.budget 
            ELSE 0 
        END AS roi
    FROM campaigns c
    LEFT JOIN interactions i ON c.campaign_id = i.campaign_id
    LEFT JOIN customer_data cd ON i.customer_id = cd.customer_id
    LEFT JOIN revenue_data rd ON i.customer_id = rd.customer_id
    GROUP BY 1, 2, 3, 4, 5, 6, 7
)

SELECT * FROM campaign_performance