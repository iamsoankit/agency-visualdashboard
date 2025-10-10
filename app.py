<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Name ❀ Product Design</title>
    <link rel="stylesheet" href="style.css">
    </head>
<body>

    <header class="navbar">
        <div class="logo">Your Name ❀ Product Design</div>
    </header>

    <section id="hero" class="hero-section">
        <div class="intro-text">
            <h1>hey, i am a product designer based out of [Your City, Country].</h1>
            <p class="pronunciation">[ import streamlit as st

import pandas as pd

import os

import requests # Need this for fetching data from a URL



# --- Configuration ---

# Google Sheet ID extracted from your URL: 

# https://docs.google.com/spreadsheets/d/1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo/edit?gid=1933215839#gid=1933215839

SHEET_ID = '1cRXv_5qkGmfYtrRcXRqDrRnZKnBzoabf95yb9zh5Koo'

# The gid (internal sheet ID) is for the specific sheet tab within the file (MAIN DATA 07.10.25)

GID = '1933215839' 



# Construct the public CSV export URL for the specific sheet tab

DATA_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'



# Define the expected, clean column names (based on the provided spreadsheet structure)

CLEAN_COLUMN_NAMES = [

    'sr_no', 'agency_name', 'unique_id', 'state', 'agency_type', 

    'category', 'child_expenditure_limit_assigned', 'success', 

    'pending', 're_initiated', 'balance'

]



# Function to load data safely and efficiently

@st.cache_data(ttl=60) # Cache for 60 seconds to enable "real-time" feel

def load_data(url):

    """

    Loads data directly from the public Google Sheet CSV export URL.

    This is the most reliable method for live data access in Streamlit.

    """

    try:

        # Use pandas read_csv directly on the URL

        df = pd.read_csv(

            url, 

            header=None, # Skip the default header row

            names=CLEAN_COLUMN_NAMES, # Assign clean column names

            skiprows=1 # Skip the actual header row from the sheet

        )

        

        # Basic check to ensure a valid dataset was returned

        if len(df.columns) != len(CLEAN_COLUMN_NAMES) or df.empty:

            st.error("Data loading failed. Please ensure the Google Sheet link is public, the GID is correct, and the sheet contains data.")

            return pd.DataFrame()



        st.success("Data loaded successfully from Google Sheet URL.")

        return df



    except Exception as e:

        # Handling for unauthorized access (401) and general errors

        if "401" in str(e) or "Unauthorized" in str(e) or "403" in str(e):

            st.error(

                "Failed to fetch data: Unauthorized Error.\n\n"

                "Please ensure the Google Sheet is set to 'Anyone with the link' (Viewer access) "

                "in its sharing settings."

            )

        else:

            st.error(f"Failed to fetch data from Google Sheet URL. Please check your URL and network connection. Error: {e}")

        return pd.DataFrame()



# --- Load Data and Handle Failure ---

df = load_data(DATA_URL)



if df.empty:

    st.stop() # Stop the script if data failed to load



# The column names are now guaranteed to be clean.

numeric_cols = ['child_expenditure_limit_assigned', 'success', 'pending', 're_initiated', 'balance']



# Ensure numeric columns are actually numeric after loading

for col in numeric_cols:

    # IMPORTANT: The str.replace(r'[^\d.]', '', regex=True) line cleans out

    # foreign characters, commas (if used as thousand separators), and non-numeric

    # symbols, retaining only digits and periods (decimals). This is crucial for non-English locales.

    df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)

    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) 



# --- Sidebar Filters ---

st.sidebar.header("Filter Data")



# --- Start Cascading Filters ---

# 1. State Selection (Always independent)

selected_state = st.sidebar.selectbox(

    "Select State:",

    options=['All States'] + sorted(df['state'].astype(str).str.upper().unique().tolist())

)



# DataFrame filtered by State

df_for_category_selection = df.copy()

if selected_state != 'All States':

    df_for_category_selection = df_for_category_selection[df_for_category_selection['state'].astype(str).str.upper() == selected_state]



# 2. Category Selection (Depends on State)

selected_category = st.sidebar.selectbox(

    "Select Category:",

    options=['All Categories'] + sorted(df_for_category_selection['category'].astype(str).unique().tolist())

)



# DataFrame filtered by State and Category

df_for_agency_selection = df_for_category_selection.copy()

if selected_category != 'All Categories':

    df_for_agency_selection = df_for_agency_selection[df_for_agency_selection['category'] == selected_category]



# 3. Agency Name Selection (Depends on State and Category)

selected_agency = st.sidebar.selectbox(

    "Select Agency Name:",

    options=['All Agencies'] + sorted(df_for_agency_selection['agency_name'].astype(str).unique().tolist())

)



# DataFrame filtered by State, Category, and Agency Name

df_for_unique_code_selection = df_for_agency_selection.copy()

if selected_agency != 'All Agencies':

    df_for_unique_code_selection = df_for_unique_code_selection[df_for_unique_code_selection['agency_name'] == selected_agency]



