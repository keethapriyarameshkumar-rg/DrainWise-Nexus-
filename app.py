import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

st.set_page_config(
    page_title="DrainWise Nexus",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ DRAINWISE NEXUS")
st.subheader("Network-Aware Flood Preparedness System")
st.caption("Gurugram | SustainX Round 2")

st.info(
    "Prototype Mode: All drainage connections and sensor readings "
    "below are illustrative simulated data, not verified MCG data."
)

# SIDEBAR INPUTS

st.sidebar.header("⚙️ Environmental Inputs")

rainfall = st.sidebar.slider(
    "Expected Rainfall (mm)",
    0, 200, 100
)

water_level = st.sidebar.slider(
    "Average Drain Water Level (%)",
    0, 100, 65
)

crews = st.sidebar.slider(
    "Available Cleaning Crews",
    1, 10, 3
)

pumps = st.sidebar.slider(
    "Available Pumps",
    1, 10, 2
)

# SIMULATED DRAINAGE DATA

drains = pd.DataFrame({
    "Segment": ["D1", "D2", "D3", "D4", "D5"],
    "From": ["A", "B", "C", "D", "E"],
    "To": ["B", "C", "D", "F", "F"],
    "Water_Level": [80, 65, 90, 55, 75],
    "Hotspots_Protected": [3, 2, 4, 1, 2],
    "Crew_Hours": [3, 2, 4, 2, 3]
})

# FLOOD RISK CALCULATION

drains["Risk_Score"] = (
    0.4 * water_level +
    0.3 * rainfall / 2 +
    0.3 * drains["Water_Level"]
)

def classify_risk(score):
    if score >= 75:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"

drains["Risk"] = drains["Risk_Score"].apply(classify_risk)

# PRIORITY CALCULATION

drains["Priority_Score"] = (
    drains["Risk_Score"] *
    drains["Hotspots_Protected"] /
    drains["Crew_Hours"]
)

drains = drains.sort_values(
    "Priority_Score",
    ascending=False
).reset_index(drop=True)

# DASHBOARD METRICS

st.header("📊 Flood Monitoring Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Expected Rainfall", f"{rainfall} mm")
c2.metric("Water Level", f"{water_level}%")
c3.metric("Cleaning Crews", crews)
c4.metric("Available Pumps", pumps)

# RISK ANALYSIS

st.header("🚨 Drainage Risk Analysis")

critical = len(drains[drains["Risk"] == "Critical"])
high = len(drains[drains["Risk"] == "High"])

r1, r2, r3 = st.columns(3)

r1.metric("Critical Segments", critical)
r2.metric("High Risk Segments", high)
r3.metric("Total Drain Segments", len(drains))

st.dataframe(
    drains[
        ["Segment", "Water_Level", "Hotspots_Protected",
         "Risk_Score", "Risk"]
    ],
    use_container_width=True
)

# NETWORK VISUALIZATION

st.header("🗺️ Drainage Network Visualization")

G = nx.DiGraph()

for _, row in drains.iterrows():
    G.add_edge(row["From"], row["To"], segment=row["Segment"])

positions = {
    "A": (0, 3),
    "B": (2, 4),
    "C": (4, 3),
    "D": (6, 4),
    "E": (2, 1),
    "F": (8, 2)
}

edge_x = []
edge_y = []

for u, v in G.edges():
    x0, y0 = positions[u]
    x1, y1 = positions[v]

    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=edge_x,
    y=edge_y,
    mode="lines",
    line=dict(width=3, color="blue"),
    hoverinfo="none"
))

fig.add_trace(go.Scatter(
    x=[positions[n][0] for n in G.nodes()],
    y=[positions[n][1] for n in G.nodes()],
    mode="markers+text",
    text=list(G.nodes()),
    textposition="top center",
    marker=dict(size=25, color="lightblue"),
    hoverinfo="text"
))

fig.update_layout(
    title="Illustrative Drain Connectivity",
    showlegend=False,
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# RESOURCE OPTIMIZATION

st.header("🛠️ MCG Resource Allocation")

st.write(
    "Priority is calculated using estimated risk, "
    "number of hotspots protected and crew-hours required."
)

selected = drains.head(crews)

st.subheader("Recommended Cleaning Priorities")

st.dataframe(
    selected[
        ["Segment", "Risk", "Hotspots_Protected",
         "Crew_Hours", "Priority_Score"]
    ],
    use_container_width=True
)

st.success(
    f"Recommended cleaning assignments: {len(selected)} crews"
)

# PUMP RECOMMENDATIONS

st.subheader("💧 Pump Deployment")

pump_locations = drains.head(pumps)

for _, row in pump_locations.iterrows():
    st.write(
        f"• Consider positioning a pump near the drainage "
        f"area associated with {row['Segment']} "
        f"(Risk: {row['Risk']})"
    )

# OPERATIONS PROTOCOL

st.header("📋 MCG Operations Protocol")

st.write("1. Review rainfall forecasts.")
st.write("2. Check water-level sensor readings.")
st.write("3. Inspect high-priority upstream drain segments.")
st.write("4. Allocate available cleaning crews.")
st.write("5. Position pumps at vulnerable locations.")
st.write("6. Verify drainage improvement after maintenance.")

st.warning(
    "These are decision-support recommendations. "
    "MCG officials must verify field conditions before action."
)

st.caption("DRAINWISE NEXUS | SUSTAINX ROUND 2")
