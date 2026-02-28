import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add parent directory to path so we can import our existing DB connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.forecast_model import get_db_engine, forecast_mrr

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SaaS Intelligence Dashboard", page_icon="📈", layout="wide")
st.title("📈 SaaS Customer Lifecycle & Revenue Intelligence")
st.markdown("Executive dashboard tracking MRR, Churn, Cohort Retention, and Predicted Risk.")

# --- DATA LOADING (CACHED FOR PERFORMANCE) ---
@st.cache_data
def load_data():
    engine = get_db_engine()
    
    # 1. Revenue Data
    df_mrr = pd.read_sql("SELECT * FROM core_mrr_movements ORDER BY month_date", engine)
    
    # 2. Churn Data
    df_churn = pd.read_sql("SELECT * FROM core_churn_metrics ORDER BY month_date", engine)
    
    # 3. Cohort Data
    df_cohorts = pd.read_sql("SELECT * FROM core_cohort_retention", engine)
    
    # 4. Risk Data (From Phase 4 CSV)
    risk_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed', 'risk_segments.csv')
    df_risk = pd.read_csv(risk_path) if os.path.exists(risk_path) else pd.DataFrame()
    
    return df_mrr, df_churn, df_cohorts, df_risk

with st.spinner("Loading Data Engine..."):
    df_mrr, df_churn, df_cohorts, df_risk = load_data()

# --- DASHBOARD TABS ---
# The PDF requested 5 distinct sections. We'll use Streamlit Tabs for a clean UI.
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💵 Revenue Overview", 
    "🚨 Churn Intelligence", 
    "🗓️ Retention & Cohorts", 
    "⚠️ Usage & Risk", 
    "🔮 Forecast vs Actual"
])

# ==========================================
# TAB 1: REVENUE OVERVIEW
# ==========================================
with tab1:
    st.header("Revenue Overview")
    
    # Top KPI Cards
    col1, col2, col3 = st.columns(3)
    current_mrr = df_mrr['total_mrr'].iloc[-1]
    prev_mrr = df_mrr['total_mrr'].iloc[-2]
    mrr_growth = ((current_mrr - prev_mrr) / prev_mrr) * 100
    
    col1.metric("Current MRR", f"${current_mrr:,.2f}", f"{mrr_growth:.1f}%")
    col2.metric("Annual Recurring Revenue (ARR)", f"${current_mrr * 12:,.2f}")
    col3.metric("Net New MRR (Last Month)", f"${df_mrr['net_new_mrr'].iloc[-1]:,.2f}")

    # MRR Trend Chart
    st.subheader("Total MRR Over Time")
    fig_mrr = px.area(df_mrr, x='month_date', y='total_mrr', title="MRR Growth Trend")
    st.plotly_chart(fig_mrr, width="stretch")
    
    # MRR Bridge (New vs Expansion vs Contraction vs Churn)
    st.subheader("MRR Movements (The Bridge)")
    df_bridge = df_mrr[['month_date', 'new_mrr', 'expansion_mrr', 'contraction_mrr', 'churned_mrr']].melt(id_vars='month_date')
    fig_bridge = px.bar(df_bridge, x='month_date', y='value', color='variable', barmode='relative', 
                        title="Monthly MRR Breakdown", 
                        color_discrete_map={'new_mrr':'#2ca02c', 'expansion_mrr':'#1f77b4', 'contraction_mrr':'#ff7f0e', 'churned_mrr':'#d62728'})
    st.plotly_chart(fig_bridge, width="stretch")

# ==========================================
# TAB 2: CHURN INTELLIGENCE
# ==========================================
with tab2:
    st.header("Churn Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overall Churn Rate (%)")
        fig_churn_rate = px.line(df_churn, x='month_date', y='churn_rate_pct', markers=True, title="Monthly Churn Rate")
        fig_churn_rate.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_churn_rate, width="stretch")
        
    with col2:
        st.subheader("Voluntary vs Involuntary Churn")
        df_churn_types = df_churn[['month_date', 'voluntary_churn_count', 'involuntary_churn_count']].melt(id_vars='month_date')
        fig_churn_type = px.bar(df_churn_types, x='month_date', y='value', color='variable', title="Churn by Reason")
        st.plotly_chart(fig_churn_type, width="stretch")

