import os
import pandas as pd
from forecast_model import get_db_engine # Re-use the connection we already built!

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'processed', 'risk_segments.csv')

def run_risk_segmentation():
    print("🔍 Analyzing Customer Usage Signals for Churn Risk...")
    engine = get_db_engine()
    
    # SQL query to get current usage, previous usage, and user tenure
    query = """
        WITH latest_usage AS (
            SELECT customer_id, total_feature_actions
            FROM fct_usage_signals
            WHERE month_date = (SELECT MAX(month_date) FROM fct_usage_signals)
        ),
        previous_usage AS (
            SELECT customer_id, total_feature_actions
            FROM fct_usage_signals
            WHERE month_date = (SELECT MAX(month_date) - INTERVAL '1 month' FROM fct_usage_signals)
        ),
        customer_tenure AS (
            SELECT customer_id, plan_id,
                   (CURRENT_DATE - start_date) AS tenure_days
            FROM subscriptions
            WHERE status = 'Active'
        )
        SELECT 
            c.customer_id,
            c.plan_id,
            c.tenure_days,
            COALESCE(l.total_feature_actions, 0) as current_usage,
            COALESCE(p.total_feature_actions, 0) as previous_usage
        FROM customer_tenure c
        LEFT JOIN latest_usage l ON c.customer_id = l.customer_id
        LEFT JOIN previous_usage p ON c.customer_id = p.customer_id
    """
    
    df = pd.read_sql(query, engine)
    
    # Calculate drop in engagement
    df['usage_drop'] = df['previous_usage'] - df['current_usage']
    
    # --- RISK SCORING ALGORITHM ---
    def assign_risk(row):
        # High Risk: Massive drop in usage OR zero current usage OR new user with drop
        if row['current_usage'] == 0:
            return 'High Risk'
        elif row['usage_drop'] > 15:
            return 'High Risk'
        elif row['usage_drop'] > 5 and row['tenure_days'] < 90:
            return 'High Risk' # Early churn signal!
            
        # Medium Risk: Slight drop in usage
        elif row['usage_drop'] > 0:
            return 'Medium Risk'
            
        # Low Risk: Usage is stable or growing
        else:
            return 'Low Risk'
            
    df['risk_level'] = df.apply(assign_risk, axis=1)
    
    # Save the output for the Dashboard (Phase 5)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("\n🎯 --- CUSTOMER RISK SEGMENTS --- 🎯")
    print(df['risk_level'].value_counts())
    print(f"\n✅ Data exported to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_risk_segmentation()