# 4. Unique ID Selection (Depends on State, Category, and Agency Name)

selected_unique_id = st.sidebar.selectbox(

    "Agency Unique Code:",

    options=['All Codes'] + sorted(df_for_unique_code_selection['unique_id'].astype(str).unique().tolist())

)

# --- End Cascading Filters ---





# Apply Filters (This block now ensures all 4 selections filter the data,

# but the available options in 2, 3, and 4 are constrained by earlier selections.)

df_filtered = df.copy()



if selected_state != 'All States':

    df_filtered = df_filtered[df_filtered['state'].astype(str).str.upper() == selected_state]



if selected_category != 'All Categories':

    df_filtered = df_filtered[df_filtered['category'] == selected_category]



if selected_agency != 'All Agencies':

    df_filtered = df_filtered[df_filtered['agency_name'] == selected_agency]



if selected_unique_id != 'All Codes':

    df_filtered = df_filtered[df_filtered['unique_id'] == selected_unique_id]



# Add instruction for theme switching in the sidebar (NEW)

st.sidebar.info("To switch between Light and Dark mode, use the 'Settings' option in the main menu (☰) at the top right of the page.")



# --- 2. Calculate KPIs on Filtered Data ---

total_limit = df_filtered['child_expenditure_limit_assigned'].sum()

total_success = df_filtered['success'].sum()

total_pending = df_filtered['pending'].sum()

total_reinitiated = df_filtered['re_initiated'].sum() # NEW CALCULATION

total_balance = df_filtered['balance'].sum()



# Safe calculation for success rate

success_rate = (total_success / total_limit) * 100 if total_limit != 0 else 0





# --- 3. Dashboard Layout ---

# Removed confusing theme comments, relying on native Streamlit theme selection

st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Agency Dashboard")

st.title("💰 Agency Expenditure Dashboard (Live Data)")



# Get the list of unique states in the filtered data for display

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

    

# Updated Markdown to show the State name(s) clearly

st.markdown(f"""

    **Data displayed for:** | **State(s):** **{display_states}** | **Category:** **{selected_category}** | **Agency:** **{selected_agency}** | **Code:** **{selected_unique_id}** | *Auto-refreshes every 60 seconds.*

""")

st.divider()



# --- SCALING AND CURRENCY ---

# To display amounts in Crores (Cr), we divide the sums by 10.

CRORE_FACTOR = 10 

CURRENCY_LABEL = "INR (Cr)" 



# Scale the KPIs to Crores

limit_cr = total_limit / CRORE_FACTOR

success_cr = total_success / CRORE_FACTOR

pending_cr = total_pending / CRORE_FACTOR

reinitiated_cr = total_reinitiated / CRORE_FACTOR

balance_cr = total_balance / CRORE_FACTOR





# KPI Header - Now using 6 columns (Total Limit, Success, Success Rate, Pending, Re-Initiated, Balance)

col1, col2, col3, col4, col5, col6 = st.columns(6) 



# Metrics: Total Limit, Total Success, Success Rate, Total Pending, Total Re-Initiated, Total Balance



col1.metric(f"Total Budget Assigned ({CURRENCY_LABEL})", f"₹{limit_cr:,.2f}")

col2.metric(f"Total Success ({CURRENCY_LABEL})", f"₹{success_cr:,.2f}", delta_color="normal")

col3.metric("Success Rate", f"{success_rate:,.2f}%", delta_color="inverse")

col4.metric(f"Total Pending ({CURRENCY_LABEL})", f"₹{pending_cr:,.2f}")

col5.metric(f"Total Re-Initiated ({CURRENCY_LABEL})", f"₹{reinitiated_cr:,.2f}")

col6.metric(f"Total Balance ({CURRENCY_LABEL})", f"₹{balance_cr:,.2f}")





# --- Main Visualizations ---



col_vis1, col_vis2 = st.columns(2)



# Visualization 1: Expenditure Status by Category

with col_vis1:

    st.subheader("📊 Expenditure Breakdown by Category Status")

    # Group and ensure no NaN columns before sum

    category_summary = df_filtered.groupby('category')[['success', 'pending', 're_initiated']].sum()

    # Apply scaling for the chart data

    category_summary_cr = category_summary / CRORE_FACTOR

    category_summary_cr.columns = [f'Success ({CURRENCY_LABEL})', f'Pending ({CURRENCY_LABEL})', f'Re-Initiated ({CURRENCY_LABEL})']

    st.bar_chart(category_summary_cr)



# Visualization 2: Top 10 States by Limit

with col_vis2:

    st.subheader("🗺️ Top 10 States by Limit Assigned")

    

    # Check if a state filter is applied before showing Top 10 states

    if selected_state == 'All States':

        state_summary = df_filtered.groupby('state')['child_expenditure_limit_assigned'].sum().nlargest(10).reset_index()

        # Apply scaling for the chart data

        state_summary['child_expenditure_limit_assigned'] = state_summary['child_expenditure_limit_assigned'] / CRORE_FACTOR

        state_summary = state_summary.set_index('state')

        st.bar_chart(state_summary, y='child_expenditure_limit_assigned') # Explicitly use the scaled column

    else:

        st.info("Top 10 States chart is only available when 'All States' filter is selected.")





