# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Farm Financial Dashboard")
st.title("🌾 Farm Financial Analytics Dashboard")

# --- File upload
st.sidebar.header("📂 Upload Your CSV Files")
laborsot = st.sidebar.file_uploader("Labor Cost SOT", type="csv")
payroll = st.sidebar.file_uploader("Payroll Register", type="csv")
sales = st.sidebar.file_uploader("Sales Orders", type="csv")
harvest = st.sidebar.file_uploader("Harvest Yields", type="csv")
gl = st.sidebar.file_uploader("GL Summary", type="csv")
budget = st.sidebar.file_uploader("Budget Plan", type="csv")

if not all([laborsot, sales, harvest, gl, budget]):
    st.warning("Please upload all required CSVs.")
    st.stop()

# --- Load data
laborsot = pd.read_csv(laborsot, parse_dates=['Week Start Date'])
sales = pd.read_csv(sales, parse_dates=['Week Start Date'])
harvest = pd.read_csv(harvest, parse_dates=['Week Start Date'])
gl = pd.read_csv(gl, parse_dates=['Week Start Date'])
budget = pd.read_csv(budget, parse_dates=['Week Start Date'])

# --- Tabs
view = st.selectbox("Choose View:", [
    "Crop ROI",
    "Labor Cost by Job Type",
    "Labor Budget vs Actual",
    "GL Actual vs Budget"
])

# --- Crop ROI View
if view == "Crop ROI":
    st.header("📈 Crop ROI per Pound Over Time")
    sales_crop = sales.groupby(['Week Start Date', 'Crop'])['Total Sales ($)'].sum().reset_index()
    harvest_crop = harvest.groupby(['Week Start Date', 'Crop'])['Pounds Harvested'].sum().reset_index()
    labor_crop = laborsot.groupby(['Week Start Date', 'Crop'])['Total Pay ($)'].sum().reset_index()
    df = sales_crop.merge(harvest_crop, on=['Week Start Date', 'Crop'], how='outer')
    df = df.merge(labor_crop, on=['Week Start Date', 'Crop'], how='outer').fillna(0)
    df['ROI per lb'] = (df['Total Sales ($)'] - df['Total Pay ($)']) / df['Pounds Harvested'].replace(0, np.nan)

    pivot = df.pivot(index='Week Start Date', columns='Crop', values='ROI per lb')
    st.line_chart(pivot)
    st.dataframe(df.sort_values('Week Start Date'))

# --- Labor Cost by Job Type View
elif view == "Labor Cost by Job Type":
    st.header("🧱 Labor Cost by Job Type")
    job_df = laborsot.groupby(['Week Start Date', 'Job Type'])['Total Pay ($)'].sum().reset_index()
    pivot = job_df.pivot(index='Week Start Date', columns='Job Type', values='Total Pay ($)').fillna(0)
    st.line_chart(pivot)
    st.dataframe(job_df.sort_values('Week Start Date'))

# --- Labor Budget vs Actual View
elif view == "Labor Budget vs Actual":
    st.header("🧾 Budget vs Actual Labor Costs by Crew")
    actual = laborsot.groupby(['Week Start Date', 'Crew']).agg({
        'Worker ID': 'nunique',
        'Regular Hours Worked': 'sum',
        'Overtime Hours Worked': 'sum',
        'Total Pay ($)': 'sum'
    }).reset_index().rename(columns={
        'Worker ID': 'Unique Workers',
        'Regular Hours Worked': 'Total Reg Hours',
        'Overtime Hours Worked': 'Total OT Hours',
        'Total Pay ($)': 'Actual Pay'
    })
    forecast = budget.groupby(['Week Start Date', 'Crew'])['Total Pay Forecast ($)'].sum().reset_index()
    df = actual.merge(forecast, on=['Week Start Date', 'Crew'], how='outer').fillna(0)
    df['Variance ($)'] = df['Actual Pay'] - df['Total Pay Forecast ($)']

    for crew in df['Crew'].unique():
        crew_df = df[df['Crew'] == crew].set_index('Week Start Date')
        st.subheader(f"👷‍♀️ Crew: {crew}")
        st.line_chart(crew_df[['Actual Pay', 'Total Pay Forecast ($)', 'Variance ($)']])

    st.dataframe(df)

# --- GL Actual vs Budget View
elif view == "GL Actual vs Budget":
    st.header("📚 GL Actual vs Budget Comparison")
    actual = gl.groupby(['Week Start Date', 'GL Category'])['Amount ($)'].sum().reset_index()
    budget_labor = budget.copy()
    budget_labor['GL Category'] = 'Labor Budget Forecast'
    budget_grouped = budget_labor.groupby(['Week Start Date', 'GL Category'])['Total Pay Forecast ($)'].sum().reset_index()
    budget_grouped = budget_grouped.rename(columns={'Total Pay Forecast ($)': 'Amount ($)'})
    df = pd.concat([actual, budget_grouped], axis=0).fillna(0)
    pivot = df.pivot(index='Week Start Date', columns='GL Category', values='Amount ($)').fillna(0)

    st.line_chart(pivot)
    st.dataframe(df.sort_values('Week Start Date'))
