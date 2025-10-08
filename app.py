import streamlit as st
import pandas as pd
import os
import requests # Need this for fetching data from a URL

# --- Configuration ---
# Google Sheet ID extracted from your URL: 
# https://docs.google.com/spreadsheets/d/1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo/edit?gid=1933215839#gid=1933215839
SHEET_ID = '1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo'
# The gid is for the specific sheet tab within the file (MAIN DATA 07.10.25)
GID = '1933215839' 

# Construct the public CSV export URL for the specific sheet tab
DATA_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'

# Define the expected, clean column names (same as before)
CLEAN_COLUMN_NAMES = [
    'sr_no', 'agency_name', 'unique_id', 'state', 'agency_type', 
    'category', 'child_expenditure_limit_assigned', 'success', 
    'pending', 're_initiated', 'balance'
]

# Function to load data safely and efficiently
@st.cache_data(ttl=60) # Cache for 60 seconds to enable "real-time" feel
def load_data(url):
    """
    Loads data directly from the Google Sheet CSV export URL.
    This bypasses local file issues and is more reliable for live data.
    """
    try:
        # Use pandas read_csv directly on the URL
        # We assume the data starts immediately (no malformed header)
        df = pd.read_csv(
            url, 
            header=None, # Skip the default header row
            names=CLEAN_COLUMN_NAMES, # Assign clean column names
            skiprows=1 # Skip the actual header row from the sheet
        )
        
        # Check if the data fetch was successful but returned an error page (common issue)
        if len(df.columns) != len(CLEAN_COLUMN_NAMES):
            st.error("Data loading failed. Check if the Google Sheet link is public and the GID is correct.")
            return pd.DataFrame()

        st.success("Data loaded successfully from Google Sheet URL.")
        return df

    except Exception as e:
        st.error(f"Failed to fetch data from Google Sheet URL. Error: {e}")
        return pd.DataFrame()

# --- Load Data and Handle Failure ---
df = load_data(DATA_URL)

if df.empty:
    st.stop() # Stop the script if data failed to load

# The column names are now guaranteed to be clean.
numeric_cols = ['child_expenditure_limit_assigned', 'success', 'pending', 're_initiated', 'balance']

# Ensure numeric columns are actually numeric after loading
for col in numeric_cols:
    # Handle the fact that non-English languages/locales sometimes use commas (,) for decimal separators.
    # We will use regex to clean up potential non-numeric characters before conversion.
    # This addresses the "data entry is in different language" issue for numbers.
    df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) 

# --- Sidebar Filters ---
st.sidebar.header("Filter Data")

# Filter 1: State Selection (Using cleaned 'state' column)
selected_state = st.sidebar.selectbox(
    "Select State:",
    options=['All States'] + sorted(df['state'].astype(str).unique().tolist())
)

# Filter 2: Category Selection (Using cleaned 'category' column)
selected_category = st.sidebar.selectbox(
    "Select Category:",
    options=['All Categories'] + sorted(df['category'].astype(str).unique().tolist())
)

# Apply Filters
df_filtered = df.copy()

if selected_state != 'All States':
    df_filtered = df_filtered[df_filtered['state'] == selected_state]

if selected_category != 'All Categories':
    df_filtered = df_filtered[df_filtered['category'] == selected_category]


# --- 2. Calculate KPIs on Filtered Data ---
total_limit = df_filtered['child_expenditure_limit_assigned'].sum()
total_success = df_filtered['success'].sum()
total_pending = df_filtered['pending'].sum()
total_balance = df_filtered['balance'].sum()

# Safe calculation for success rate
success_rate = (total_success / total_limit) * 100 if total_limit != 0 else 0


# --- 3. Dashboard Layout ---
st.set_page_config(layout="wide")
st.title("💰 Agency Expenditure Dashboard (Live Data)")
st.markdown(f"**Data displayed for:** State: **{selected_state}** | Category: **{selected_category}** | Auto-refreshes every 60 seconds.")
st.divider()

# KPI Header
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Budget Assigned (M)", f"${total_limit:,.2f}")
col2.metric("Total Success (M)", f"${total_success:,.2f}", delta_color="normal")
col3.metric("Total Pending (M)", f"${total_pending:,.2f}")
col4.metric("Success Rate", f"{success_rate:,.2f}%", delta_color="inverse")


# --- Main Visualizations ---

col_vis1, col_vis2 = st.columns(2)

# Visualization 1: Expenditure Status by Category
with col_vis1:
    st.subheader("📊 Expenditure Breakdown by Category Status")
    # Group and ensure no NaN columns before sum
    category_summary = df_filtered.groupby('category')[['success', 'pending', 're_initiated']].sum()
    st.bar_chart(category_summary)

# Visualization 2: Top 10 States by Limit
with col_vis2:
    st.subheader("🗺️ Top 10 States by Limit Assigned")
    
    # Check if a state filter is applied before showing Top 10 states
    if selected_state == 'All States':
        state_summary = df_filtered.groupby('state')['child_expenditure_limit_assigned'].sum().nlargest(10).reset_index()
        state_summary = state_summary.set_index('state')
        st.bar_chart(state_summary)
    else:
        st.info("Top 10 States chart is only available when 'All States' filter is selected.")


# --- Detailed Data Table ---
st.divider()
st.subheader("📋 Raw Data View")
st.dataframe(df_filtered)
