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
    actual = laborsot.groupby(['Week Start Date', 'Crew'])['Total Pay ($)'].sum().reset_index()
    forecast = budget.groupby(['Week Start Date', 'Crew'])['Total Pay Forecast ($)'].sum().reset_index()
    df = actual.merge(forecast, on=['Week Start Date', 'Crew'], how='outer').fillna(0)

    st.subheader("📊 Crew Forecast vs Actual Labor Costs")
    crews = df['Crew'].unique()
    fig, ax = plt.subplots(figsize=(14, 8))

    for i, crew in enumerate(crews):
        crew_df = df[df['Crew'] == crew]
        x = np.arange(len(crew_df['Week Start Date']))
        width = 0.35
        ax.bar(x + i*width, crew_df['Total Pay Forecast ($)'], width=width, label=f"{crew} Forecast", hatch='//', alpha=0.5)
        ax.bar(x + i*width, crew_df['Total Pay ($)'], width=width, label=f"{crew} Actual", alpha=0.7)

    ax.set_xticks(np.arange(len(crew_df['Week Start Date'])) + width/2)
    ax.set_xticklabels(crew_df['Week Start Date'].dt.strftime('%Y-%m-%d'), rotation=45)
    ax.set_ylabel('Pay ($)')
    ax.set_title('Crew Forecast vs Actual Labor Costs')
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.dataframe(df)

# --- GL Actual vs Budget View
elif view == "GL Actual vs Budget":
    st.header("📚 GL Actual vs Budget (High-Level Categories)")
    actual = gl.copy()
    # Map detailed GL categories into broader ones
    mapping = {
        'Material Expenses': 'Materials',
        'Shipping Supplies': 'Materials',
        'Stickers': 'Materials',
        'Pallets': 'Materials',
        'Line Chemicals': 'Materials',
        'Lime DPA': 'Materials',
        'Line Propane': 'Materials',
        'Nitrogen Tank': 'Materials',
        'Labor Benefits': 'Labor Costs',
        'FICA Taxes': 'Labor Costs',
        'FUTA Taxes': 'Labor Costs',
        'SUTA Taxes': 'Labor Costs',
        'PFMLA Contributions': 'Labor Costs',
        'Production Labor Total': 'Labor Costs',
        'Back Office Labor Total': 'Labor Costs'
    }
    actual['High-Level Category'] = actual['GL Category'].map(mapping).fillna('Other')
    budget_labor = budget.copy()
    budget_labor['GL Category'] = 'Labor Budget Forecast'
    budget_labor['High-Level Category'] = 'Labor Costs'
    budget_grouped = budget_labor.groupby(['Week Start Date', 'High-Level Category'])['Total Pay Forecast ($)'].sum().reset_index().rename(columns={'Total Pay Forecast ($)': 'Amount ($)'})

    actual_grouped = actual.groupby(['Week Start Date', 'High-Level Category'])['Amount ($)'].sum().reset_index()

    df = pd.concat([actual_grouped, budget_grouped], axis=0).fillna(0)
    pivot = df.pivot(index='Week Start Date', columns='High-Level Category', values='Amount ($)').fillna(0)

    st.line_chart(pivot)
    st.dataframe(df.sort_values('Week Start Date'))
