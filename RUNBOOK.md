# 🚀 Operational Runbook: SaaS Revenue Retention Engine

## 📖 Overview
This runbook provides step-by-step instructions to configure, deploy, and operate the **SaaS Revenue Retention Engine**. The pipeline simulates a Medallion Architecture data stack, generating synthetic data, running an ETL process into a PostgreSQL database, executing machine learning models, and deploying a Streamlit dashboard.

---

## ⚙️ Prerequisites
Before running this project, ensure you have the following installed:
* **Python:** `v3.9` or higher
* **Git:** For cloning the repository
* **PostgreSQL:** Running locally or remotely (Port `5432` by default)
* **pgAdmin or DBeaver** (Optional): For inspecting the database output

---

## 🛠️ Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Saqlain0911/SaaS-Revenue-Retention-Engine.git
cd SaaS-Revenue-Retention-Engine

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Database Connection
```bash
# Update the database connection details in src/etl_loader.py
# Update the database connection details in src/forecast_model.py
```

### 5. Run the Pipeline
```bash
python main.py
```
