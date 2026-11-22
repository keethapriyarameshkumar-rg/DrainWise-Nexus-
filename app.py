import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

st.set_page_config(
    page_title="DrainWise Nexus",
    page_icon="🌧️",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
[data-testid="stMetric"] {
    background: rgba(80, 120, 160, 0.12);
    border: 1px solid rgba(130, 170, 210, 0.22);
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌧️ DRAINWISE NEXUS")
st.subheader("Network-Aware Flood Preparedness System")
st.caption("Gurugram | SustainX Round 2")

st.info(
    "Prototype Mode: All drainage connections, hotspot counts and sensor "
    "readings are illustrative simulated data, not verified MCG data. "
    "This is a decision-support prototype, not an official flood warning."
)

# Environmental controls
st.sidebar.header("⚙️ Environmental Inputs")

rainfall = st.sidebar.slider(
    "Expected Rainfall (mm)", 0, 200, 100, 5
)

water_level = st.sidebar.slider(
    "Average Drain Water Level (%)", 0, 100, 65
)

crews = st.sidebar.slider(
    "Available Cleaning Crews", 0, 10, 3
)

pumps = st.sidebar.slider(
    "Available Pumps", 0, 10, 2
)

st.sidebar.caption(
    "Change the sliders to test different simulated scenarios."
)

# Illustrative drainage network
drains = pd.DataFrame({
    "Segment": ["D1", "D2", "D3", "D4", "D5"],
    "From": ["A", "B", "C", "D", "E"],
    "To": ["B", "C", "D", "F", "F"],
    "Baseline_Level": [80, 65, 90, 55, 75],
    "Hotspots_Protected": [3, 2, 4, 1, 2],
    "Crew_Hours": [3, 2, 4, 2, 3]
})

# Initial illustrative risk calculation
drains["Base_Risk"] = (
    0.40 * water_level
    + 0.30 * rainfall / 2
    + 0.30 * drains["Baseline_Level"]
).clip(0, 100)

# Network-aware upstream risk propagation
drains["Risk_Score"] = drains["Base_Risk"].copy()

for _ in range(3):

    updated_scores = drains["Risk_Score"].copy()

    for index, row in drains.iterrows():

        upstream_segments = drains[
            drains["To"] == row["From"]
        ]

        if not upstream_segments.empty:

            upstream_risk = upstream_segments["Risk_Score"].max()

            updated_scores.loc[index] = min(
                100,
                0.75 * row["Base_Risk"]
                + 0.25 * upstream_risk
            )

    drains["Risk_Score"] = updated_scores


# Risk classification
def classify_risk(score):

    if score >= 75:
        return "Critical"

    if score >= 60:
        return "High"

    if score >= 40:
        return "Moderate"

    return "Low"


risk_colors = {
    "Low": "#2ECC71",
    "Moderate": "#F1C40F",
    "High": "#E67E22",
    "Critical": "#E74C3C"
}

drains["Risk"] = drains["Risk_Score"].apply(classify_risk)

drains["Color"] = drains["Risk"].map(risk_colors)


# Calculate downstream network impact
def get_downstream_segments(segment):

    destination = drains.loc[
        drains["Segment"] == segment, "To"
    ].iloc[0]

    downstream = drains[
        drains["From"] == destination
    ]

    result = set()

    for _, row in downstream.iterrows():

        if row["Segment"] not in result:

            result.add(row["Segment"])

            result.update(
                get_downstream_segments(row["Segment"])
            )

    return result


drains["Downstream_Segments"] = drains["Segment"].apply(
    get_downstream_segments
)


# Calculate downstream hotspots
drains["Downstream_Hotspots"] = drains.apply(
    lambda row: sum(
        drains.loc[
            drains["Segment"].isin(row["Downstream_Segments"]),
            "Hotspots_Protected"
        ]
    ),
    axis=1
)


# Calculate network importance
drains["Network_Importance"] = (
    drains["Hotspots_Protected"]
    + drains["Downstream_Hotspots"]
)


# Calculate final priority score
drains["Priority_Score"] = (
    drains["Risk_Score"]
    * drains["Network_Importance"]
    / drains["Crew_Hours"]
)


# Sort after calculating priority
drains = drains.sort_values(
    "Priority_Score",
    ascending=False
).reset_index(drop=True)


# Dashboard
st.header("📊 Flood Monitoring Dashboard")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Expected Rainfall", f"{rainfall} mm")
c2.metric("Water Level", f"{water_level}%")
c3.metric("Cleaning Crews", crews)
c4.metric("Available Pumps", pumps)

st.caption(
    "Scenario results recalculate whenever an input changes."
)


# Risk analysis
st.header("🚨 Drainage Risk Analysis")

counts = {
    risk: int((drains["Risk"] == risk).sum())
    for risk in ["Critical", "High", "Moderate", "Low"]
}

r1, r2, r3, r4 = st.columns(4)

r1.metric("Critical Segments", counts["Critical"])
r2.metric("High Risk Segments", counts["High"])
r3.metric("Moderate Segments", counts["Moderate"])
r4.metric("Low Risk Segments", counts["Low"])


risk_table = drains[[
    "Segment",
    "From",
    "To",
    "Baseline_Level",
    "Hotspots_Protected",
    "Risk_Score",
    "Risk"
]].copy().rename(columns={
    "From": "Upstream Junction",
    "To": "Downstream Junction",
    "Baseline_Level": "Illustrative Segment Level (%)",
    "Hotspots_Protected": "Hotspots Protected",
    "Risk_Score": "Risk Score"
})

risk_table["Risk Score"] = risk_table["Risk Score"].round(1)

st.dataframe(
    risk_table,
    use_container_width=True,
    hide_index=True
)


# Directed network visualization
st.header("🗺️ Drainage Network Visualization")

st.caption(
    "Illustrative flow direction: upstream → downstream. "
    "The topology is a prototype assumption and must be verified against MCG maps."
)

G = nx.DiGraph()

for _, row in drains.iterrows():

    G.add_edge(
        row["From"],
        row["To"],
        segment=row["Segment"],
        risk=row["Risk"],
        score=row["Risk_Score"]
    )


positions = {
    "A": (0, 3),
    "B": (2, 4),
    "C": (4, 3),
    "D": (6, 4),
    "E": (2, 1),
    "F": (8, 2)
}

fig = go.Figure()

for u, v, data in G.edges(data=True):

    x0, y0 = positions[u]
    x1, y1 = positions[v]

    color = risk_colors[data["risk"]]

    fig.add_trace(go.Scatter(
        x=[x0, x1],
        y=[y0, y1],
        mode="lines",
        line=dict(width=4, color=color),
        hovertemplate=(
            f'{data["segment"]}: {u} → {v}<br>'
            f'Risk: {data["risk"]}<br>'
            f'Illustrative score: {data["score"]:.1f}<extra></extra>'
        ),
        showlegend=False
    ))

    fig.add_annotation(
        x=x0 + 0.68 * (x1 - x0),
        y=y0 + 0.68 * (y1 - y0),
        ax=x0 + 0.48 * (x1 - x0),
        ay=y0 + 0.48 * (y1 - y0),
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        text="",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.1,
        arrowwidth=2,
        arrowcolor=color
    )


node_scores = {}

for node in G.nodes():

    adjacent = (
        [d["score"] for _, _, d in G.in_edges(node, data=True)]
        + [d["score"] for _, _, d in G.out_edges(node, data=True)]
    )

    node_scores[node] = max(adjacent) if adjacent else 0


fig.add_trace(go.Scatter(
    x=[positions[n][0] for n in G.nodes()],
    y=[positions[n][1] for n in G.nodes()],
    mode="markers+text",
    text=list(G.nodes()),
    textposition="top center",
    marker=dict(
        size=27,
        color=[
            risk_colors[classify_risk(node_scores[n])]
            for n in G.nodes()
        ],
        line=dict(width=1, color="white")
    ),
    customdata=[
        [node_scores[n], classify_risk(node_scores[n])]
        for n in G.nodes()
    ],
    hovertemplate=(
        "Junction %{text}<br>"
        "Highest adjacent segment score: %{customdata[0]:.1f}"
        "<br>Risk: %{customdata[1]}<extra></extra>"
    ),
    showlegend=False
))


for label, color in risk_colors.items():

    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(size=10, color=color),
        name=f"{label} risk"
    ))


