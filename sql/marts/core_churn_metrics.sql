-- File: sql/marts/core_churn_metrics.sql
-- Description: Core business logic for Voluntary vs Involuntary Churn
-- Materialization: View

CREATE OR REPLACE VIEW core_churn_metrics AS

WITH monthly_subscriptions AS (
    -- 1. Create a "Scaffold" of months for each subscription to track status over time
    SELECT 
        s.subscription_id,
        s.customer_id,
        s.plan_id,
        DATE_TRUNC('month', i.invoice_date)::DATE AS month_date,
        s.start_date,
        s.end_date,
        s.status AS current_status,
        s.cancellation_reason,
        i.amount,
        p.payment_status
    FROM subscriptions s
    JOIN invoices i ON s.subscription_id = i.subscription_id
    LEFT JOIN payments p ON i.invoice_id = p.invoice_id
),

churn_status AS (
    -- 2. Define CHURN TYPE based on data signals
    SELECT 
        *,
        CASE 
            -- Logic: If payment failed, it's Involuntary Churn
            WHEN payment_status = 'Failed' THEN 'Involuntary'
            -- Logic: If cancelled and payment was OK, it's Voluntary
            WHEN current_status = 'Cancelled' AND end_date <= month_date + INTERVAL '1 month' THEN 'Voluntary'
            ELSE 'Active'
        END AS churn_type
    FROM monthly_subscriptions
)

-- 3. Calculate Aggregated Metrics
SELECT 
    month_date,
    COUNT(DISTINCT customer_id) AS total_customers,
    SUM(CASE WHEN churn_type = 'Voluntary' THEN 1 ELSE 0 END) AS voluntary_churn_count,
    SUM(CASE WHEN churn_type = 'Involuntary' THEN 1 ELSE 0 END) AS involuntary_churn_count,
    
    -- Churn Rate Formulas
    ROUND(
        (SUM(CASE WHEN churn_type IN ('Voluntary', 'Involuntary') THEN 1 ELSE 0 END)::DECIMAL / NULLIF(COUNT(DISTINCT customer_id), 0)) * 100, 
    2) AS churn_rate_pct,
    
    -- Revenue Impact (Revenue Churn)
    SUM(CASE WHEN churn_type IN ('Voluntary', 'Involuntary') THEN amount ELSE 0 END) AS lost_revenue
    
FROM churn_status
WHERE month_date < DATE_TRUNC('month', CURRENT_DATE) -- Exclude current incomplete month
GROUP BY month_date;