-- File: sql/marts/fct_usage_signals.sql
-- Description: Aggregates usage events and support tickets to define customer engagement and churn risk.
-- Materialization: View

CREATE OR REPLACE VIEW fct_usage_signals AS

WITH monthly_usage AS (
    -- 1. Aggregate usage events per customer per month
    SELECT 
        customer_id,
        DATE_TRUNC('month', event_date)::DATE AS month_date,
        COUNT(event_id) AS total_login_events,
        SUM(usage_count) AS total_feature_actions
    FROM usage_events
    GROUP BY 1, 2
),

monthly_tickets AS (
    -- 2. Aggregate support tickets per customer per month
    SELECT 
        customer_id,
        DATE_TRUNC('month', ticket_date)::DATE AS month_date,
        COUNT(ticket_id) AS ticket_count
    FROM support_tickets
    GROUP BY 1, 2
),

customer_churn_status AS (
    -- 3. Get the churn status and date for each customer
    SELECT 
        customer_id,
        status,
        DATE_TRUNC('month', end_date)::DATE AS churn_month
    FROM subscriptions
)

-- 4. Combine everything into a unified Feature Table
SELECT 
    u.customer_id,
    u.month_date,
    COALESCE(u.total_login_events, 0) AS total_login_events,
    COALESCE(u.total_feature_actions, 0) AS total_feature_actions,
    COALESCE(t.ticket_count, 0) AS support_tickets,
    
    -- Engagement Segmentation
    CASE 
        WHEN COALESCE(u.total_feature_actions, 0) < 10 THEN 'Low Risk (Low Usage)'
        WHEN COALESCE(u.total_feature_actions, 0) BETWEEN 10 AND 50 THEN 'Medium (Healthy)'
        ELSE 'High (Power User)'
    END AS usage_segment,

    -- Target Variable for ML: Did they churn in this specific month?
    CASE 
        WHEN c.status = 'Cancelled' AND c.churn_month = u.month_date THEN 1 
        ELSE 0 
    END AS is_churned_this_month

FROM monthly_usage u
LEFT JOIN monthly_tickets t 
    ON u.customer_id = t.customer_id 
    AND u.month_date = t.month_date
JOIN customer_churn_status c 
    ON u.customer_id = c.customer_id;