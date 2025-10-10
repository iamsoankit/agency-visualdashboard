import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os # For checking environment variables, though API key is handled by platform

# --- Configuration ---
# Google Sheet ID and GID for the specific tab
SHEET_ID = '1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo'
GID = '1933215839' 
DATA_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'

# Define stable, clean column names
CLEAN_COLUMN_NAMES = [
    'sr_no', 'agency_name', 'unique_id', 'state', 'agency_type', 
    'category', 'child_expenditure_limit_assigned', 'success', 
    'pending', 're_initiated', 'balance'
]
numeric_cols = ['child_expenditure_limit_assigned', 'success', 'pending', 're_initiated', 'balance']

# Currency and Scaling
CRORE_FACTOR = 10 
CURRENCY_LABEL = "INR (Cr)" 

# Logos (REPLACE THESE WITH YOUR ACTUAL PUBLIC LOGO LINKS!)
# NOTE: Use stable links (ending in .png, .jpg, or .svg).
LOGO_URL_DST = "https://placehold.co/100x100/003473/ffffff?text=DST+Logo" # Replace this URL
LOGO_URL_MOST = "https://placehold.co/100x100/003473/ffffff?text=MoST+Logo" # Replace this URL

# --- Custom CSS for UI/UX ---
st.markdown("""
<style>
/* Modern Font, Consistent Spacing, and Header */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Subtle Floating Animation for Title */
@keyframes float {
	0% {
		transform: translateY(0px);
	}
	50% {
		transform: translateY(-5px);
	}
	100% {
		transform: translateY(0px);
	}
}
.main-title-container {
    animation: float 3s ease-in-out infinite;
}

/* Card-like Look for Metrics */
div[data-testid="stMetric"] {
    border: 1px solid rgba(0, 0, 0, 0.1); /* Subtle border */
    border-radius: 10px;
    padding: 10px 15px;
    box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.05); /* Soft shadow */
    transition: all 0.2s ease-in-out;
}
div[data-testid="stMetric"]:hover {
    box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.1); /* Shadow on hover */
    transform: translateY(-2px);
}

/* Card-like Look for Charts (Chart Container) */
.chart-container {
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 10px;
    padding: 20px;
    box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    transition: all 0.3s ease-in-out;
}
.chart-container:hover {
    box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.1);
}

/* Sidebar Title and Info Box Styling */
.sidebar .sidebar-content {
    padding-top: 1rem;
}
h2 {
    font-weight: 700 !important;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


# --- API Call Functions ---

# Function to call the Gemini API for financial summary
async def generate_summary(prompt):
    # API key is automatically provided by the Canvas runtime
    api_key = "" 
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    # System prompt to define the model's persona
    system_prompt = "You are a senior financial analyst and expert in government expenditure. Provide a concise, professional, single-paragraph summary of the financial performance metrics provided. Focus on utilization (Success Rate, Balance, Re-Initiated amount) and overall health. Use a formal and analytical tone."

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "tools": [{"google_search": {}}], # Use Google Search for grounding general knowledge
    }

    # Implement exponential backoff for robustness
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                api_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Analysis unavailable.')
            return text
            
        except requests.exceptions.HTTPError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                st.warning(f"API request failed with status {response.status_code}. Retrying in {wait_time}s...")
                import time
                time.sleep(wait_time)
            else:
                return f"Error: Failed to connect to AI service after {max_retries} attempts ({e})"
        except Exception as e:
            return f"An unexpected error occurred during AI call: {e}"
    return "Analysis failed due to unknown error."


# --- Function to load data safely and efficiently ---
@st.cache_data(ttl=60) 
def load_data(url):
    try:
        df = pd.read_csv(
            url, 
            header=None, 
            names=CLEAN_COLUMN_NAMES, 
            skiprows=1 
        )
        
        if len(df.columns) != len(CLEAN_COLUMN_NAMES) or df.empty:
            raise ValueError("Data structure mismatch or empty sheet.")

        # Data Cleaning and Type Conversion
        for col in numeric_cols:
            df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)  

        st.sidebar.success("Data loaded successfully from Google Sheet URL (Refreshed every 60s).")
        return df

    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e) or "403" in str(e):
            st.error("Failed to fetch data: Unauthorized Error. Ensure the Google Sheet is 'Anyone with the link'.")
        else:
            st.error(f"Failed to fetch data from Google Sheet URL. Error: {e}")
        return pd.DataFrame()


# --- Load Data and Handle Failure ---
df = load_data(DATA_URL)

if df.empty:
    st.stop() 


# --- Page Configuration and Header ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Agency Expenditure Dashboard")

# 1. Header with Logos and Title
col_logo_left, col_title, col_logo_right = st.columns([1, 4, 1])

with col_logo_left:
    st.image(LOGO_URL_DST, width=100) # DST Logo Placeholder

with col_title:
    st.markdown(f'<div class="main-title-container" style="text-align: center;"><h1>{st.session_state.get("page_title", "💸 Agency Expenditure Dashboard")}</h1></div>', unsafe_allow_html=True)

with col_logo_right:
    st.image(LOGO_URL_MOST, width=100) # MoST Logo Placeholder

st.divider()


# --- Sidebar Filters ---
st.sidebar.markdown("## **🔍 Filter Data**")

# --- Start Cascading Filters ---
# 1. State Selection (Always independent)
selected_state = st.sidebar.selectbox(
    "Select State:",
    options=['All States'] + sorted(df['state'].astype(str).str.upper().unique().tolist())
)

# Filtering based on selected state
df_temp = df.copy()
if selected_state != 'All States':
    df_temp = df_temp[df_temp['state'].astype(str).str.upper() == selected_state]

# 2. Category Selection (Depends on State)
selected_category = st.sidebar.selectbox(
    "Select Category:",
    options=['All Categories'] + sorted(df_temp['category'].astype(str).unique().tolist())
)

# Filtering based on selected category
df_temp = df_temp.copy()
if selected_category != 'All Categories':
    df_temp = df_temp[df_temp['category'] == selected_category]

# 3. Agency Name Selection (Depends on State and Category)
selected_agency = st.sidebar.selectbox(
    "Select Agency Name:",
    options=['All Agencies'] + sorted(df_temp['agency_name'].astype(str).unique().tolist())
)

# Filtering based on selected agency
df_temp = df_temp.copy()
if selected_agency != 'All Agencies':
    df_temp = df_temp[df_temp['agency_name'] == selected_agency]

# 4. Unique ID Selection (Depends on State, Category, and Agency Name)
selected_unique_id = st.sidebar.selectbox(
    "Agency Unique Code:",
    options=['All Codes'] + sorted(df_temp['unique_id'].astype(str).unique().tolist())
)
# --- End Cascading Filters ---

# Final Filter Application
df_filtered = df.copy()
if selected_state != 'All States':
    df_filtered = df_filtered[df_filtered['state'].astype(str).str.upper() == selected_state]
if selected_category != 'All Categories':
    df_filtered = df_filtered[df_filtered['category'] == selected_category]
if selected_agency != 'All Agencies':
    df_filtered = df_filtered[df_filtered['agency_name'] == selected_agency]
if selected_unique_id != 'All Codes':
    df_filtered = df_filtered[df_filtered['unique_id'] == selected_unique_id]


# --- 2. Calculate KPIs on Filtered Data ---
total_limit = df_filtered['child_expenditure_limit_assigned'].sum()
total_success = df_filtered['success'].sum()
total_pending = df_filtered['pending'].sum()
total_reinitiated = df_filtered['re_initiated'].sum()
total_balance = df_filtered['balance'].sum()
success_rate = (total_success / total_limit) * 100 if total_limit != 0 else 0

# Scale the KPIs to Crores
limit_cr = total_limit / CRORE_FACTOR
success_cr = total_success / CRORE_FACTOR
pending_cr = total_pending / CRORE_FACTOR
reinitiated_cr = total_reinitiated / CRORE_FACTOR
balance_cr = total_balance / CRORE_FACTOR

# Determine status for metric display
def get_status_description(rate):
    if rate > 80:
        return "Excellent"
    elif rate > 50:
        return "Good"
    elif rate < 30 and rate > 0:
        return "Needs Review"
    elif rate == 0 and total_limit > 0:
        return "Zero Utilization"
    else:
        return "Moderate"

status = get_status_description(success_rate)
success_rate_delta = f"{status} ({success_rate:,.2f}%)"


# --- Display Filter Summary ---
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
    **Current Scope:** | **State(s):** `{display_states}` | **Category:** `{selected_category}` | **Agency:** `{selected_agency}` | **Code:** `{selected_unique_id}`
""")
st.markdown("---")


