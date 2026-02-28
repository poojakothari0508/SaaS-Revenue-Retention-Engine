-- File: sql/marts/core_mrr_movements.sql
-- Description: Calculates New, Expansion, Contraction, and Churned MRR
-- Materialization: View

CREATE OR REPLACE VIEW core_mrr_movements AS

WITH monthly_revenue AS (
    -- 1. Aggregate revenue per customer per month
    SELECT 
        DATE_TRUNC('month', i.invoice_date)::DATE AS month_date,
        s.customer_id,
        SUM(i.amount) AS current_mrr
    FROM invoices i
    JOIN subscriptions s ON i.subscription_id = s.subscription_id
    WHERE i.invoice_date <= CURRENT_DATE
    GROUP BY 1, 2
),

mrr_lagged AS (
    -- 2. Use Window Functions to see Previous Month's MRR
    SELECT 
        month_date,
        customer_id,
        current_mrr,
        LAG(current_mrr) OVER (PARTITION BY customer_id ORDER BY month_date) AS previous_mrr
    FROM monthly_revenue
),

mrr_movements AS (
    -- 3. Classify the Movement Type
    SELECT 
        month_date,
        customer_id,
        current_mrr,
        previous_mrr,
        CASE 
            WHEN previous_mrr IS NULL THEN 'New'
            WHEN current_mrr > previous_mrr THEN 'Expansion'
            WHEN current_mrr < previous_mrr THEN 'Contraction'
            ELSE 'No Change'
        END AS movement_type,
        
        -- Calculate the $ impact
        COALESCE(current_mrr, 0) - COALESCE(previous_mrr, 0) AS mrr_change
    FROM mrr_lagged
    
    UNION ALL
    
    -- 4. Handle CHURN (Users who exist in prev month but NOT in current)
    SELECT 
        DATE_TRUNC('month', end_date + INTERVAL '1 month')::DATE AS month_date,
        customer_id,
        0 AS current_mrr,
        amount AS previous_mrr,
        'Churn' AS movement_type,
        -amount AS mrr_change
    FROM subscriptions s
    JOIN invoices i ON s.subscription_id = i.subscription_id
    WHERE status = 'Cancelled' 
    AND end_date IS NOT NULL
)

-- 5. Final Report: MRR Bridge
SELECT 
    month_date,
    SUM(CASE WHEN movement_type = 'New' THEN mrr_change ELSE 0 END) AS new_mrr,
    SUM(CASE WHEN movement_type = 'Expansion' THEN mrr_change ELSE 0 END) AS expansion_mrr,
    SUM(CASE WHEN movement_type = 'Contraction' THEN mrr_change ELSE 0 END) AS contraction_mrr,
    SUM(CASE WHEN movement_type = 'Churn' THEN mrr_change ELSE 0 END) AS churned_mrr,
    
    -- Net New MRR = (New + Expansion) - (Churn + Contraction)
    SUM(mrr_change) AS net_new_mrr,
    
    -- Total MRR at end of month (Cumulative Sum)
    SUM(SUM(mrr_change)) OVER (ORDER BY month_date) AS total_mrr
    
FROM mrr_movements
WHERE month_date IS NOT NULL
GROUP BY month_date;