fig.update_layout(
    title="Illustrative Drain Connectivity — Direction of Flow",
    height=430,
    margin=dict(l=10, r=10, t=55, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#EAECEF"),
    legend=dict(orientation="h", y=-0.12),
    xaxis=dict(visible=False, range=[-0.7, 8.7]),
    yaxis=dict(visible=False, range=[0.2, 4.8])
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "D1: A→B  |  D2: B→C  |  D3: C→D  |  D4: D→F  |  D5: E→F"
)

# Network impact analysis
st.header("🔗 Network Impact Analysis")

impact_table = drains[[
    "Segment",
    "From",
    "To",
    "Downstream_Segments",
    "Downstream_Hotspots",
    "Network_Importance",
    "Priority_Score"
]].copy()

impact_table["Downstream_Segments"] = impact_table["Downstream_Segments"].apply(
    lambda segments: ", ".join(sorted(segments)) if segments else "None"
)

impact_table = impact_table.rename(columns={
    "Downstream_Segments": "Connected Downstream Segments",
    "Downstream_Hotspots": "Downstream Hotspots",
    "Network_Importance": "Network Importance",
    "Priority_Score": "Priority Score"
})

impact_table["Priority Score"] = impact_table["Priority Score"].round(1)

st.dataframe(impact_table, use_container_width=True, hide_index=True)

st.caption(
    "Network connections and hotspot counts are illustrative "
    "and require validation against verified MCG drainage maps."
)
# Resource allocation
st.header("🛠️ MCG Resource Allocation")

st.write(
    "Priority combines the illustrative risk score, "
    "hotspots protected including downstream hotspots, "
    "and estimated crew-hours."
)

st.subheader("Recommended Cleaning Priorities")


if crews == 0:

    st.warning(
        "No cleaning crews are marked available. "
        "Priority segments are shown for planning only."
    )

else:

    selected = drains.head(crews)

    assignments = selected[[
        "Segment",
        "From",
        "To",
        "Risk",
        "Hotspots_Protected",
        "Downstream_Hotspots",
        "Network_Importance",
        "Crew_Hours",
        "Priority_Score"
    ]].copy().rename(columns={
        "From": "Upstream",
        "To": "Downstream",
        "Hotspots_Protected": "Hotspots Protected",
        "Downstream_Hotspots": "Downstream Hotspots",
        "Network_Importance": "Network Importance",
        "Crew_Hours": "Estimated Crew-hours",
        "Priority_Score": "Priority Score"
    })

    assignments["Priority Score"] = (
        assignments["Priority Score"].round(1)
    )

    st.dataframe(
        assignments,
        use_container_width=True,
        hide_index=True
    )

    st.success(
        f"{len(selected)} priority segment(s) listed "
        f"for up to {crews} available crew(s)."
    )


# Pump recommendations
st.subheader("💧 Pump Deployment")

if pumps == 0:

    st.warning("No pumps are marked available.")

else:

    for _, row in drains.head(
        min(pumps, len(drains))
    ).iterrows():

        st.write(
            f"• Review pump positioning near **{row['Segment']}** "
            f"({row['From']} → {row['To']}; "
            f"estimated risk: **{row['Risk']}**)."
        )


# Preparedness scenario
st.header("⏱️ Preparedness Scenario")

if rainfall >= 150 or water_level >= 85:

    scenario = "Elevated preparedness"

    guidance = (
        "Review high-priority segments, verify local readings and confirm "
        "crew and pump readiness before the expected rainfall period."
    )

elif rainfall >= 80 or water_level >= 65:

    scenario = "Enhanced monitoring"

    guidance = (
        "Increase review of upstream segments and recheck rainfall and "
        "water-level inputs as updated information becomes available."
    )

else:

    scenario = "Routine monitoring"

    guidance = (
        "Continue routine monitoring and verify maintenance records "
        "and resource counts."
    )


st.metric("Scenario Status", scenario)
st.write(guidance)

st.caption(
    "This is an illustrative rule-based scenario, not a validated 24–48 hour "
    "forecast. It does not replace official IMD forecasts or field verification."
)


# Operations protocol
st.header("📋 MCG Operations Protocol")

for item in [
    "Review official rainfall forecasts and their issue time.",
    "Check drain water-level readings and sensor status.",
    "Inspect high-priority upstream drain segments.",
    "Review crew availability and estimated maintenance hours.",
    "Assess suitable pump locations and access conditions.",
    "Verify drainage conditions after maintenance and record the result."
]:

    st.write(f"✓ {item}")


st.warning(
    "These are decision-support recommendations based on simulated prototype "
    "data. MCG officials must verify network topology, field conditions, "
    "resource availability and official forecasts before action."
)

st.caption("DRAINWISE NEXUS | SUSTAINX ROUND 2")
