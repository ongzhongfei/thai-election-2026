import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # For generating district positions

st.set_page_config(page_title="400 Constituency Seats Map", layout="wide")

st.title("🇹🇭 400 Constituency Seat Winners")
st.subheader("Each bubble represents one district, colored by winning party.")

# 1. Load Data
@st.cache_data
def load_election_data():
    sheet_id = "1fm_6pbiXU6jBwHtu13Yuqh_XgQY-AW03"
    province_gid = "858321697"
    partylist_gid = "374730466"
    coordinates_gid = "2069825376"

    def process_sheet(gid, header=1):
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url, header=header)
        non_party_cols = ['Province', 'Region', 'Constituency_ID', 'Province (English)', 'District', "Coordinates"]
        party_cols = [c for c in df.columns if c not in non_party_cols and "Unnamed" not in c]
        for col in party_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['District_Winner'] = df[party_cols].idxmax(axis=1)
        df['Winning_Votes'] = df[party_cols].max(axis=1)
        return df, party_cols

    province_df, _ = process_sheet(province_gid)
    partylist_df, party_cols = process_sheet(partylist_gid)
    province_coordinates_df, _ = process_sheet(coordinates_gid, header=0)
    return province_df, partylist_df, party_cols, province_coordinates_df

province_df, partylist_df, party_cols, province_coordinates_df = load_election_data()

# 2. Prepare Plotting Data
plot_df = province_df.merge(
    province_coordinates_df[['Province (English)', 'Latitude', 'Longitude']], 
    on='Province (English)', 
    how='left'
)

# Jittering to separate districts in the same province
np.random.seed(42)
jitter_scale = 0.12
plot_df['Lat_Jitter'] = plot_df['Latitude'] + np.random.uniform(-jitter_scale, jitter_scale, size=len(plot_df))
plot_df['Lon_Jitter'] = plot_df['Longitude'] + np.random.uniform(-jitter_scale, jitter_scale, size=len(plot_df))

# 3. Define Party Colors
thai_colors = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080"
}

# 4. Layout: Two Columns
col_map, col_info = st.columns([2, 1])

with col_map:
    fig_map = px.scatter_mapbox(
        plot_df,
        lat="Lat_Jitter",
        lon="Lon_Jitter",
        color="District_Winner",
        color_discrete_map=thai_colors,
        hover_name="District",
        hover_data={
            "Province (English)": True,
            "District_Winner": True,
            "Lat_Jitter": False,
            "Lon_Jitter": False
        },
        zoom=5,
        center={"lat": 13.7367, "lon": 100.5231},
        mapbox_style="carto-positron",
        height=700
    )
    fig_map.update_traces(marker=dict(size=12, opacity=0.8))
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # ENABLE INTERACTION
    # Selection mode 'points' allows us to capture which bubble is clicked
    selected_data = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", use_container_width=True)

with col_info:
    # 5. Logic to show District Details
    district_name = None
    
    # Check if a point was clicked
    if selected_data and "selection" in selected_data and selected_data["selection"]["points"]:
        # Get district name from the hovertext/hover_name of the clicked point
        district_name = selected_data["selection"]["points"][0]["hovertext"]
    
    if district_name:
        st.subheader(f"Results: {district_name}")
        
        # Filter data for selected district
        district_row = province_df[province_df['District'] == district_name].iloc[0]
        
        # Get Top 3 Parties
        votes = district_row[party_cols].sort_values(ascending=False).head(3)
        votes_df = pd.DataFrame({'Party': votes.index, 'Votes': votes.values})
        
        # Bar Chart
        fig_bar = px.bar(
            votes_df,
            x='Votes',
            y='Party',
            orientation='h',
            color='Party',
            color_discrete_map=thai_colors,
            text_auto=',.0f'
        )
        fig_bar.update_layout(showlegend=False, xaxis_title="Total Votes", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Show breakdown table
        st.dataframe(votes_df, hide_index=True, use_container_width=True)
    else:
        st.info("Click on a district bubble on the map to see the Top 3 party breakdown.")
        # Optional: Show national top 3 if nothing is selected
        st.caption("Current View: National Summary")
        total_votes = province_df[party_cols].sum().sort_values(ascending=False).head(5)
        st.bar_chart(total_votes)