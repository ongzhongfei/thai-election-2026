import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection


st.set_page_config(page_title="Thailand Election 2026 Dashboard", layout="wide")


# sheet_id = "1fm_6pbiXU6jBwHtu13Yuqh_XgQY-AW03"
# gid = "858321697"
# url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# # 2. Read the CSV
# # This will likely put the English labels as headers and the Thai labels as Row 0
# df = pd.read_csv(url,header=1)

# # 3. Drop the first row (the Thai labels) to clean the data
# df = df.iloc[0:].reset_index(drop=True)

# # 4. Clean up column names 
# # (Google often adds .1, .2 to duplicate column names; this cleans them)
# df.columns = [col.split('.')[0] for col in df.columns]

# st.subheader("Cleaned Province Data")
# st.dataframe(df, use_container_width=True)

# 1. Load the Excel File
@st.cache_data
def load_excel_data():
    # Use 'openpyxl' engine for Excel files
    # df = pd.read_excel("Th election Province list.xlsx", skiprows=2)
    sheet_id = "1fm_6pbiXU6jBwHtu13Yuqh_XgQY-AW03"
    gid = "858321697"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    # 2. Read the CSV
    # This will likely put the English labels as headers and the Thai labels as Row 0
    df = pd.read_csv(url,header=1)

    # 3. Drop the first row (the Thai labels) to clean the data
    # df = df.iloc[0:].reset_index(drop=True)
    # Identify party columns (everything except Province/Region)
    non_party_cols = ['Province', 'Region','Constituency_ID','Province (English)','District']
    party_cols = [c for c in df.columns if c not in non_party_cols]
    
    # Force numeric to avoid the "Equal Pie Chart" bug
    for col in party_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Determine the winner for each district row
    df['District_Winner'] = df[party_cols].idxmax(axis=1)
    # 2. Process Winner for Each Province
    # Determine winner by finding the column with the maximum value in each row
    df['Winner'] = df[party_cols].idxmax(axis=1)
    df['Winning_Votes'] = df[party_cols].max(axis=1)
    
    return df, party_cols

df, party_cols = load_excel_data()


# 3. Sidebar Filters
st.sidebar.header("Filters")
selected_region = st.sidebar.multiselect("Select Region", options=df['Region'].unique(), default=df['Region'].unique())
filtered_df = df[df['Region'].isin(selected_region)]

# 4. Top Level Metrics
st.title("🗳️ Thailand Election Tracker")
seat_counts = filtered_df['Winner'].value_counts().reset_index()
seat_counts.columns = ['Party', 'Seats']

# Define Party Colors
color_map = {
    "People's Party": "#FF6600", "Pheu Thai": "#DF0000", 
    "Bhumjaithai": "#00008B", "Democrat": "#00BFFF", 
    "Economic Party": "#DAF759", "Klatam": "#065A1F",
    "Others": "#808080"
}
color_map = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080"
    }
# Display Metrics
cols = st.columns(len(seat_counts))
for i, row in seat_counts.iterrows():
    cols[i].metric(row['Party'], f"{row['Seats']} Seats")

# 5. Charts
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Election Seat Control Share")
    # Using 'Seats' as the numeric value ensures proportional slices
    fig_pie = px.pie(seat_counts, values="Seats", names="Party", 
                     color="Party", color_discrete_map=color_map, hole=0.4)
    st.plotly_chart(fig_pie, width='stretch')

with col_right:
    st.subheader("Regional Breakdown")
    fig_bar = px.histogram(filtered_df, x="Region", color="Winner", 
                           barmode="group", color_discrete_map=color_map)
    st.plotly_chart(fig_bar, width='stretch')

# 6. Data Explorer
st.subheader("Detailed Results")
st.dataframe(filtered_df, width='stretch')