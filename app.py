import streamlit as st
import pandas as pd
import os
import requests 
import plotly.express as px

# --- Configuration ---
# Google Sheet ID extracted from your URL: 
SHEET_ID = '1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo'
GID = '1933215839' 
DATA_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'

CLEAN_COLUMN_NAMES = [
    'sr_no', 'agency_name', 'unique_id', 'state', 'agency_type', 
    'category', 'child_expenditure_limit_assigned', 'success', 
    'pending', 're_initiated', 'balance'
]

# --- LOGO URLS (PLACEHOLDERS - REPLACE THESE WITH YOUR STABLE LINKS) ---
# NOTE: Replace these URLs with stable, public links to your DST and MoST logos.
LOGO_URL_DST = "https://i.imgur.com/example/dst_logo.png" 
LOGO_URL_MOST = "https://i.imgur.com/example/most_logo.png" 

# --- Custom CSS for UI/Aesthetics (Enhanced with Animations) ---
st.markdown(
    """
    <style>
    /* 1. ANIMATION KEYFRAMES */
    @keyframes subtle-float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-3px); } /* Slight upward movement */
        100% { transform: translateY(0px); }
    }

    /* Global Font/Body cleanup */
    .stApp {
        background-color: var(--body-background-color);
    }
    
    /* Bolder sidebar header */
    .css-1d391kg, .css-1lcbmhc {
        font-weight: 700;
        font-size: 1.3rem;
        color: var(--text-color);
        padding-top: 0;
    }
    
    /* Custom styling for metrics (KPI cards) - Neutral background, clear border */
    [data-testid="stMetric"] {
        padding: 15px 15px;
        border-radius: 12px; 
        border: 1px solid var(--border-color); 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
        margin-bottom: 15px;
        background-color: var(--secondary-background-color);
        transition: transform 0.2s, box-shadow 0.2s; /* Faster transition for better feel */
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px); /* Increased lift on hover */
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1); /* Deeper shadow on hover */
    }

    /* Change the main header font/style AND add float animation */
    h1 {
        font-size: 2.5rem;
        color: #1f77b4; 
        font-weight: 700;
        margin-bottom: 5px;
        /* Animation applied to the title */
        animation: subtle-float 5s ease-in-out infinite; 
    }
    
    /* Style for Visualization Containers (Chart "Cards") */
    .chart-container {
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        background-color: var(--secondary-background-color);
        transition: transform 0.2s, box-shadow 0.2s; /* Added transition */
    }
    .chart-container:hover {
        transform: translateY(-2px); /* Slight lift on hover */
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Remove default Streamlit padding at the top */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Style for images in the header columns */
    [data-testid="column"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to load data safely and efficiently
@st.cache_data(ttl=60) # Cache for 60 seconds to enable "real-time" feel
def load_data(url):
    """Loads data directly from the public Google Sheet CSV export URL."""
    try:
        # Use pandas read_csv directly on the URL
        df = pd.read_csv(
            url, 
            header=None, # Skip the default header row
            names=CLEAN_COLUMN_NAMES, # Assign clean column names
            skiprows=1 # Skip the actual header row from the sheet
        )
        
        if len(df.columns) != len(CLEAN_COLUMN_NAMES) or df.empty:
            st.error("Data loading failed. Check sheet link/GID.")
            return pd.DataFrame()

        st.success("Data loaded successfully from Google Sheet URL.")
        return df

    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "403" in str(e):
            st.error(
                "Failed to fetch data: Unauthorized Error.\n\n"
                "Please ensure the Google Sheet is set to 'Anyone with the link' (Viewer access)."
            )
        else:
            st.error(f"Failed to fetch data from Google Sheet URL. Error: {e}")
        return pd.DataFrame()

# --- Load Data and Handle Failure ---
df = load_data(DATA_URL)

if df.empty:
    st.stop() 

# Data Cleaning
numeric_cols = ['child_expenditure_limit_assigned', 'success', 'pending', 're_initiated', 'balance']
for col in numeric_cols:
    df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) 

# --- Sidebar Filters ---
st.sidebar.markdown("## 🔍 **FILTER EXPENDITURE DATA**") # Bolder sidebar title

# --- Start Cascading Filters (Logic remains the same) ---
selected_state = st.sidebar.selectbox(
    "Select State:",
    options=['All States'] + sorted(df['state'].astype(str).str.upper().unique().tolist())
)

df_for_category_selection = df.copy()
if selected_state != 'All States':
    df_for_category_selection = df_for_category_selection[df_for_category_selection['state'].astype(str).str.upper() == selected_state]

selected_category = st.sidebar.selectbox(
    "Select Category:",
    options=['All Categories'] + sorted(df_for_category_selection['category'].astype(str).unique().tolist())
)

df_for_agency_selection = df_for_category_selection.copy()
if selected_category != 'All Categories':
    df_for_agency_selection = df_for_agency_selection[df_for_agency_selection['category'] == selected_category]

selected_agency = st.sidebar.selectbox(
    "Select Agency Name:",
    options=['All Agencies'] + sorted(df_for_agency_selection['agency_name'].astype(str).unique().tolist())
)

df_for_unique_code_selection = df_for_agency_selection.copy()
if selected_agency != 'All Agencies':
    df_for_unique_code_selection = df_for_unique_code_selection[df_for_agency_selection['agency_name'] == selected_agency]

selected_unique_id = st.sidebar.selectbox(
    "Agency Unique Code:",
    options=['All Codes'] + sorted(df_for_unique_code_selection['unique_id'].astype(str).unique().tolist())
)

# Apply Filters
df_filtered = df.copy()
if selected_state != 'All States':
    df_filtered = df_filtered[df_filtered['state'].astype(str).str.upper() == selected_state]
if selected_category != 'All Categories':
    df_filtered = df_filtered[df_filtered['category'] == selected_category]
if selected_agency != 'All Agencies':
    df_filtered = df_filtered[df_filtered['agency_name'] == selected_agency]
if selected_unique_id != 'All Codes':
    df_filtered = df_filtered[df_filtered['unique_id'] == selected_unique_id]

# Add instruction for theme switching in the sidebar 
st.sidebar.markdown("---")
st.sidebar.info("💡 **Theme Toggle:** Use the main menu (☰) at the top right to switch between Light and Dark mode.")

# --- 2. Calculate KPIs on Filtered Data ---
total_limit = df_filtered['child_expenditure_limit_assigned'].sum()
total_success = df_filtered['success'].sum()
total_pending = df_filtered['pending'].sum()
total_reinitiated = df_filtered['re_initiated'].sum()
total_balance = df_filtered['balance'].sum()

success_rate = (total_success / total_limit) * 100 if total_limit != 0 else 0


# --- 3. Dashboard Layout (Beautified) ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Financial Dashboard")

# --- NEW HEADER WITH LOGOS ---
col_logo1, col_title, col_logo2 = st.columns([1, 4, 1])

with col_logo1:
    # Display DST Logo
    st.image(LOGO_URL_DST, width=80) 

with col_title:
    # Main Title
    st.title("📊 **Financial Expenditure Dashboard: Live Performance**") 

with col_logo2:
    # Display MoST Logo
    st.image(LOGO_URL_MOST, width=80) 
    
st.markdown("---") 

# Get display data for header
filtered_states = df_filtered['state'].astype(str).unique().tolist()
display_states = ", ".join(filtered_states[:3])
if len(filtered_states) > 3:
    display_states += f" (+{len(filtered_states) - 3} more)"
elif len(filtered_states) == 0:
    display_states = "None"
elif len(filtered_states) == 1:
    display_states = filtered_states[0]
else:
    display_states = ", ".join(filtered_states)
    
st.markdown(f"""
    **Current Scope:** *State(s):* **{display_states}** | *Category:* **{selected_category}** | *Agency:* **{selected_agency}** | *Code:* **{selected_unique_id}** <br><small>Data updates live from the source.</small>
""", unsafe_allow_html=True)
st.markdown("---") 

# --- SCALING AND CURRENCY ---
CRORE_FACTOR = 10 
CURRENCY_LABEL = "INR (Cr)" 

# Scale the KPIs to Crores
limit_cr = total_limit / CRORE_FACTOR
success_cr = total_success / CRORE_FACTOR
pending_cr = total_pending / CRORE_FACTOR
reinitiated_cr = total_reinitiated / CRORE_FACTOR
balance_cr = total_balance / CRORE_FACTOR

# Determine color/delta cues for metrics
if success_rate > 80:
    success_rate_delta = f"Excellent (+{success_rate:,.2f}%)"
elif success_rate > 50:
    success_rate_delta = "Good"
elif success_rate < 30:
    success_rate_delta = "Needs Review"
else:
    success_rate_delta = "Moderate"

delta_color = "inverse" if success_rate < 30 else "normal" 

# KPI Header - 6 prominent columns
col1, col2, col3, col4, col5, col6 = st.columns(6) 

# Metrics: Total Limit, Total Success, Success Rate, Total Pending, Total Re-Initiated, Total Balance
col1.metric(f"Total Budget Assigned ({CURRENCY_LABEL})", f"₹{limit_cr:,.2f}")
col2.metric(f"Total Success ({CURRENCY_LABEL})", f"₹{success_cr:,.2f}", delta=success_rate_delta, delta_color=delta_color)
col3.metric("Success Rate", f"{success_rate:,.2f}%", delta_color=delta_color)
col4.metric(f"Total Pending ({CURRENCY_LABEL})", f"₹{pending_cr:,.2f}")
col5.metric(f"Total Re-Initiated ({CURRENCY_LABEL})", f"₹{reinitiated_cr:,.2f}")
col6.metric(f"Total Balance ({CURRENCY_LABEL})", f"₹{balance_cr:,.2f}", delta="Unspent", delta_color="inverse")

st.markdown("---") 


# --- Main Visualizations (Using Plotly Express) ---

col_vis1, col_vis2 = st.columns(2)

# Visualization 1: Expenditure Status by Category (Plotly Stacked Bar)
with col_vis1:
    # Use the custom CSS class for the container (New visual enhancement)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("✅ Status Breakdown by Agency Type")
    
    category_summary = df_filtered.groupby('category')[['success', 'pending', 're_initiated']].sum().reset_index()
    
    # Scale data for Plotly
    category_summary_cr = category_summary[['category']].copy()
    category_summary_cr[f'Success ({CURRENCY_LABEL})'] = category_summary['success'] / CRORE_FACTOR
    category_summary_cr[f'Pending ({CURRENCY_LABEL})'] = category_summary['pending'] / CRORE_FACTOR
    category_summary_cr[f'Re-Initiated ({CURRENCY_LABEL})'] = category_summary['re_initiated'] / CRORE_FACTOR

    # Melt DataFrame for Plotly stacked bar chart
    category_melted = pd.melt(
        category_summary_cr, 
        id_vars='category', 
        value_vars=[f'Success ({CURRENCY_LABEL})', f'Pending ({CURRENCY_LABEL})', f'Re-Initiated ({CURRENCY_LABEL})'],
        var_name='Status', 
        value_name='Amount (Cr)'
    )

    fig1 = px.bar(
        category_melted,
        x='category',
        y='Amount (Cr)',
        color='Status',
        title='Utilization Status Across Categories',
        labels={'category': 'Agency Type'},
        color_discrete_map={ # Maintain appealing and consistent colors
            f'Success ({CURRENCY_LABEL})': '#2ecc71', # Emerald Green
            f'Pending ({CURRENCY_LABEL})': '#f1c40f', # Sunflower Yellow
            f'Re-Initiated ({CURRENCY_LABEL})': '#3498db' # Peter River Blue
        },
        template='plotly_white' # Clean theme for modern look
    )
    fig1.update_layout(xaxis_title=None, legend_title="Status", margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True) # Close custom container

# Visualization 2: Top 10 States by Limit (Plotly Bar)
with col_vis2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True) # New visual enhancement
    st.subheader("💰 Top 10 States by Limit Assigned")
    
    if selected_state == 'All States':
        state_summary = df_filtered.groupby('state')['child_expenditure_limit_assigned'].sum().nlargest(10).reset_index()
        
        # Apply scaling and rename column for Plotly
        state_summary['Limit (Cr)'] = state_summary['child_expenditure_limit_assigned'] / CRORE_FACTOR
        
        fig2 = px.bar(
            state_summary,
            x='Limit (Cr)',
            y='state',
            orientation='h',
            title='Top 10 States by Budget (INR Cr)',
            color='Limit (Cr)', 
            color_continuous_scale=px.colors.sequential.Plasma, # A sleek, modern gradient scale
            labels={'state': 'State'},
            template='plotly_white' # Clean theme for modern look
        )
        fig2.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            margin=dict(t=30, b=0, l=0, r=0),
            coloraxis_showscale=False # Hide color bar for cleaner look
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Top 10 States chart is filtered only when 'All States' is selected.")
    st.markdown('</div>', unsafe_allow_html=True) # Close custom container


# --- Detailed Data Table (Using Expander) ---
st.markdown("---")
st.subheader("📋 Detailed Records")

# Display data frame with scaled monetary columns for consistency (optional, but good practice)
df_display = df_filtered.copy()
for col in numeric_cols:
    df_display[f'{col} ({CURRENCY_LABEL})'] = df_display[col] / CRORE_FACTOR
    df_display = df_display.drop(columns=[col])

# Use st.expander to hide the large table initially
with st.expander("Click here to view the full list of filtered agency records"):
    st.dataframe(df_display, use_container_width=True)
