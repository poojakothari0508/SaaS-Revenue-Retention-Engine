-- SaaS Revenue Retention Engine Schema
-- Database: PostgreSQL

-- 1. CUSTOMERS (The Core Entity)
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    signup_date DATE NOT NULL,
    acquisition_channel VARCHAR(50),
    country VARCHAR(50),
    industry VARCHAR(50)
);

-- 2. SUBSCRIPTION PLANS (Static Data)
CREATE TABLE IF NOT EXISTS subscription_plans (
    plan_id INTEGER PRIMARY KEY,
    plan_name VARCHAR(50),
    billing_cycle VARCHAR(20), -- Monthly, Annual
    price DECIMAL(10, 2),
    discount_flag BOOLEAN
);

-- 3. SUBSCRIPTIONS (The Engine of MRR)
-- One customer can have multiple subscriptions over time (upgrades, reactivations)
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id),
    plan_id INTEGER REFERENCES subscription_plans(plan_id),
    start_date DATE NOT NULL,
    end_date DATE, -- NULL means Active
    status VARCHAR(20), -- Active, Cancelled, Paused
    cancellation_reason VARCHAR(100)
);

-- 4. INVOICES (Financial Record)
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    subscription_id VARCHAR(50) REFERENCES subscriptions(subscription_id),
    invoice_date DATE NOT NULL,
    amount DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2)
);

-- 5. PAYMENTS (Cash Flow & Involuntary Churn Source)
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    invoice_id VARCHAR(50) REFERENCES invoices(invoice_id),
    payment_status VARCHAR(20), -- Paid, Failed, Refunded
    payment_date DATE
);

-- 6. USAGE EVENTS (Behavioral Data for Risk Modeling)
CREATE TABLE IF NOT EXISTS usage_events (
    event_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id),
    feature_name VARCHAR(50),
    event_date TIMESTAMP,
    usage_count INTEGER
);

-- 7. SUPPORT TICKETS (Churn Signal)
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id),
    ticket_date TIMESTAMP,
    issue_type VARCHAR(50), -- Billing, Technical, Feature Request
    resolution_time_hours DECIMAL(5, 2)
);

-- INDEXES (For Performance on Large Joins)
CREATE INDEX idx_subs_cust ON subscriptions(customer_id);
CREATE INDEX idx_inv_sub ON invoices(subscription_id);
CREATE INDEX idx_usage_cust ON usage_events(customer_id);