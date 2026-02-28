-- core_cohort_retention.sql
-- Goal: Calculate monthly retention rates by user signup cohort.
-- Note: Wrapping this in a CREATE OR REPLACE VIEW so it can be queried by BI/Python.

CREATE OR REPLACE VIEW core_cohort_retention AS

WITH cohort_definition AS (
    -- 1. Find the first start_date for each customer (The Cohort)
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(start_date))::DATE AS cohort_month
    FROM subscriptions
    GROUP BY customer_id
),

active_months AS (
    -- 2. Find every month a customer was active based on their invoices
    SELECT DISTINCT
        s.customer_id,
        DATE_TRUNC('month', i.invoice_date)::DATE AS active_month
    FROM subscriptions s
    JOIN invoices i ON s.subscription_id = i.subscription_id
),

cohort_activity AS (
    -- 3. Calculate the "Month Index" (e.g., Month 0, Month 1, Month 2)
    SELECT 
        c.customer_id,
        c.cohort_month,
        a.active_month,
        -- Extract the number of months between cohort month and active month
        (EXTRACT(YEAR FROM a.active_month) - EXTRACT(YEAR FROM c.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM a.active_month) - EXTRACT(MONTH FROM c.cohort_month)) AS month_index
    FROM cohort_definition c
    JOIN active_months a ON c.customer_id = a.customer_id
),

cohort_sizes AS (
    -- 4. Calculate total users in each original cohort (Month 0)
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS initial_customers
    FROM cohort_definition
    GROUP BY cohort_month
),

retention_matrix AS (
    -- 5. Count active users per cohort per month index
    SELECT 
        ca.cohort_month,
        cs.initial_customers,
        ca.month_index,
        COUNT(DISTINCT ca.customer_id) AS active_customers
    FROM cohort_activity ca
    JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
    GROUP BY ca.cohort_month, cs.initial_customers, ca.month_index
)

-- 6. Final output with Retention Percentage
SELECT 
    cohort_month,
    initial_customers,
    month_index,
    active_customers,
    ROUND((active_customers::DECIMAL / initial_customers) * 100, 2) AS retention_rate_pct
FROM retention_matrix
ORDER BY cohort_month, month_index;