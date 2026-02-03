import streamlit as st
import pandas as pd
import math
import plotly.express as px

st.set_page_config(page_title="Total 500 Seats", layout="wide")

# 1. Load Data
df = pd.read_excel("Th election Province list.xlsx", skiprows=2)

# 2. Identify and Clean Party Columns
party_cols = [c for c in df.columns if c not in ['Province', 'Region','Constituency_ID','District (English)','District']]

# --- THE FIX ---
for col in party_cols:
    # errors='coerce' turns non-numbers into NaN, then we fill them with 0
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
# ---------------

# 3. Calculate Constituency Seats (400)
# Now idxmax will work because all values are floats/ints
constituency_winners = df[party_cols].idxmax(axis=1).value_counts()

# 3. Calculate Party-List Seats (100)
total_party_votes = df[party_cols].sum()
national_total = total_party_votes.sum()
quota = national_total / 100

# Calculate seats and remainders
pl_seats = (total_party_votes / quota).apply(lambda x: int(x))
remainders = (total_party_votes / quota) % 1

# If total PL seats < 100, give extra to highest remainders
extra_seats = 100 - pl_seats.sum()
top_remainders = remainders.nlargest(int(extra_seats)).index
for party in top_remainders:
    pl_seats[party] += 1

# 4. Combine Results
summary = pd.DataFrame({
    "Constituency": constituency_winners,
    "Party-List": pl_seats
}).fillna(0).astype(int)

summary["Total Seats"] = summary["Constituency"] + summary["Party-List"]

# 5. Display
st.title("🏛️ Total Parliament (500 Seats)")
st.table(summary.sort_values("Total Seats", ascending=False))

# 6. Progress Bar Fix
# We calculate the progress based on the fixed target of 500
total_allocated = summary["Total Seats"].sum()

# If logic errors pushed it to 501 or 502, we cap it at 1.0 for the UI
display_progress = min(total_allocated / 500, 1.0)

st.write(f"Total Seats Allocated: {total_allocated} / 500")
st.progress(display_progress)

if total_allocated > 500:
    st.warning(f"⚠️ Warning: Seat allocation ({total_allocated}) exceeds 500. Please check for duplicate Province entries in your Excel.")


#########################################################
#### Bubble Chart for Parliamentary Seating Layout ####
def get_parliament_coords(seat_counts, rows=8, radius=5):
    """Calculates x, y coordinates for a semi-circle parliament layout."""
    data = []
    total_seats = sum(seat_counts.values())
    
    # Sort parties so they sit together in chunks
    sorted_parties = sorted(seat_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Flat list of party names for every single seat
    all_seats = []
    for party, count in sorted_parties:
        all_seats.extend([party] * count)
        
    # Calculate coordinates in a semi-circle (180 degrees)
    for i in range(total_seats):
        # Determine which "row" and "angle" the seat belongs to
        row = i % rows
        angle = math.pi * (i / total_seats) # Distributed from 0 to 180 degrees
        
        # Polar to Cartesian conversion
        r = radius + row
        x = r * math.cos(math.pi - angle)
        y = r * math.sin(math.pi - angle)
        
        data.append({"x": x, "y": y, "Party": all_seats[i]})
        
    return pd.DataFrame(data)

# Create the coordinates based on your 'summary' dataframe
seat_dict = summary["Total Seats"].to_dict()
coords_df = get_parliament_coords(seat_dict)

st.subheader("Parliamentary Seating Layout")

# Define your color map again to ensure consistency
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
fig_parliament = px.scatter(
    coords_df, x="x", y="y", color="Party",
    color_discrete_map=color_map,
    title="500 Seats Distribution"
)

# Clean up the chart (hide axes/grid) for a professional look
fig_parliament.update_traces(marker=dict(size=12, opacity=0.9, line=dict(width=1, color='white')))
fig_parliament.update_layout(
    showlegend=True,
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False),
    plot_bgcolor="rgba(0,0,0,0)",
    height=500
)

st.plotly_chart(fig_parliament, use_container_width=True)