# ==========================================
# TAB 3: RETENTION & COHORTS
# ==========================================
with tab3:
    st.header("Cohort Retention Analysis")
    st.markdown("*Percentage of users retained from their initial signup month.*")
    
    # Pivot the data for the heatmap
    cohort_pivot = df_cohorts.pivot(index='cohort_month', columns='month_index', values='retention_rate_pct')
    
    # Ensure index is string for better formatting on Y axis
    cohort_pivot.index = cohort_pivot.index.astype(str)
    
    fig_heatmap = px.imshow(cohort_pivot, 
                            text_auto=".1f", 
                            aspect="auto",
                            color_continuous_scale="RdYlGn",
                            labels=dict(x="Months Since Signup", y="Cohort Month", color="Retention %"),
                            title="Monthly Cohort Retention Heatmap")
    st.plotly_chart(fig_heatmap, width="stretch")

# ==========================================
# TAB 4: USAGE & RISK
# ==========================================
with tab4:
    st.header("Usage Signals & At-Risk Segments")
    
    if not df_risk.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Customer Risk Distribution")
            risk_counts = df_risk['risk_level'].value_counts().reset_index()
            risk_counts.columns = ['Risk Level', 'Customer Count']
            fig_risk = px.pie(risk_counts, values='Customer Count', names='Risk Level', 
                              color='Risk Level',
                              color_discrete_map={'Low Risk':'#2ca02c', 'Medium Risk':'#ffaa00', 'High Risk':'#d62728'},
                              hole=0.4)
            st.plotly_chart(fig_risk, width="stretch")
            
        with col2:
            st.subheader("Usage Drop vs Tenure")
            # Showing scatter of usage drop to visualize why users are high risk
            df_risk['usage_drop'] = df_risk['previous_usage'] - df_risk['current_usage']
            fig_scatter = px.scatter(df_risk, x='tenure_days', y='usage_drop', color='risk_level',
                                     color_discrete_map={'Low Risk':'#2ca02c', 'Medium Risk':'#ffaa00', 'High Risk':'#d62728'},
                                     title="Identifying Early Churn Signals",
                                     labels={'tenure_days':'Days Since Signup', 'usage_drop': 'Drop in Feature Usage'})
            st.plotly_chart(fig_scatter, width="stretch")
    else:
        st.warning("Risk segments data not found. Please run src/risk_segmentation.py first.")

# ==========================================
# TAB 5: FORECAST VS ACTUAL
# ==========================================
with tab5:
    st.header("6-Month Revenue Forecast")
    
    # Generate the forecast on the fly using our Phase 4 module!
    with st.spinner("Running Linear Regression Forecast..."):
        df_forecast = forecast_mrr()
    
    # Combine Historical and Forecasted Data for a seamless chart
    historical_mrr = df_mrr[['month_date', 'total_mrr']].copy()
    historical_mrr.rename(columns={'total_mrr': 'MRR'}, inplace=True)
    historical_mrr['Type'] = 'Actual'
    
    future_mrr = df_forecast[['month_date', 'forecasted_mrr']].copy()
    future_mrr.rename(columns={'forecasted_mrr': 'MRR'}, inplace=True)
    future_mrr['Type'] = 'Forecast'
    
    combined_mrr = pd.concat([historical_mrr, future_mrr])
    
    fig_forecast = px.line(combined_mrr, x='month_date', y='MRR', color='Type', 
                           line_dash='Type', markers=True,
                           title="Actual vs Predicted MRR (Next 6 Months)",
                           color_discrete_map={'Actual':'#1f77b4', 'Forecast':'#ff7f0e'})
    st.plotly_chart(fig_forecast, width="stretch")
    
    st.success("✅ Dashboard successfully synced with PostgreSQL Data Engine & Python ML layer.")