import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from configparser import ConfigParser
from sklearn.linear_model import LinearRegression
from datetime import timedelta

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'database.ini')

def load_config(filename=CONFIG_FILE, section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db_config = {}
    if parser.has_section(section):
        for param in parser.items(section):
            db_config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    return db_config

def get_db_engine():
    config = load_config()
    url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    return create_engine(url)

def forecast_mrr():
    print("🔌 Connecting to Database to fetch MRR data...")
    engine = get_db_engine()
    
    # 1. Pull Data from our Gold/Mart View!
    query = """
        SELECT month_date, total_mrr 
        FROM core_mrr_movements 
        WHERE total_mrr IS NOT NULL
        ORDER BY month_date ASC;
    """
    df = pd.read_sql(query, engine)
    df['month_date'] = pd.to_datetime(df['month_date'])
    
    if df.empty:
        print("⚠️ No data found. Make sure you generated data and ran the SQL views.")
        return

    print(f"📊 Historical Data Loaded: {len(df)} months of MRR.")

    # 2. Prepare Data for Linear Regression
    # Convert dates to ordinal numbers (e.g., days since 0001-01-01) so the math model can understand it
    df['date_ordinal'] = df['month_date'].map(pd.Timestamp.toordinal)
    
    X = df[['date_ordinal']]  # Features (Time)
    y = df['total_mrr']       # Target (Revenue)

    # 3. Train the Model (No deep ML, just simple interpretable linear regression)
    model = LinearRegression()
    model.fit(X, y)

    # 4. Generate Future Dates (Next 6 Months)
    last_date = df['month_date'].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 7)]
    
    future_df = pd.DataFrame({'month_date': future_dates})
    future_df['date_ordinal'] = future_df['month_date'].map(pd.Timestamp.toordinal)
    
    # 5. Predict Future MRR
    future_df['forecasted_mrr'] = model.predict(future_df[['date_ordinal']])
    future_df['forecasted_mrr'] = future_df['forecasted_mrr'].round(2)

    # 6. Display the Results
    print("\n🔮 --- 6 MONTH MRR FORECAST --- 🔮")
    # Formatting for terminal output
    output = future_df[['month_date', 'forecasted_mrr']].copy()
    output['month_date'] = output['month_date'].dt.strftime('%Y-%m')
    output.rename(columns={'month_date': 'Month', 'forecasted_mrr': 'Projected MRR ($)'}, inplace=True)
    print(output.to_string(index=False))
    print("----------------------------------\n")
    
    return future_df

if __name__ == "__main__":
    # You might need to install scikit-learn if you haven't already:
    # pip install scikit-learn
    forecast_mrr()