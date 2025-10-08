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

# --- FIX for KeyError: Strip whitespace from all column names ---
df.columns = df.columns.str.strip()

# Ensure numeric columns are actually numeric after loading
numeric_cols = ['Child Expenditure Limit Assigned', 'Success', 'Pending', 'Re-Initiated', 'Balance']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) # 'coerce' turns non-numeric text into NaN, then fill NaN with 0

# --- Sidebar Filters ---
st.sidebar.header("Filter Data")

# Filter 1: State Selection
selected_state = st.sidebar.selectbox(
    "Select State:",
    options=['All States'] + sorted(df['State'].astype(str).unique().tolist())
)

# Filter 2: Category Selection
selected_category = st.sidebar.selectbox(
    "Select Category:",
    options=['All Categories'] + sorted(df['Category'].astype(str).unique().tolist())
)

# Apply Filters
df_filtered = df.copy()

if selected_state != 'All States':
    df_filtered = df_filtered[df_filtered['State'] == selected_state]

if selected_category != 'All Categories':
    df_filtered = df_filtered[df_filtered['Category'] == selected_category]


# --- 2. Calculate KPIs on Filtered Data ---
total_limit = df_filtered['Child Expenditure Limit Assigned'].sum()
total_success = df_filtered['Success'].sum()
total_pending = df_filtered['Pending'].sum()
total_balance = df_filtered['Balance'].sum()

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
    category_summary = df_filtered.groupby('Category')[['Success', 'Pending', 'Re-Initiated']].sum()
    st.bar_chart(category_summary)

# Visualization 2: Top 10 States by Limit
with col_vis2:
    st.subheader("🗺️ Top 10 States by Limit Assigned")
    
    # Check if a state filter is applied before showing Top 10 states
    if selected_state == 'All States':
        state_summary = df_filtered.groupby('State')['Child Expenditure Limit Assigned'].sum().nlargest(10).reset_index()
        state_summary = state_summary.set_index('State')
        st.bar_chart(state_summary)
    else:
        st.info("Top 10 States chart is only available when 'All States' filter is selected.")


# --- Detailed Data Table ---
st.divider()
st.subheader("📋 Raw Data View")
st.dataframe(df_filtered)
