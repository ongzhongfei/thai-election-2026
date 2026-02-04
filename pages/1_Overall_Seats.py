import streamlit as st
import pandas as pd
import math
import plotly.express as px

st.set_page_config(page_title="Thailand Election", layout="wide")

# 1. Load Data
@st.cache_data
def load_election_data():
    sheet_id = "1fm_6pbiXU6jBwHtu13Yuqh_XgQY-AW03"
    province_gid = "858321697"
    partylist_gid = "374730466"

    def process_sheet(gid):
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url, header=1)
        non_party_cols = ['Province', 'Region', 'Constituency_ID', 'Province (English)', 'District']
        party_cols = [c for c in df.columns if c not in non_party_cols and "Unnamed" not in c]
        for col in party_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['District_Winner'] = df[party_cols].idxmax(axis=1)
        df['Winning_Votes'] = df[party_cols].max(axis=1)
        return df, party_cols

    province_df, _ = process_sheet(province_gid)
    partylist_df, party_cols = process_sheet(partylist_gid)
    return province_df, partylist_df, party_cols

province_df, partylist_df, party_cols = load_election_data()

# 2. Seat Calculations
constituency_winners = province_df['District_Winner'].value_counts()
total_party_votes = partylist_df[party_cols].sum()
total_votes_sum = total_party_votes.sum()

# Initialize calculation dataframe for the Party List breakdown
pl_calc = pd.DataFrame({
    "Total Votes": total_party_votes,
})

if total_votes_sum > 0:
    quota = total_votes_sum / 100
    pl_calc["Quotient"] = pl_calc["Total Votes"] / quota
    pl_calc["Base Seats"] = pl_calc["Quotient"].apply(lambda x: int(x))
    pl_calc["Remainder"] = pl_calc["Quotient"] % 1
    
    # Identify which parties get the extra seats
    extra_seats_needed = 100 - pl_calc["Base Seats"].sum()
    top_remainder_indices = pl_calc["Remainder"].nlargest(int(extra_seats_needed)).index
    
    pl_calc["Extra Seat"] = 0
    pl_calc.loc[top_remainder_indices, "Extra Seat"] = 1
    pl_calc["Final PL Seats"] = pl_calc["Base Seats"] + pl_calc["Extra Seat"]
else:
    pl_calc["Final PL Seats"] = 0

# Final summary for the Arc Chart
summary = pd.DataFrame({
    "Constituency": constituency_winners, 
    "Party List": pl_calc["Final PL Seats"]
}).fillna(0).astype(int)
summary["Total"] = summary["Constituency"] + summary["Party List"]
summary = summary[summary["Total"] > 0].sort_values("Total", ascending=False)

# 3. Visualization Logic (The Arc)
def create_parliament_data(summary_df, province_df, rows=10, radius=10):
    all_seats = []
    for party in summary_df.index:
        party_districts = province_df[province_df['District_Winner'] == party]
        for _, row in party_districts.iterrows():
            all_seats.append({"Party": party, "Info": f"{row['Province (English)']}, {row['District']}"})
        pl_count = summary_df.loc[party, "Party List"]
        for _ in range(pl_count):
            all_seats.append({"Party": party, "Info": "Party List"})
    
    points = []
    for i, seat in enumerate(all_seats):
        row = i % rows
        angle = math.pi * (i / 500)
        r = radius + (row * 0.7)
        points.append({
            "x": r * math.cos(math.pi - angle),
            "y": r * math.sin(math.pi - angle),
            "Party": seat["Party"],
            "Location": seat["Info"]
        })
    return pd.DataFrame(points)

# 4. Display
st.title("🏛️ Thailand Parliament (500 Seats)")

thai_colors = {
    "เพื่อไทย": "#DF0000", "ประชาชน": "#FF6600",
    "ภูมิใจไทย": "#00008B", "ประชาธิปัตย์": "#00BFFF",
    "รวมไทยสร้างชาติ": "#000073", "พลังประชารัฐ": "#0000FF",
    "ชาติไทยพัฒนา": "#FF69B4", "ประชาชาติ": "#8B4513"
}

coords = create_parliament_data(summary, province_df)
fig = px.scatter(
    coords, x="x", y="y", color="Party", 
    color_discrete_map=thai_colors,
    custom_data=["Party", "Location"],
    category_orders={"Party": summary.index.tolist()} 
)
fig.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
    marker=dict(size=14, line=dict(width=1, color='white'))
)
fig.update_layout(
    xaxis=dict(visible=False), yaxis=dict(visible=False),
    plot_bgcolor="rgba(0,0,0,0)", height=600,
    legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Seat Distribution Summary")
st.table(summary)

# --- NEW SECTION: PARTY LIST CALCULATION TABLE ---
st.divider()
st.subheader("📝 Party List Calculation (100 Seats)")
st.write(f"**National Quota:** {total_votes_sum:,} total votes / 100 seats = **{quota:,.2f} votes per seat**")

# Format the calculation table for better readability
formatted_pl = pl_calc.sort_values("Total Votes", ascending=False).copy()
st.dataframe(
    formatted_pl.style.format({
        "Total Votes": "{:,.0f}",
        "Quotient": "{:.4f}",
        "Remainder": "{:.4f}"
    }).highlight_max(subset=["Remainder"], color="#e6f4ea"), 
    use_container_width=True
)