import streamlit as st
import pandas as pd
import math
import plotly.express as px

st.set_page_config(page_title="Total 500 Seats", layout="wide")

# 1. Load Data
@st.cache_data
def load_overall_data():
    df = pd.read_excel("Th election Province list.xlsx", skiprows=2)
    non_party_cols = ['Province', 'Region','Constituency_ID','District (English)','District']
    party_cols = [c for c in df.columns if c not in non_party_cols]
    for col in party_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df, party_cols

df, party_cols = load_overall_data()

# 2. Calculations
constituency_winners = df[party_cols].idxmax(axis=1).value_counts()
total_party_votes = df[party_cols].sum()
quota = total_party_votes.sum() / 100

pl_seats = (total_party_votes / quota).apply(lambda x: int(x))
remainders = (total_party_votes / quota) % 1
extra_seats = 100 - pl_seats.sum()
top_remainders = remainders.nlargest(int(extra_seats)).index
for party in top_remainders:
    pl_seats[party] += 1

summary = pd.DataFrame({
    "Constituency": constituency_winners,
    "Party-List": pl_seats
}).fillna(0).astype(int)
summary["Total Seats"] = summary["Constituency"] + summary["Party-List"]
summary = summary.sort_values("Total Seats", ascending=False)

# 3. UI Layout
st.title("🏛️ Total Parliament (500 Seats)")

# --- NEW: COALITION BUILDER ---
st.sidebar.header("🤝 Coalition Builder")
st.sidebar.write("Select parties to form a government:")
# Create checkboxes for each party
selected_parties = []
for party in summary.index:
    if st.sidebar.checkbox(party, key=f"coal_{party}"):
        selected_parties.append(party)

coalition_total = summary.loc[selected_parties, "Total Seats"].sum()

# Display Coalition Status
st.sidebar.divider()
st.sidebar.subheader(f"Coalition Strength: {coalition_total}")
if coalition_total >= 376:
    st.sidebar.success("✅ Majority Reached (Prime Minister Secured)")
elif coalition_total >= 251:
    st.sidebar.warning("⚠️ House Majority (But needs Senate/Extra for PM)")
else:
    st.sidebar.info("❌ Minority (Need more partners)")

# 4. Bubble Chart logic
def get_parliament_coords(seat_counts, rows=10, radius=6):
    data = []
    total_seats = sum(seat_counts.values())
    sorted_parties = sorted(seat_counts.items(), key=lambda x: x[1], reverse=True)
    
    all_seats = []
    for party, count in sorted_parties:
        all_seats.extend([party] * count)
        
    for i in range(len(all_seats)):
        row = i % rows
        angle = math.pi * (i / 500) 
        r = radius + (row * 0.5)
        x = r * math.cos(math.pi - angle)
        y = r * math.sin(math.pi - angle)
        # Check if seat is in the selected coalition for highlighting
        is_coalition = "In Coalition" if all_seats[i] in selected_parties else "Opposition"
        data.append({"x": x, "y": y, "Party": all_seats[i], "Status": is_coalition})
    return pd.DataFrame(data)

coords_df = get_parliament_coords(summary["Total Seats"].to_dict())

# Use the Thai color map you provided
thai_colors = {
    "ประชาชน": "#FF6600", "เพื่อไทย": "#DF0000", 
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "พรรคเศรษฐกิจ": "#DAF759", "พรรคกล้าธรรม": "#065A1F",
    "Others": "#808080"
}

fig_parliament = px.scatter(
    coords_df, x="x", y="y", color="Party",
    color_discrete_map=thai_colors,
    hover_data=["Status"]
)

fig_parliament.update_traces(marker=dict(size=10, line=dict(width=1, color='white')))
fig_parliament.update_layout(
    showlegend=True,
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    plot_bgcolor="rgba(0,0,0,0)",
    height=600
)

st.plotly_chart(fig_parliament, width="stretch") # Updated to your 'stretch' syntax!

st.table(summary)