# --- Detailed Data Table ---

st.divider()

st.subheader("📋 Raw Data View")

# Display data frame with scaled monetary columns for consistency (optional, but good practice)

df_display = df_filtered.copy()

for col in numeric_cols:

    df_display[f'{col} ({CURRENCY_LABEL})'] = df_display[col] / CRORE_FACTOR

    df_display = df_display.drop(columns=[col])



st.dataframe(df_display)Your Name spelled phonetically ]</p>
            <p>So I call this space my **“designverse”** where I geek on cool ideas - let me take you on a tour of it.</p>
        </div>
        
        <div class="cheesecake-dialogue">
            <p>wanna go on a cheesecake run? 🍰</p>
            <a href="#" class="dialogue-button">You read my mind! Let's go 🏃‍♂️.</a>
        </div>

        <div class="to-do-list-container">
            <h3>to-do list for next one week</h3>
            <ul>
                <li><span>✅</span> portfolio polish</li>
                <li><span>◻️</span> start a journal</li>
                <li><span>✅</span> go for a run</li>
                <li><span>◻️</span> drink water (more!)</li>
                <li><span>✅</span> write down my ideas</li>
            </ul>
        </div>
    </section>

    <section id="work" class="work-section">
        <h2>Now let's come to the point and let me show you around what I have worked on.</h2>

        <article class="project-card large-card">
            <div class="tag-row">
                <span class="tag">B2B</span>
                <span class="tag">Product Thinking</span>
                <span class="tag">2024</span>
            </div>
            <img src="project-1-main-visual.jpg" alt="Project 1 Mockup" class="project-image">
            <div class="project-content">
                <h3>Redefining Dashboards for Indian Fintech</h3>
                <p>At [Company Name], I worked on core dashboard modules. The goal was to make merchants self-sufficient and minimize support tickets.</p>
                <a href="project-1-full-case-study.html" class="case-study-link">View Full Case Study →</a>
            </div>
        </article>

        <article class="project-card large-card">
            <div class="tag-row">
                <span class="tag">Design System</span>
                <span class="tag">Mobile Design</span>
                <span class="tag">2023</span>
            </div>
            <img src="project-2-visual.jpg" alt="Project 2 Mockup" class="project-image">
            <div class="project-content">
                <h3>From Chaos to Cohesion: Crafting the [Product] Design System</h3>
                <p>I helped build their design system, focusing on scalability and speed for a YC-backed startup.</p>
                <a href="project-2-full-case-study.html" class="case-study-link">View Full Case Study →</a>
            </div>
        </article>
        
        <h3 class="minor-projects-heading">Take a breath. Next are some of the projects I worked on as assignments & on weekends.</h3>
        
        <div class="projects-grid">
            <article class="project-card small-card">
                <img src="project-3-visual.jpg" alt="Project 3 Mockup">
                <h4>Journey Beyond Borders: An Odyssey Travel App</h4>
                <div class="tag-row">
                    <span class="tag">B2C</span><span class="tag">Research</span>
                </div>
            </article>

            <article class="project-card small-card">
                <img src="project-4-visual.jpg" alt="Project 4 Mockup">
                <h4>BidNetwork: An E-Auction Platform</h4>
                <div class="tag-row">
                    <span class="tag">Procurement Tech</span><span class="tag">Mobile</span>
                </div>
            </article>

            <article class="project-card small-card">
                <img src="project-5-visual.jpg" alt="Project 5 Mockup">
                <h4>Book Launch Event Visual Branding</h4>
                <div class="tag-row">
                    <span class="tag">Visual</span><span class="tag">Branding</span>
                </div>
            </article>
        </div>

    </section>

    <footer id="contact" class="footer-section">
        <h2>Let's talk.</h2>
        <p class="cta-message">Ready to collaborate? Let's juggle between user flows, research and visuals. Shoot me a message and let's have a chat over coffee!</p>
        
        <div class="skills-and-contact">
            <div class="skills-list-block">
                <h3>Key Skills</h3>
                <ul>
                    <li>UI/UX Design</li>
                    <li>Product Strategy</li>
                    <li>Design System</li>
                    <li>UX Research</li>
                </ul>
            </div>
            
            <div class="contact-block">
                <h3>Connect</h3>
                <div class="contact-links">
                    <a href="mailto:your.email@gmail.com">your.email@gmail.com</a>
                    <a href="https://linkedin.com/in/yourprofile" target="_blank">LinkedIn</a>
                    <a href="https://instagram.com/yourprofile" target="_blank">Instagram</a>
                    <a href="https://cal.com/yourprofile" target="_blank">Cal.com</a>
                </div>
            </div>
        </div>
        <p class="goodbye">ok bye, need to respond to my mails. 👋</p>
    </footer>

</body>
</html>
