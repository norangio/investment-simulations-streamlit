import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.simulation import simulate_paths, summarize_paths


def make_band_figure(df: pd.DataFrame, title: str = "Portfolio Value Over Time") -> go.Figure:
    fig = go.Figure()

    # Shaded 10-90 band
    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P90"],
            mode="lines", name="90th percentile",
            line=dict(width=0.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P10"],
            mode="lines", name="10th percentile",
            line=dict(width=0.5), fill="tonexty",
            fillcolor="rgba(100,100,200,0.2)",
        )
    )

    # Median
    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P50"],
            mode="lines", name="Median",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title="Portfolio value",
        hovermode="x unified",
        legend_title_text="Series",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Monte Carlo Investment Planner", page_icon="📈", layout="wide")
st.title("📈 Monte Carlo Investment Planner")
st.caption("Simulate possible futures. Not advice. Just math.")

with st.sidebar:
    st.header("Inputs")

    # Presets
    st.subheader("Quick Presets")
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    with preset_col1:
        conservative = st.button("Conservative", help="5% return, 10% vol", use_container_width=True)
    with preset_col2:
        moderate = st.button("Moderate", help="7% return, 15% vol", use_container_width=True)
    with preset_col3:
        aggressive = st.button("Aggressive", help="9% return, 20% vol", use_container_width=True)

    # Set defaults based on preset (using session state)
    if "preset_applied" not in st.session_state:
        st.session_state.preset_applied = None
    if conservative:
        st.session_state.preset_applied = "conservative"
    elif moderate:
        st.session_state.preset_applied = "moderate"
    elif aggressive:
        st.session_state.preset_applied = "aggressive"

    # Determine default values based on preset
    if st.session_state.preset_applied == "conservative":
        default_mean, default_std = 5.0, 10.0
    elif st.session_state.preset_applied == "aggressive":
        default_mean, default_std = 9.0, 20.0
    else:  # moderate or None
        default_mean, default_std = 7.0, 15.0

    st.divider()
    initial = st.number_input("Initial investment ($)", min_value=0.0, value=10000.0, step=1000.0, format="%0.2f")
    contrib = st.number_input("Annual contribution ($)", min_value=0.0, value=12000.0, step=1000.0, format="%0.2f")
    years = st.number_input("Horizon (years)", min_value=1, max_value=80, value=30, step=1)

    st.subheader("Returns")
    mean_ret = st.number_input("Expected annual return (%)", value=default_mean, step=0.1, format="%0.2f")
    std_ret = st.number_input("Annual volatility (stdev, %)", value=default_std, step=0.5, format="%0.2f")
    expense_ratio = st.number_input("Annual expense ratio (%)", min_value=0.0, value=0.05, step=0.01, format="%0.2f")

    st.subheader("Return Distribution")
    distribution = st.selectbox(
        "Distribution type",
        options=["normal", "t-distribution", "mixture"],
        index=0,
        help="Normal may underestimate tail risk. T-distribution has fatter tails. Mixture models occasional crash years."
    )

    # Show distribution-specific parameters
    t_df = 5.0
    crash_prob = 10.0
    crash_mean = -20.0
    crash_std = 25.0

    if distribution == "t-distribution":
        t_df = st.number_input(
            "Degrees of freedom",
            min_value=2.1, max_value=30.0, value=5.0, step=0.5,
            help="Lower = fatter tails (more extreme events). 5-10 is typical for financial modeling. >30 approaches normal."
        )
    elif distribution == "mixture":
        crash_prob = st.number_input("Crash probability per year (%)", min_value=0.0, max_value=50.0, value=10.0, step=1.0)
        crash_mean = st.number_input("Crash year mean return (%)", value=-20.0, step=1.0)
        crash_std = st.number_input("Crash year volatility (%)", min_value=0.1, value=25.0, step=1.0)

    st.subheader("Contributions & Inflation")
    contrib_growth = st.number_input("Contribution growth per year (%)", min_value=0.0, value=0.0, step=0.5, format="%0.2f")
    inflation = st.number_input("Inflation (for real dollars, %)", min_value=0.0, value=2.5, step=0.1, format="%0.2f")
    timing = st.selectbox("Contribution timing", options=["start", "end"], index=0, help="Start = before growth; End = after growth")

    st.subheader("Goal")
    goal = st.number_input("Target portfolio value ($)", min_value=0.0, value=1000000.0, step=50000.0, format="%0.0f", help="Used to calculate probability of reaching your goal")

    st.subheader("Simulation")
    n_sims = st.slider("Number of simulations", min_value=100, max_value=20000, value=5000, step=100)
    seed = st.number_input("Random seed (optional)", value=42)

