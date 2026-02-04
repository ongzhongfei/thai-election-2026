import streamlit as st
import pandas as pd
import plotly.express as px
import json

# 1. Load and Cache Data
@st.cache_data
def load_overall_data():
    df = pd.read_excel("Th election Province list.xlsx", skiprows=2)
    # Using your updated column names
    non_party_cols = ['Province', 'Region', 'Constituency_ID', 'Province (English)', 'District']
    party_cols = [c for c in df.columns if c not in non_party_cols]
    
    for col in party_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Determine the winner for each district row
    df['District_Winner'] = df[party_cols].idxmax(axis=1)
    return df, party_cols

df, party_cols = load_overall_data()

# 2. Aggregate Data by Province (English)
# This creates a summary: how many districts each party won per province
province_results = df.groupby(['Province (English)', 'District_Winner']).size().unstack(fill_value=0)

# The "Overall Winner" is the party with the most won districts in that province
province_results['Overall_Winner'] = province_results.idxmax(axis=1)
province_results = province_results.reset_index()

# 3. Create Hover Text (Seat Counts)
def create_hover_text(row):
    # Only include parties that won at least 1 seat
    won_districts = {party: row[party] for party in party_cols if party in row and row[party] > 0}
    # Sort descending so the winner is at the top of the tooltip
    sorted_wins = sorted(won_districts.items(), key=lambda x: x[1], reverse=True)
    return "<br>".join([f"{party}: {int(count)} seats" for party, count in sorted_wins])

province_results['Map_Hover'] = province_results.apply(create_hover_text, axis=1)

# 4. Plotly Choropleth Map
st.title("🗺️ Thailand Election: Province Seat Winners")

with open("thailand-provinces.geojson", encoding='utf-8') as f:
    geojson_data = json.load(f)

thai_colors = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080"
}

# Create the map
fig = px.choropleth(
    province_results,
    geojson=geojson_data,
    locations="Province (English)",
    featureidkey="properties.NAME_1",
    color="Overall_Winner",
    color_discrete_map=thai_colors,
    hover_name="Province (English)",
    hover_data={
        "Overall_Winner": False,
        "Province (English)": False,
        "Map_Hover": True
    }
)

#### Only show thai
fig.update_geos(fitbounds="locations", visible=False)
# A. DISABLE PANNING (Dragging)
# We set dragmode to False so users can't click and move the map
fig.update_layout(
    dragmode=False, 
    margin={"r":0,"t":0,"l":0,"b":0},
    height=750,
    legend_title_text='Dominant Party'
)

# B. DISABLE ZOOMING (Scroll & Buttons)
# We pass a 'config' dictionary to st.plotly_chart to turn off the mouse wheel 
# and hide the zoom buttons in the top-right toolbar.
st.plotly_chart(fig, use_container_width=True, config={
    'scrollZoom': False,              # Disable mouse wheel zoom
    'displayModeBar': True,           # Keep the bar but...
    'modeBarButtonsToRemove': [       # ...remove the zoom/pan tools
        'zoom2d', 'pan2d', 'select2d', 
        'lasso2d', 'zoomIn2d', 'zoomOut2d', 
        'autoScale2d', 'resetScale2d'
    ]
})

st.info("💡 Tip: Hover over any province to see the specific seat breakdown for each party.")