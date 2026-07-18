USE ecommerce_analytics;
SELECT
    DATE_FORMAT(orders.order_date, '%Y-%m')            AS order_month,
    COUNT(DISTINCT orders.order_id)                    AS total_orders,
    SUM(orders.quantity * orders.unit_price_at_order)  AS total_revenue
FROM
    orders
GROUP BY
    DATE_FORMAT(orders.order_date, '%Y-%m')
ORDER BY
    order_month ASC;
    WITH customer_order_summary AS (
    SELECT
        customers.customer_id                                    AS customer_id,
        CONCAT(customers.first_name, ' ', customers.last_name)    AS customer_name,
        MAX(orders.order_date)                                    AS last_order_date,
        COUNT(DISTINCT orders.order_id)                           AS order_frequency,
        SUM(orders.quantity * orders.unit_price_at_order)         AS total_monetary_value
    FROM
        customers
    INNER JOIN
        orders ON customers.customer_id = orders.customer_id
    GROUP BY
        customers.customer_id,
        CONCAT(customers.first_name, ' ', customers.last_name)
),
customer_rfm_metrics AS (
    SELECT
        customer_order_summary.customer_id                                      AS customer_id,
        customer_order_summary.customer_name                                     AS customer_name,
        customer_order_summary.last_order_date                                   AS last_order_date,
        DATEDIFF(CURDATE(), customer_order_summary.last_order_date)              AS recency_days,
        customer_order_summary.order_frequency                                    AS order_frequency,
        customer_order_summary.total_monetary_value                               AS total_monetary_value
    FROM
        customer_order_summary
)
SELECT
    customer_rfm_metrics.customer_id            AS customer_id,
    customer_rfm_metrics.customer_name            AS customer_name,
    customer_rfm_metrics.recency_days             AS recency_days,
    customer_rfm_metrics.order_frequency           AS order_frequency,
    customer_rfm_metrics.total_monetary_value       AS total_monetary_value,
    CASE
        WHEN customer_rfm_metrics.order_frequency >= 5
             AND customer_rfm_metrics.total_monetary_value >= 300 THEN 'VIP'
        WHEN customer_rfm_metrics.order_frequency >= 3
             AND customer_rfm_metrics.recency_days <= 60 THEN 'Loyal'
        WHEN customer_rfm_metrics.recency_days > 120 THEN 'Churned'
        WHEN customer_rfm_metrics.recency_days > 60 THEN 'At Risk'
        ELSE 'New / Low Engagement'
    END AS customer_segment
FROM
    customer_rfm_metrics
ORDER BY
    total_monetary_value DESC;