# --- KPI Header (6 Metrics) ---
col1, col2, col3, col4, col5, col6 = st.columns(6) 

col1.metric(f"Total Budget Assigned ({CURRENCY_LABEL})", f"₹{limit_cr:,.2f}")
col2.metric(f"Total Success ({CURRENCY_LABEL})", f"₹{success_cr:,.2f}")
col3.metric("Success Rate", success_rate_delta, delta_color="normal")
col4.metric(f"Total Pending ({CURRENCY_LABEL})", f"₹{pending_cr:,.2f}")
col5.metric(f"Total Re-Initiated ({CURRENCY_LABEL})", f"₹{reinitiated_cr:,.2f}")
col6.metric(f"Total Balance ({CURRENCY_LABEL})", f"₹{balance_cr:,.2f}", delta_color="inverse") # Inverse color for large balance


# --- AI Summary Toolbar ---
st.markdown("<hr style='border: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
st.subheader("🤖 AI Financial Analysis Summary")

if 'summary_text' not in st.session_state:
    st.session_state.summary_text = "Click the button below to generate an AI-powered analysis of the displayed financial metrics."

col_ai_button, col_ai_display = st.columns([1, 4])

with col_ai_button:
    if st.button("✨ Generate Performance Analysis", key="ai_summary_button"):
        
        # Construct the detailed prompt for the AI
        prompt_data = f"""
        Analyze the following financial metrics (values are in Crores INR) for the current filtered scope:
        - Scope Filtered: State(s): {display_states}, Category: {selected_category}, Agency: {selected_agency}
        - Total Budget Assigned: ₹{limit_cr:,.2f} Cr
        - Total Successful Expenditure: ₹{success_cr:,.2f} Cr
        - Success Rate (Utilization): {success_rate:,.2f}%
        - Total Pending Expenditure: ₹{pending_cr:,.2f} Cr
        - Total Re-Initiated Expenditure: ₹{reinitiated_cr:,.2f} Cr
        - Total Balance Remaining: ₹{balance_cr:,.2f} Cr

        Provide a concise, single-paragraph financial analysis summarizing the utilization and overall health.
        """
        # Call the asynchronous function in a Streamlit context
        with st.spinner('Generating analysis, please wait...'):
            st.session_state.summary_text = generate_summary(prompt_data)

with col_ai_display:
    st.markdown(f"""
    <div style="border: 1px solid #dcdcdc; padding: 15px; border-radius: 8px; background-color: #f9f9f9;">
        {st.session_state.summary_text}
    </div>
    """, unsafe_allow_html=True)


# --- Visualizations (Modern Card Layout) ---
st.markdown("---")
col_vis1, col_vis2 = st.columns(2)

# Visualization 1: Expenditure Status by Category
with col_vis1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📊 Expenditure Breakdown by Category Status")
    
    category_summary = df_filtered.groupby('category')[['success', 'pending', 're_initiated']].sum().reset_index()
    category_summary_cr = category_summary.copy()
    
    # Scale and rename columns for Plotly
    for col in ['success', 'pending', 're_initiated']:
        category_summary_cr[col] = category_summary_cr[col] / CRORE_FACTOR
        
    fig1 = px.bar(
        category_summary_cr,
        x='category',
        y=['success', 'pending', 're_initiated'],
        title="Success vs. Pending vs. Re-Initiated",
        labels={'value': f'Amount ({CURRENCY_LABEL})', 'category': 'Agency Category', 'variable': 'Status'},
        template="plotly_white", # Clean theme
        color_discrete_map={'success': 'green', 'pending': 'orange', 're_initiated': 'blue'}
    )
    fig1.update_layout(height=450, xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# Visualization 2: Top 10 States by Limit
with col_vis2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🗺️ Top 10 States by Limit Assigned")
    
    if selected_state == 'All States':
        state_summary = df_filtered.groupby('state')['child_expenditure_limit_assigned'].sum().nlargest(10).reset_index()
        state_summary['child_expenditure_limit_assigned'] = state_summary['child_expenditure_limit_assigned'] / CRORE_FACTOR
        
        fig2 = px.bar(
            state_summary,
            y='state', # Use Y-axis for states (Horizontal bar chart)
            x='child_expenditure_limit_assigned',
            orientation='h',
            title=f"Top 10 States by Limit ({CURRENCY_LABEL})",
            labels={'child_expenditure_limit_assigned': f'Total Limit ({CURRENCY_LABEL})', 'state': 'State'},
            template="plotly_white",
            color='child_expenditure_limit_assigned',
            color_continuous_scale=px.colors.sequential.Plasma 
        )
        fig2.update_layout(height=450, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("The Top 10 States chart is active only when the 'All States' filter is selected. View the Detailed Data Table for current state breakdown.")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- Detailed Data Table (Collapsible) ---
st.markdown("---")
with st.expander("📋 Click to View Detailed Raw Data (Filtered)", expanded=False):
    st.subheader("Filtered Agency Data (All amounts in INR Crores)")
    
    # Display data frame with scaled monetary columns for consistency
    df_display = df_filtered.copy()
    for col in numeric_cols:
        df_display[f'{col.replace("_", " ").title()} ({CURRENCY_LABEL})'] = df_display[col] / CRORE_FACTOR
        df_display = df_display.drop(columns=[col])

    # Remove internal Sr. No. column for display clarity
    if 'sr_no' in df_display.columns:
        df_display = df_display.drop(columns=['sr_no'])
        
    st.dataframe(df_display, use_container_width=True)
