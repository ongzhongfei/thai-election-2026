import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # For generating district positions

st.set_page_config(page_title="400 Constituency Seats Map", layout="wide")

st.title("🇹🇭 400 Constituency Seat Winners")
st.subheader("Each bubble represents one district, colored by winning party.")

# 1. Load Data
@st.cache_data
def load_district_data():
    df = pd.read_excel("Th election Province list.xlsx", skiprows=2)
    non_party_cols = ['Province', 'Region', 'Constituency_ID', 'Province (English)', 'District']
    party_cols = [c for c in df.columns if c not in non_party_cols]
    
    for col in party_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['District_Winner'] = df[party_cols].idxmax(axis=1)
    
    # We need a unique identifier for each district
    df['District_Full_Name'] = df['District'] + " (" + df['Province (English)'] + ")"
    return df, party_cols

df_districts, party_cols = load_district_data()

# 2. Define Party Colors
thai_colors = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080" # Ensure 'Others' is handled if it appears
}

# 3. Assign Approximate X, Y Coordinates for Each District
# This is a simplified "manual" mapping for visualization purposes,
# as precise district coordinates are not in your data.
# We'll use regions and an internal counter to place them on a grid.

# Start with a base X, Y for each region, then distribute districts within that region
region_coords = {
    'Northern': (10, 80),
    'Northeastern': (50, 70),
    'Central': (30, 40),
    'Eastern': (60, 30),
    'Western': (10, 30),
    'Southern': (30, 10),
    'Bangkok': (40, 50) # Assuming Bangkok is within Central, but slightly offset
}

# Create a temporary dataframe to assign coordinates
plot_df = df_districts.copy()
plot_df['x_coord'] = 0.0
plot_df['y_coord'] = 0.0

# Counters for distributing districts within regions
region_x_offset = {}
region_y_offset = {}

# Assign coordinates
for index, row in plot_df.iterrows():
    region = row['Region']
    base_x, base_y = region_coords.get(region, (0, 0)) # Default if region not found

    if region not in region_x_offset:
        region_x_offset[region] = 0
        region_y_offset[region] = 0

    # Distribute districts in a small grid within the region's base coordinate
    plot_df.loc[index, 'x_coord'] = base_x + (region_x_offset[region] % 10) * 1.5
    plot_df.loc[index, 'y_coord'] = base_y - (region_y_offset[region] // 10) * 1.5
    
    region_x_offset[region] += 1
    if region_x_offset[region] % 10 == 0: # Move to next 'row' every 10 districts
        region_y_offset[region] += 1

# 4. Create the Scatter Plot (Bubble Map)
fig = px.scatter(
    plot_df,
    x="x_coord",
    y="y_coord",
    color="District_Winner",
    color_discrete_map=thai_colors,
    hover_name="District_Full_Name",
    hover_data={
        "District_Winner": True,
        "Province (English)": True,
        "Region": True,
        "x_coord": False, # Hide raw coordinates in hover
        "y_coord": False
    },
    title="Thailand 400 Constituency Winners"
)

# 5. Customize Layout for Map-like Appearance
fig.update_traces(marker=dict(size=15, line=dict(width=1, color='DarkSlateGrey')))
fig.update_layout(
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1), # Keep aspect ratio
    plot_bgcolor="rgba(0,0,0,0)", # Transparent background
    margin=dict(l=20, r=20, t=50, b=20),
    height=800,
    showlegend=True,
    dragmode=False # Disable panning
)

# 6. Disable Zooming
st.plotly_chart(fig, use_container_width=True, config={
    'scrollZoom': False,
    'displayModeBar': True,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'
    ]
})

st.info("💡 Each bubble is a single constituency. Hover for details.")