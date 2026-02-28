import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker()
np.random.seed(42)

# Configuration
NUM_CUSTOMERS = 2000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2023, 12, 31)
OUTPUT_DIR = "data/raw"

# Ensure directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🚀 Starting SaaS Data Generation...")

# --- 1. PLANS ---
plans_data = [
    {'plan_id': 1, 'plan_name': 'Basic', 'price': 29.00, 'billing_cycle': 'Monthly', 'discount_flag': False},
    {'plan_id': 2, 'plan_name': 'Pro', 'price': 99.00, 'billing_cycle': 'Monthly', 'discount_flag': False},
    {'plan_id': 3, 'plan_name': 'Enterprise', 'price': 299.00, 'billing_cycle': 'Monthly', 'discount_flag': False},
    {'plan_id': 4, 'plan_name': 'Pro Discount', 'price': 79.00, 'billing_cycle': 'Monthly', 'discount_flag': True},
]
df_plans = pd.DataFrame(plans_data)

# --- 2. CUSTOMERS ---
customers = []
industries = ['Tech', 'Healthcare', 'Finance', 'Retail', 'Education']
countries = ['USA', 'UK', 'Canada', 'Germany', 'Australia']
channels = ['Organic Search', 'LinkedIn Ads', 'Referral', 'Direct', 'Email']

for _ in range(NUM_CUSTOMERS):
    days_offset = np.random.beta(2, 5) * (END_DATE - START_DATE).days # Skew towards earlier dates for long history
    signup_date = START_DATE + timedelta(days=int(days_offset))
    
    customers.append({
        'customer_id': fake.uuid4()[:8],
        'signup_date': signup_date,
        'acquisition_channel': np.random.choice(channels),
        'country': np.random.choice(countries),
        'industry': np.random.choice(industries)
    })

df_customers = pd.DataFrame(customers)

# --- 3. SUBSCRIPTIONS & INVOICES & PAYMENTS ---
subscriptions = []
invoices = []
payments = []
churn_reasons = ['Too Expensive', 'Switching to Competitor', 'Technical Issues', 'No Longer Needed', 'Bad Support']

for _, cust in df_customers.iterrows():
    # 30% chance of churn
    will_churn = np.random.choice([True, False], p=[0.3, 0.7])
    
    plan = df_plans.sample(1).iloc[0]
    start_date = cust['signup_date']
    
    if will_churn:
        # Churn happens between 1 and 18 months
        months_active = np.random.randint(1, 18)
        end_date = start_date + timedelta(days=months_active * 30)
        
        if end_date > END_DATE:
            end_date = None # Hasn't churned YET in our observation window
            status = 'Active'
            cancellation_reason = None
        else:
            status = 'Cancelled'
            cancellation_reason = np.random.choice(churn_reasons)
    else:
        end_date = None
        status = 'Active'
        cancellation_reason = None
        
    sub_id = fake.uuid4()[:8]
    
    subscriptions.append({
        'subscription_id': sub_id,
        'customer_id': cust['customer_id'],
        'plan_id': plan['plan_id'],
        'start_date': start_date,
        'end_date': end_date,
        'status': status,
        'cancellation_reason': cancellation_reason
    })
    
    # Generate Monthly Invoices
    curr_date = start_date
    final_billing_date = end_date if end_date else END_DATE
    
    while curr_date <= final_billing_date:
        inv_id = fake.uuid4()[:8]
        amount = plan['price']
        discount = 20.00 if plan['discount_flag'] else 0.00
        
        invoices.append({
            'invoice_id': inv_id,
            'subscription_id': sub_id,
            'invoice_date': curr_date,
            'amount': amount,
            'discount_amount': discount
        })
        
        # Payments
        # 5% Involuntary Churn risk (Failed Payment)
        payment_status = np.random.choice(['Paid', 'Failed'], p=[0.95, 0.05])
        
        payments.append({
            'payment_id': fake.uuid4()[:8],
            'invoice_id': inv_id,
            'payment_status': payment_status,
            'payment_date': curr_date + timedelta(days=random.randint(0, 5))
        })
        
        curr_date += timedelta(days=30)

df_subs = pd.DataFrame(subscriptions)
df_invoices = pd.DataFrame(invoices)
df_payments = pd.DataFrame(payments)

# --- 4. USAGE EVENTS (Simulating Engagement) ---
usage_data = []
features = ['Dashboard', 'Report Export', 'API Call', 'User Invite', 'Settings Change']

for _, sub in df_subs.iterrows():
    # If churned, usage drops off before end_date
    limit_date = sub['end_date'] if pd.notna(sub['end_date']) else END_DATE
    start_dt = sub['start_date']
    
    # Generate 5-20 interactions per month
    while start_dt < limit_date:
        if np.random.random() > 0.8: # Skip some days (not daily usage)
             usage_data.append({
                'customer_id': sub['customer_id'],
                'feature_name': np.random.choice(features),
                'event_date': start_dt + timedelta(hours=random.randint(9, 17)),
                'usage_count': random.randint(1, 10)
            })
        start_dt += timedelta(days=random.randint(1, 3))

df_usage = pd.DataFrame(usage_data)

# --- SAVE TO CSV ---
df_customers.to_csv(f'{OUTPUT_DIR}/customers.csv', index=False)
df_plans.to_csv(f'{OUTPUT_DIR}/subscription_plans.csv', index=False)
df_subs.to_csv(f'{OUTPUT_DIR}/subscriptions.csv', index=False)
df_invoices.to_csv(f'{OUTPUT_DIR}/invoices.csv', index=False)
df_payments.to_csv(f'{OUTPUT_DIR}/payments.csv', index=False)
df_usage.to_csv(f'{OUTPUT_DIR}/usage_events.csv', index=False)

print(f"✅ Data Generated in {OUTPUT_DIR}")