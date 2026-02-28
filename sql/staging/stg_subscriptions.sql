-- File: sql/staging/stg_subscriptions.sql
-- Description: Cleans up the raw subscriptions table for downstream use.

CREATE OR REPLACE VIEW stg_subscriptions AS
SELECT 
    subscription_id,
    customer_id,
    plan_id,
    start_date,
    -- Data cleanup: If end_date is null, treat it as active far into the future 
    -- (Helps prevent NULL handling bugs in complex queries)
    COALESCE(end_date, '2099-12-31'::DATE) AS end_date,
    status,
    LOWER(cancellation_reason) AS cancellation_reason,
    -- Add an easy boolean flag for active/churned
    CASE WHEN status = 'Active' THEN TRUE ELSE FALSE END AS is_active
FROM subscriptions;