import pandas as pd
from sqlalchemy import create_engine, text
from configparser import ConfigParser
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'database.ini')

def load_config(filename=CONFIG_FILE, section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db_config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return db_config

def get_db_engine():
    config = load_config()
    url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    return create_engine(url)

def truncate_tables(engine):
    """Wipes all data before reloading to prevent duplicates."""
    print("🧹 Cleaning old data (Truncating tables)...")
    with engine.connect() as conn:
        # Cascade ensures we delete child rows (payments) before parents (invoices)
        conn.execute(text("TRUNCATE TABLE payments, invoices, subscriptions, customers, subscription_plans, usage_events RESTART IDENTITY CASCADE;"))
        conn.commit()
    print("✨ Tables cleaned.")

def load_data():
    engine = get_db_engine()
    print("🔌 Connected to PostgreSQL...")

    # OPTIONAL: Wipe data before loading (Enable this if you want fresh data every time)
    try:
        truncate_tables(engine)
    except Exception as e:
        print(f"⚠️ Could not truncate tables (First run?): {e}")

    files_map = [
        ('subscription_plans.csv', 'subscription_plans'),
        ('customers.csv', 'customers'),
        ('subscriptions.csv', 'subscriptions'),
        ('invoices.csv', 'invoices'),
        ('payments.csv', 'payments'),
        ('usage_events.csv', 'usage_events')
    ]

    for csv_file, table_name in files_map:
        file_path = os.path.join(DATA_DIR, csv_file)
        
        if os.path.exists(file_path):
            print(f"⏳ Loading {table_name}...")
            try:
                df = pd.read_csv(file_path)
                
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                # if_exists='append' works now because we truncated first!
                df.to_sql(table_name, engine, if_exists='append', index=False)
                print(f"✅ Success: Loaded {len(df)} rows into '{table_name}'")
            except Exception as e:
                print(f"❌ Error loading {table_name}: {e}")
        else:
            print(f"⚠️ Warning: File {csv_file} not found.")

if __name__ == "__main__":
    load_data()