# Run simulation
bal_nom, bal_real = simulate_paths(
    initial_amount=initial,
    annual_contribution=contrib,
    years=years,
    mean_return_pct=mean_ret,
    std_return_pct=std_ret,
    n_sims=int(n_sims),
    contrib_growth_pct=contrib_growth,
    expense_ratio_pct=expense_ratio,
    inflation_pct=inflation,
    contribution_timing=timing,
    seed=int(seed),
    distribution=distribution,
    t_df=t_df,
    crash_prob_pct=crash_prob,
    crash_mean_pct=crash_mean,
    crash_std_pct=crash_std,
)

# Summaries
summary_nom = summarize_paths(bal_nom)
summary_real = summarize_paths(bal_real)

# Helper for formatting currency
def format_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    else:
        return f"${value:.0f}"

# Calculate key metrics
final_values = bal_nom[:, -1]
total_contributions = initial + sum(contrib * ((1 + contrib_growth / 100) ** t) for t in range(years))
prob_reach_goal = (final_values >= goal).mean() * 100
median_final = np.median(final_values)
p10_final = np.percentile(final_values, 10)
p90_final = np.percentile(final_values, 90)

# Key metrics row
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Median Final Value",
        value=format_currency(median_final),
        delta=f"{((median_final / total_contributions) - 1) * 100:.0f}% gain" if median_final > total_contributions else f"{((median_final / total_contributions) - 1) * 100:.0f}%"
    )
with col2:
    st.metric(
        label="10th Percentile",
        value=format_currency(p10_final),
        help="Worst 10% of outcomes"
    )
with col3:
    st.metric(
        label="90th Percentile",
        value=format_currency(p90_final),
        help="Best 10% of outcomes"
    )
with col4:
    st.metric(
        label=f"Prob. of {format_currency(goal)}",
        value=f"{prob_reach_goal:.1f}%",
        help=f"Chance of reaching your ${goal:,.0f} goal"
    )

st.divider()

# Tabs for nominal vs real
tab1, tab2 = st.tabs(["Nominal $", "Real $ (inflation-adjusted)"])

with tab1:
    st.subheader("Summary table (Nominal $)")
    st.dataframe(
        summary_nom[["Year", "P10", "P50", "P90", "Mean"]]
        .round(0)
        .rename(columns={"P10": "P10 $", "P50": "Median $", "P90": "P90 $", "Mean": "Mean $"}),
        use_container_width=True,
    )
    fig1 = make_band_figure(summary_nom, title="Nominal portfolio value")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Summary table (Real $)")
    st.dataframe(
        summary_real[["Year", "P10", "P50", "P90", "Mean"]]
        .round(0)
        .rename(columns={"P10": "P10 $ (real)", "P50": "Median $ (real)", "P90": "P90 $ (real)", "Mean": "Mean $ (real)"}),
        use_container_width=True,
    )
    fig2 = make_band_figure(summary_real, title="Inflation-adjusted portfolio value (real)")
    st.plotly_chart(fig2, use_container_width=True)

# Optional: show a sample of single paths
with st.expander("Show a sample of individual simulation paths (nominal)"):
    n_show = st.slider("How many paths to overlay?", 1, 200, 20)
    yrs = np.arange(0, years + 1)
    fig_paths = go.Figure()
    for i in range(n_show):
        fig_paths.add_trace(go.Scatter(x=yrs, y=bal_nom[i, :], mode="lines", name=f"sim {i+1}", line=dict(width=1)))
    # Add median for reference
    fig_paths.add_trace(go.Scatter(x=summary_nom["Year"], y=summary_nom["P50"], mode="lines", name="Median", line=dict(width=3)))
    fig_paths.update_layout(title="Sample simulation paths (nominal)", xaxis_title="Year", yaxis_title="Portfolio value", showlegend=False)
    st.plotly_chart(fig_paths, use_container_width=True)

# Downloads
csv_nom = summary_nom.to_csv(index=False).encode("utf-8")
csv_real = summary_real.to_csv(index=False).encode("utf-8")

colA, colB = st.columns(2)
with colA:
    st.download_button("Download summary (Nominal $)", data=csv_nom, file_name="summary_nominal.csv", mime="text/csv")
with colB:
    st.download_button("Download summary (Real $)", data=csv_real, file_name="summary_real.csv", mime="text/csv")

