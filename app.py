import streamlit as st
import pandas as pd
import os # Import the os module

# 1. Load Data (Critical Change: Use a relative path or st.cache_data)
# BEST PRACTICE: Ensure the CSV file is in the same directory as this Python script
# and include a function with @st.cache_data for performance.

@st.cache_data
def load_data(file_path):
    # Check if the file exists before reading
    if not os.path.exists(file_path):
        st.error(f"Data file not found at: {file_path}")
        return pd.DataFrame() # Return an empty DataFrame on error
    return pd.read_csv(file_path)

# Assign the file name to a variable for clarity
DATA_FILE = "Book3.xlsx - MAIN DATA 07.10.25.csv"
df = load_data(DATA_FILE)

# Check if data loaded successfully before proceeding
if df.empty:
    st.stop() # Stop the script execution if data load failed

# 2. Calculate KPIs
total_limit = df['Child Expenditure Limit Assigned'].sum()
total_success = df['Success'].sum()

# Add a check for division by zero
success_rate = (total_success / total_limit) * 100 if total_limit != 0 else 0

# 3. Create Dashboard Layout
st.set_page_config(layout="wide")
st.title("Agency Expenditure Dashboard")

# KPI Header
# ... (rest of your existing code is fine) ...
col1, col2, col3 = st.columns(3)
col1.metric("Total Budget Assigned", f"${total_limit:,.2f}")
col2.metric("Total Success", f"${total_success:,.2f}")
col3.metric("Success Rate", f"{success_rate:,.2f}%")

st.divider()

# Visualization 1: Expenditure Status by Category
st.subheader("Expenditure Breakdown by Agency Category")
category_summary = df.groupby('Category')[['Success', 'Pending', 'Re-Initiated']].sum()
st.bar_chart(category_summary)


## --- Recommended Addition: Second Visualization ---
st.subheader("Top 10 States by Total Expenditure Limit")

# Calculate Top 10 States
state_summary = df.groupby('State')['Child Expenditure Limit Assigned'].sum().nlargest(10).reset_index()

# Use st.bar_chart for simplicity, setting the x-index manually
state_summary = state_summary.set_index('State')
st.bar_chart(state_summary)
