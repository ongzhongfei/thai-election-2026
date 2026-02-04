import streamlit as st
import pandas as pd
import plotly.express as px
import json
import numpy as np

st.set_page_config(page_title="Thailand Population Map", layout="wide")

st.title("🗺️ Thailand Province Population Map")

# Load GeoJSON data for Thailand provinces
@st.cache_data
def load_geojson(filepath="thailand-provinces.geojson"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        return geojson_data
    except FileNotFoundError:
        st.error(f"Error: GeoJSON file '{filepath}' not found. Please ensure it's in the app's root directory.")
        return None

geojson_data = load_geojson()

# 2. Extract Province Names from GeoJSON to ensure a perfect match
# Your GeoJSON uses 'NAME_1' for province names
provinces = [feature['properties']['NAME_1'] for feature in geojson_data['features']]

# 3. Create Dummy Data (Replace this with your real election results later)
df_map = pd.DataFrame({
    "Province": provinces,
    "Random_Metric": np.random.randint(1, 100, size=len(provinces))
})

# 4. Build the Choropleth
st.title("🗺️ Thailand Geographic Data")

fig = px.choropleth(
    df_map,
    geojson=geojson_data,
    locations="Province",          # Column in your DataFrame
    featureidkey="properties.NAME_1", # Path to the name in your GeoJSON
    color="Random_Metric",
    color_continuous_scale="Reds",
    scope="asia",                  # Initial scope
    labels={'Random_Metric': 'Value'}
)

# 5. Adjust the Map View (Zoom to Thailand)
fig.update_geos(
    visible=False, 
    resolution=50,
    showcountries=True, 
    countrycolor="RebeccaPurple",
    fitbounds="locations" # This automatically zooms the map to Thailand
)

fig.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0},
    height=700
)

st.plotly_chart(fig, width="stretch")

# 6. Data Table
st.subheader("Province Data Breakdown")
st.dataframe(df_map, width="stretch")