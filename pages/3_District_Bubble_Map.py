import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np # For generating district positions
import plotly.graph_objects as go

st.set_page_config(page_title="400 Constituency Seats Map", layout="wide")

st.title("🇹🇭 400 Constituency Seat Winners")
st.subheader("Each bubble represents one district, colored by winning party.")

# 1. Load Data
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
        row_max = df[party_cols].max(axis=1)
        row_idxmax = df[party_cols].idxmax(axis=1)

        # Only assign a winner if the max vote is > 0; otherwise, leave blank
        df['District_Winner'] = row_idxmax.where(row_max > 0, "NO INFORMATION YET")
        df['Winning_Votes'] = row_max
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

# Organised layout: arrange districts in a small grid around the province centroid
# This creates deterministic, non-overlapping clusters per province instead of random jitter.
spacing = 0.2 # degrees between points in the province grid
marker_size = 25
# Prepare offset dataframe
offsets = pd.DataFrame(0.0, index=plot_df.index, columns=['dx', 'dy'])

for province, group in plot_df.groupby('Province (English)'):
    n = len(group)
    if n == 1:
        # single district: keep at centroid
        continue
    grid_size = int(np.ceil(np.sqrt(n)))

    # Scale longitude offsets by 1/cos(lat) to approximate equal physical spacing
    centroid_lat = group['Latitude'].mean()
    lat_rad = np.deg2rad(centroid_lat)
    lon_scale = 1.0 / max(np.cos(lat_rad), 0.2)

    # Create grid coordinates: left-to-right, top-to-bottom
    coords_list = []
    for row in reversed(range(grid_size)):
        y = (row - (grid_size - 1) / 2.0) * spacing
        for col in range(grid_size):
            x = (col - (grid_size - 1) / 2.0) * spacing * lon_scale
            coords_list.append([x, y])
    coords = np.array(coords_list)[:n]

    # # Deterministic ordering: use Constituency_ID if present, otherwise sort by District name
    # if 'Constituency_ID' in group.columns:
    #     order_idx = np.argsort(group['Constituency_ID'].astype(str).values)
    # else:
    order_idx = np.argsort(group['District'].astype(int).values)

    ordered_indices = group.index.to_numpy()[order_idx]
    # Assign coordinates in left-to-right, top-to-bottom order to the sorted districts
    offsets.loc[ordered_indices, 'dx'] = coords[:, 0]
    offsets.loc[ordered_indices, 'dy'] = coords[:, 1]

# Apply offsets: dx -> longitude, dy -> latitude
plot_df['Lat_Jitter'] = plot_df['Latitude'] + offsets['dy']
plot_df['Lon_Jitter'] = plot_df['Longitude'] + offsets['dx']

# 3. Define Party Colors
thai_colors = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080", "NO INFORMATION YET": "#808080"
}

# 4. Sidebar: Zoom Control
zoom_level = 6.2

# Adaptive marker and text size based on zoom
marker_size = 15 + (zoom_level - 3) * 2.5  # ranges from 15 to 32.5
text_size = 7 + (zoom_level - 3) * 1  # ranges from 7 to 14

# 4. Layout: Two Columns
col_map, col_info = st.columns([2, 1])
plot_df['District'] =plot_df['District'].astype(str)
with col_map:
    
    fig_map = px.scatter_mapbox(
        plot_df,
        lat="Lat_Jitter",
        lon="Lon_Jitter",
        text="District",
        color="District_Winner",
        color_discrete_map=thai_colors,
        hover_name="Constituency_ID",
        hover_data={
            # "Province (English)": True,
            "District": False,
            "District_Winner": True,
            "Winning_Votes": True,
            "Lat_Jitter": False,
            "Lon_Jitter": False
        },
        zoom=zoom_level,
        center={"lat": 13.7367, "lon": 100.5231},
        mapbox_style="carto-positron",
        height=1000
        )
    fig_map.update_traces(marker=dict(size=marker_size, opacity=0.8), textfont=dict(size=text_size, color='white'), hoverinfo=None)

    # Add a separate text-only trace so labels are displayed centered without altering markers
    # fig_map.add_trace(
    #     go.Scattermapbox(
    #         lat=plot_df['Lat_Jitter'],
    #         lon=plot_df['Lon_Jitter'],
    #         mode='text',
    #         text=plot_df['District'].astype(str),
    #         textposition='middle center',
    #         textfont=dict(size=text_size, color='white'),
    #         hoverinfo='none',
    #         showlegend=False
    #     )
    # )

    # ENABLE INTERACTION
    # Selection mode 'points' allows us to capture which bubble is clicked
    selected_data = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", use_container_width=True, config={"displayModeBar": False})

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
        district_row = province_df[province_df['Constituency_ID'] == str(district_name)].iloc[0]
        
        # Get Top 3 Parties
        votes = district_row[party_cols].sort_values(ascending=False).head(5)
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
        st.plotly_chart(fig_bar, use_container_width=True,)
        
        # Show breakdown table
        st.dataframe(votes_df, hide_index=True, use_container_width=True)
    else:
        st.info("Click on a district bubble on the map to see the Top 3 party breakdown.")
        # Optional: Show national top 3 if nothing is selected
        st.caption("Current View: National Summary")
        total_votes = province_df[party_cols].sum().sort_values(ascending=False).head(5)
        st.bar_chart(total_votes)