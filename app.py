import streamlit as st
import pandas as pd
import os

# --- Configuration ---
# NOTE: Ensure this CSV file is uploaded to the same directory as app.py
DATA_FILE = "Book3.xlsx - MAIN DATA 07.10.25.csv"

# Function to load data safely and efficiently
@st.cache_data
def load_data(file_path):
    """
    Loads and caches data from the CSV file, trying different encodings 
    and the Python engine to handle file structure and encoding errors.
    """
    if not os.path.exists(file_path):
        st.error(f"Data file not found: {file_path}. Please ensure it is in the same directory.")
        return pd.DataFrame()
    
    # Try common encodings and include error handling for bad lines
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            # Attempt to read the CSV using the more flexible Python engine
            df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip', engine='python')
            
            # --- Optional Logging for Debugging ---
            st.success(f"Data loaded successfully using {encoding} encoding and Python engine. (Some bad lines may have been skipped)")
            
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # If a complex error occurs, log it and continue trying other encodings
            st.warning(f"Failed to read with {encoding} and Python engine. Trying next encoding. Error: {e}")
            continue
    
    st.error("Failed to read CSV with all common encodings and the Python engine. Please check the file's encoding or structure.")
    return pd.DataFrame()

# --- Load Data and Handle Failure ---
df = load_data(DATA_FILE)

if df.empty:
    st.stop() # Stop the script if data failed to load

# --- FIX for KeyError: AGGRESSIVE COLUMN CLEANING ---
# 1. Strip all leading/trailing whitespace
df.columns = df.columns.str.strip()

# 2. Convert to lowercase and replace spaces/special characters with underscores
# This ensures we have clean, consistent column names regardless of hidden characters.
df.columns = df.columns.str.lower().str.replace(' ', '_', regex=False).str.replace(r'[^\w]+', '', regex=True)

# Update the list of expected column names to the new, clean format
numeric_cols = ['child_expenditure_limit_assigned', 'success', 'pending', 're_initiated', 'balance']

# Ensure numeric columns are actually numeric after loading
for col in numeric_cols:
    # Check if the cleaned column name exists before trying to access it
    if col not in df.columns:
        st.error(f"Critical Error: Required column '{col}' not found after cleaning header. The original header name might be severely malformed.")
        st.dataframe(df.columns.tolist())
        st.stop()
        
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) # 'coerce' turns non-numeric text into NaN, then fill NaN with 0

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
st.title("💰 Agency Expenditure Dashboard")
st.markdown(f"**Data displayed for:** State: **{selected_state}** | Category: **{selected_category}**")
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
