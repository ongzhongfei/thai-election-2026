import streamlit as st
import pandas as pd
import math
import plotly.express as px

st.set_page_config(page_title="Thailand Election 2026", layout="wide")

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
        row_max = df[party_cols].max(axis=1)
        row_idxmax = df[party_cols].idxmax(axis=1)

        # Only assign a winner if the max vote is > 0; otherwise, leave blank
        df['District_Winner'] = row_idxmax.where(row_max > 0, "NO INFORMATION YET")
        df['Winning_Votes'] = row_max
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
    "Constituency Seats": constituency_winners, 
    "Party List": pl_calc["Final PL Seats"]
}).fillna(0).astype(int)
summary["Total"] = summary["Constituency Seats"] + summary["Party List"]
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
    "ชาติไทยพัฒนา": "#FF69B4", "ประชาชาติ": "#8B4513",
    "NO INFORMATION YET": "#D3D3D3",
    "พรรคเศรษฐกิจ":"#FFD700","พรรคกล้าธรรม":"#00A651"
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

st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("📊 Seat Distribution Summary")
# Create a copy to add percentage columns without affecting the original summary used for the Arc
summary_display = summary.copy()

# Calculate percentages based on the fixed total house sizes
summary_display["Constituency %"] = (summary_display["Constituency Seats"] / 400 * 100).map("{:.1f}%".format)
summary_display["Total %"] = (summary_display["Total"] / 500 * 100).map("{:.1f}%".format)

# Reorder columns for better flow: Seats then their corresponding %
summary_display = summary_display[[
    "Constituency Seats", "Constituency %", 
    "Party List", 
    "Total", "Total %"
]]
parties = summary.index.tolist()
cols_per_row = 5

for i in range(0, len(parties), cols_per_row):
    row_parties = parties[i:i + cols_per_row]
    row_cols = st.columns(len(row_parties))
    
    for party, col in zip(row_parties, row_cols):
        with col:
            color = thai_colors.get(party, "#808080")
            total_seats = summary.loc[party, 'Total']
            # Calculate total percentage for the card
            total_pct = (total_seats / 500) * 100
            
            st.markdown(f"""
                <div style="border-left: 5px solid {color}; padding: 10px; background-color: #f9f9f9; border-radius: 5px; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #333;">{party}</h4>
                    <p style="margin: 5px 0 2px 0; font-size: 1.3em; color: #666;">
                        Total: <b>{total_seats}</b> <span style="font-size: 0.7em;">({total_pct:.1f}%)</span>
                    </p>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 2px 0; font-size: 0.9em;">🏛️ Constituency: {summary.loc[party, 'Constituency Seats']}</p>
                    <p style="margin: 2px 0; font-size: 0.9em;">📝 List: {summary.loc[party, 'Party List']}</p>
                </div>
            """, unsafe_allow_html=True)
st.subheader("Total Parliament Control Share (500 Seats)")
# Using 'Seats' as the numeric value ensures proportional slices
fig_pie = px.pie(summary, values="Total", names=summary.index.tolist(), 
                    color=summary.index.tolist(), color_discrete_map=thai_colors, hole=0.2)
st.plotly_chart(fig_pie, width='stretch')

st.markdown("<br>", unsafe_allow_html=True) 

# 3. Add Total Row and Display Table
# ---------------------------------------------------------
# Calculate totals for the numeric columns only
numeric_totals = summary.sum(numeric_only=True)
totals_df = pd.DataFrame(numeric_totals).T
totals_df.index = ["TOTAL"]

# Calculate percentages for the TOTAL row
totals_df["Constituency %"] = (totals_df["Constituency Seats"] / 400 * 100).map("{:.1f}%".format)
totals_df["Total %"] = (totals_df["Total"] / 500 * 100).map("{:.1f}%".format)

# Combine and display
summary_final = pd.concat([summary_display, totals_df[summary_display.columns]])
st.table(summary_final)         

# --- NEW SECTION: Voting detail breakdown ---
st.divider()
st.subheader("🗳️ Constituency Voting Details")
with st.expander("See detailed vote counts and seat allocations for each party"):
    detailed_table = pl_calc.copy()
    detailed_table["Constituency Seats"] = detailed_table.index.map(constituency_winners).fillna(0).astype(int)
    detailed_table = detailed_table[["Total Votes", "Constituency Seats"]]
    detailed_table.columns = ["Total Votes", "Constituency Seats"]
    st.dataframe(
        detailed_table.style.format({
            "Total Votes": "{:,.0f}"
        }), 
        width="stretch"
    )
    st.dataframe(province_df)
# --- NEW SECTION: PARTY LIST CALCULATION TABLE ---
st.divider()
st.subheader("📝 Party List Calculation (100 Seats)")
with st.expander("How are Party List seats calculated?"):

    st.info("""
    **How the Party List is Calculated**

    The seats are allocated using the [Largest Remainder Method (LRM) with a Hare Quota](https://www.thaidatapoints.com/post/calculating-the-party-list-seats):

    1. **Calculate the Quota:** The total valid votes are divided by 100 (the number of available seats).
    2. **Initial Allocation:** Each party gets seats based on the whole number (integer) of their votes divided by the quota.
    3. **Remainder Seats:** Any leftover seats are given to parties with the largest "fractions" or remainders until all 100 seats are filled.
    """, icon="ℹ️")
    st.write(f"**National Quota:** {total_votes_sum:,} total votes / 100 seats = **{quota:,.2f} votes per seat**")

    # Format the calculation table for better readability
    formatted_pl = pl_calc.sort_values("Total Votes", ascending=False).copy()
    st.dataframe(
        formatted_pl.style.format({
            "Total Votes": "{:,.0f}",
            "Quotient": "{:.4f}",
            "Remainder": "{:.4f}"
        }).highlight_max(subset=["Extra Seat"], color="#e6f4ea"), 
        width="stretch"
    )