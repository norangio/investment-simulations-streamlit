import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.simulation import simulate_paths, summarize_paths


DISTRIBUTION_OPTIONS = {
    "regime-t": "Regime-aware fat tails (recommended)",
    "normal": "Normal IID baseline",
    "t-distribution": "Student's t IID fat tails",
    "mixture": "Crash-regime mixture",
}

DISTRIBUTION_HELP = {
    "regime-t": (
        "Default. Ordinary years use a fat-tailed Student's t distribution, "
        "with random crash years layered in. The ordinary-year mean is calibrated "
        "so the user's expected return remains the long-run target."
    ),
    "normal": "Simple independent normal annual returns. Useful as a baseline, but it understates tail risk.",
    "t-distribution": "Independent fat-tailed annual returns. Captures extreme years better than normal IID.",
    "mixture": (
        "Ordinary normal years plus randomly occurring crash years. The ordinary-year mean is calibrated "
        "so the user's expected return remains the long-run target."
    ),
}


PRIMARY_LINE = "#6f8295"
BAND_FILL = "rgba(151, 170, 188, 0.22)"
PERCENTILE_LINE = "#aab6c2"
GRID_COLOR = "#e5e7eb"
TEXT_COLOR = "#27313b"
CONTRIBUTION_MARKER = "#8aa0b3"
WITHDRAWAL_MARKER = "#b8949f"
GOAL_LINE = "#7ba68a"


def apply_figure_style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title="Portfolio value",
        hovermode="x unified",
        legend_title_text="Series",
        margin=dict(l=40, r=20, t=54, b=40),
        paper_bgcolor="#f7f8fa",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=12, color=TEXT_COLOR),
        title_font=dict(size=15, color=TEXT_COLOR),
        legend=dict(font=dict(size=11)),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig


SUPPLEMENTAL_MARKER = "#7ba68a"


def add_timing_markers(
    fig: go.Figure,
    contribution_stop_year: int | None = None,
    withdrawal_start_year: int | None = None,
    supplemental_start_year: int | None = None,
) -> go.Figure:
    if contribution_stop_year is not None:
        fig.add_vline(
            x=contribution_stop_year,
            line_width=1,
            line_dash="dash",
            line_color=CONTRIBUTION_MARKER,
            annotation_text="contributions stop",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color=TEXT_COLOR,
        )
    if withdrawal_start_year is not None:
        fig.add_vline(
            x=withdrawal_start_year,
            line_width=1,
            line_dash="dot",
            line_color=WITHDRAWAL_MARKER,
            annotation_text="withdrawals start",
            annotation_position="top right",
            annotation_font_size=10,
            annotation_font_color=TEXT_COLOR,
        )
    if supplemental_start_year is not None:
        fig.add_vline(
            x=supplemental_start_year,
            line_width=1,
            line_dash="dashdot",
            line_color=SUPPLEMENTAL_MARKER,
            annotation_text="SS/income starts",
            annotation_position="bottom right",
            annotation_font_size=10,
            annotation_font_color=SUPPLEMENTAL_MARKER,
        )
    return fig


def add_goal_line(fig: go.Figure, goal: float) -> go.Figure:
    fig.add_hline(
        y=goal,
        line_width=1.5,
        line_dash="dash",
        line_color=GOAL_LINE,
        annotation_text=f"Goal: {format_currency(goal)}",
        annotation_position="top right",
        annotation_font_size=10,
        annotation_font_color=GOAL_LINE,
    )
    return fig


def make_band_figure(df: pd.DataFrame, title: str = "Portfolio Value Over Time") -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P90"],
            mode="lines", name="90th percentile",
            line=dict(width=0.8, color=PERCENTILE_LINE),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P10"],
            mode="lines", name="10th percentile",
            line=dict(width=0.8, color=PERCENTILE_LINE), fill="tonexty",
            fillcolor=BAND_FILL,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["Year"], y=df["P50"],
            mode="lines", name="Median",
            line=dict(width=2.4, color=PRIMARY_LINE),
        )
    )

    return apply_figure_style(fig, title)


def format_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.2f}M"
    elif abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.0f}K"
    else:
        return f"{sign}${abs_value:.0f}"


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Monte Carlo Investment Planner", layout="wide")
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        :root {
            --app-bg: #f4f5f6;
            --panel-bg: #fbfbfa;
            --border: #d7dce1;
            --text: #27313b;
            --muted: #66717d;
            --accent: #6f8295;
            --accent-soft: #d9e5ea;
            --accent-green: #b9d8c5;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--app-bg);
            color: var(--text);
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
        }

        /* Hide Streamlit chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent;}

        [data-testid="stSidebar"] {
            background: #eef1f3;
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            font-size: 12px;
        }

        h1 {
            color: var(--text);
            font-size: 1.85rem !important;
            font-weight: 600 !important;
            letter-spacing: 0 !important;
            margin-bottom: 0.15rem !important;
        }

        h2, h3 {
            color: var(--text);
            font-size: 1rem !important;
            font-weight: 600 !important;
            letter-spacing: 0 !important;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--muted);
            font-size: 0.78rem;
        }

        [data-testid="stMetric"] {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.85rem 0.95rem;
            box-shadow: none;
        }

        [data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 500;
        }

        [data-testid="stMetricValue"] {
            font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
            color: var(--text);
            font-size: 1.35rem;
        }

        [data-testid="stMetricDelta"] {
            font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.75rem;
        }

        /* Highlighted scorecard */
        .scorecard {
            background: linear-gradient(135deg, #eaf2ed 0%, #f0f5f2 100%);
            border: 1.5px solid #b9d8c5;
            border-radius: 8px;
            padding: 1.2rem 1.5rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        .scorecard .value {
            font-family: "IBM Plex Mono", ui-monospace, monospace;
            font-size: 2.2rem;
            font-weight: 600;
            color: var(--text);
            margin: 0.3rem 0;
        }
        .scorecard .label {
            font-size: 0.8rem;
            color: var(--muted);
            font-weight: 500;
        }

        div[data-baseweb="select"] > div,
        input,
        textarea {
            background: #ffffff !important;
            border-color: var(--border) !important;
            border-radius: 5px !important;
            font-size: 12px !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            background: var(--accent-soft);
            color: var(--text);
            border: 1px solid #bdcbd5;
            border-radius: 5px;
            font-size: 12px;
            font-weight: 500;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 12px;
            color: var(--muted);
            padding: 0.55rem 0.75rem;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
        }

        code, pre {
            font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Monte Carlo Investment Planner")
st.caption("Projection model for portfolio accumulation, withdrawals, and tail-risk scenarios.")

with st.sidebar:
    st.markdown("**Core Assumptions**")
    default_mean, default_std = 7.0, 15.0

    initial = st.number_input("Initial investment ($)", min_value=0.0, value=10000.0, step=1000.0, format="%0.2f")
    contrib = st.number_input("Annual contribution ($)", min_value=0.0, value=12000.0, step=1000.0, format="%0.2f")
    years = st.number_input("Horizon (years)", min_value=1, max_value=80, value=30, step=1)

    st.markdown("**Returns**")
    mean_ret = st.number_input(
        "Long-run expected annual return (%)",
        value=default_mean,
        step=0.1,
        format="%0.2f",
        help="Target arithmetic annual return before expenses. Regime models calibrate ordinary years around this long-run target.",
    )
    std_ret = st.number_input("Annual volatility (stdev, %)", value=default_std, step=0.5, format="%0.2f")
    expense_ratio = st.number_input("Annual expense ratio (%)", min_value=0.0, value=0.05, step=0.01, format="%0.2f")

    with st.expander("Distribution settings"):
        distribution_label = st.selectbox(
            "Distribution type",
            options=list(DISTRIBUTION_OPTIONS.values()),
            index=0,
            help="Controls how annual returns are sampled."
        )
        distribution = next(key for key, label in DISTRIBUTION_OPTIONS.items() if label == distribution_label)
        st.caption(DISTRIBUTION_HELP[distribution])

        t_df = 5.0
        crash_prob = 8.0
        crash_mean = -24.0
        crash_std = 25.0

        if distribution in {"regime-t", "t-distribution"}:
            t_df = st.number_input(
                "Degrees of freedom",
                min_value=2.1, max_value=30.0, value=5.0, step=0.5,
                help="Lower = fatter tails (more extreme events). 5-10 is typical for financial modeling. >30 approaches normal."
            )
        if distribution in {"regime-t", "mixture"}:
            crash_prob = st.number_input("Crash probability per year (%)", min_value=0.0, max_value=50.0, value=8.0, step=1.0)
            crash_mean = st.number_input("Crash year mean return (%)", value=-24.0, step=1.0)
            crash_std = st.number_input("Crash year volatility (%)", min_value=0.1, value=25.0, step=1.0)

    st.markdown("**Contributions & Inflation**")
    contrib_growth = st.number_input("Contribution growth per year (%)", min_value=0.0, value=0.0, step=0.5, format="%0.2f")
    contribution_stop_year = st.number_input(
        "Last contribution year",
        min_value=0,
        max_value=int(years),
        value=int(years),
        step=1,
        help="A value of 10 means contributions are made through Year 10, then stop before Year 11. Use 0 for no future contributions.",
    )
    inflation = st.number_input("Inflation (for real dollars, %)", min_value=0.0, value=2.5, step=0.1, format="%0.2f")
    timing = st.selectbox("Contribution timing", options=["start", "end"], index=0, help="Start = before growth; End = after growth")

    with st.expander("Withdrawals"):
        withdrawal = st.number_input(
            "Annual withdrawal ($)",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            format="%0.2f",
            help="Total annual spending need from the portfolio, before any supplemental income offsets it.",
        )
        withdrawal_start = st.number_input(
            "First withdrawal year",
            min_value=1,
            max_value=int(years),
            value=min(10, int(years)),
            step=1,
            help="A value of 10 means the first withdrawal is taken at the end of Year 10.",
        )
        withdrawal_growth = st.number_input(
            "Withdrawal growth per year (%)",
            min_value=0.0,
            value=float(inflation),
            step=0.1,
            format="%0.2f",
            help="Use the inflation rate to model fixed real spending.",
        )

        st.markdown("---")
        st.markdown("**Supplemental income (SS, pension, etc.)**")
        supplemental_monthly = st.number_input(
            "Monthly income in today's dollars ($)",
            min_value=0.0,
            value=0.0,
            step=500.0,
            format="%0.0f",
            help="Social Security, pension, or other income that reduces how much you need from the portfolio.",
        )
        supplemental_income = supplemental_monthly * 12
        supplemental_income_start_year = st.number_input(
            "Income starts in simulation year",
            min_value=1,
            max_value=int(years),
            value=min(int(years), max(1, int(withdrawal_start) + 10)),
            step=1,
            help="The simulation year when this income begins (e.g., if you retire in year 20 and SS starts 10 years later, enter 30).",
        )
        if supplemental_income > 0:
            st.caption(
                f"Portfolio withdrawal drops from {format_currency(withdrawal)}/yr to "
                f"~{format_currency(max(withdrawal - supplemental_income, 0))}/yr in year {supplemental_income_start_year}"
            )

    st.markdown("**Retirement Goal**")
    desired_spending = st.number_input(
        "Desired annual spending in today's dollars ($)",
        min_value=0.0,
        value=150000.0,
        step=5000.0,
        format="%0.0f",
        help="How much you want to withdraw per year in retirement, in today's purchasing power.",
    )
    withdrawal_rate = st.number_input(
        "Safe withdrawal rate (%)",
        min_value=0.1,
        max_value=20.0,
        value=4.0,
        step=0.25,
        format="%0.2f",
        help="The 4% rule means you need 25x your annual spending. Lower rates are more conservative.",
    )
    goal = desired_spending / (withdrawal_rate / 100)
    st.caption(f"Required portfolio: **{format_currency(goal)}** in today's dollars")

    with st.expander("Simulation settings"):
        n_sims = st.slider("Number of simulations", min_value=100, max_value=20000, value=5000, step=100)
        seed = st.number_input("Random seed (optional)", value=42)

# Run simulation
simulation_kwargs = dict(
    initial_amount=initial,
    annual_contribution=contrib,
    years=int(years),
    mean_return_pct=mean_ret,
    std_return_pct=std_ret,
    n_sims=int(n_sims),
    contrib_growth_pct=contrib_growth,
    expense_ratio_pct=expense_ratio,
    inflation_pct=inflation,
    contribution_timing=timing,
    contribution_stop_year=int(contribution_stop_year),
    annual_withdrawal=withdrawal,
    withdrawal_start_year=int(withdrawal_start),
    withdrawal_growth_pct=withdrawal_growth,
    supplemental_income=supplemental_income,
    supplemental_income_start_year=int(supplemental_income_start_year),
    seed=int(seed),
    distribution=distribution,
    t_df=t_df,
    crash_prob_pct=crash_prob,
    crash_mean_pct=crash_mean,
    crash_std_pct=crash_std,
)
bal_nom, bal_real = simulate_paths(**simulation_kwargs)
bal_nom_no_withdraw = None
if withdrawal > 0:
    no_withdraw_kwargs = {
        **simulation_kwargs,
        "annual_withdrawal": 0.0,
        "withdrawal_growth_pct": 0.0,
        "supplemental_income": 0.0,
    }
    bal_nom_no_withdraw, _ = simulate_paths(**no_withdraw_kwargs)

# Summaries
summary_nom = summarize_paths(bal_nom)
summary_real = summarize_paths(bal_real)

# Calculate key metrics (all in real/today's dollars)
final_values_real = bal_real[:, -1]
total_contributions = initial + sum(
    contrib * ((1 + contrib_growth / 100) ** t)
    for t in range(min(int(contribution_stop_year), int(years)))
)
scheduled_withdrawals = (
    sum(withdrawal * ((1 + withdrawal_growth / 100) ** (year - withdrawal_start)) for year in range(int(withdrawal_start), int(years) + 1))
    if withdrawal > 0
    else 0.0
)
prob_reach_goal = (final_values_real >= goal).mean() * 100
median_final = np.median(final_values_real)
p10_final = np.percentile(final_values_real, 10)
p90_final = np.percentile(final_values_real, 90)
median_withdrawal_impact = None
if bal_nom_no_withdraw is not None:
    bal_real_no_withdraw = bal_nom_no_withdraw.copy()
    for t in range(bal_real_no_withdraw.shape[1]):
        bal_real_no_withdraw[:, t] /= (1 + inflation / 100) ** t
    median_withdrawal_impact = median_final - np.median(bal_real_no_withdraw[:, -1])
contribution_marker_year = (
    int(contribution_stop_year)
    if contrib > 0 and 0 <= int(contribution_stop_year) < int(years)
    else None
)
withdrawal_marker_year = int(withdrawal_start) if withdrawal > 0 else None
supplemental_marker_year = int(supplemental_income_start_year) if supplemental_income > 0 and withdrawal > 0 else None

# Headline scorecard
scorecard_subtitle = f"{n_sims:,} simulations · {years} years · supports {format_currency(desired_spending)}/yr at {withdrawal_rate:.1f}% withdrawal"
if supplemental_income > 0:
    scorecard_subtitle += f" · SS/income offsets {format_currency(supplemental_income)}/yr from year {supplemental_income_start_year}"
st.markdown(
    f"""
    <div class="scorecard">
        <div class="label">Probability of reaching {format_currency(goal)} in today's dollars</div>
        <div class="value">{prob_reach_goal:.1f}%</div>
        <div class="label">{scorecard_subtitle}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Key metrics row (all in today's dollars)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if total_contributions > 0:
        st.metric(
            label="Median Final (today's $)",
            value=format_currency(median_final),
            delta=f"{((median_final / total_contributions) - 1) * 100:.0f}% vs contributions",
        )
    else:
        st.metric(
            label="Median Final (today's $)",
            value=format_currency(median_final),
        )
with col2:
    st.metric(
        label="10th Percentile (today's $)",
        value=format_currency(p10_final),
        help="Worst 10% of outcomes in today's purchasing power"
    )
with col3:
    st.metric(
        label="90th Percentile (today's $)",
        value=format_currency(p90_final),
        help="Best 10% of outcomes in today's purchasing power"
    )
with col4:
    if median_withdrawal_impact is None:
        st.metric(
            label="Scheduled Withdrawals",
            value=format_currency(scheduled_withdrawals),
            help="Total planned withdrawals over the simulation horizon."
        )
    else:
        st.metric(
            label="Withdrawal Impact (today's $)",
            value=format_currency(median_withdrawal_impact),
            help="Difference versus the same simulation settings with no withdrawals, in today's purchasing power."
        )

st.divider()

# Tabs for nominal vs real
tab1, tab2, tab3 = st.tabs(["Today's Dollars", "Nominal $", "Distribution of Outcomes"])

MILESTONE_YEARS = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80]

with tab1:
    fig1 = make_band_figure(summary_real, title="Portfolio value in today's dollars")
    add_goal_line(fig1, goal)
    add_timing_markers(fig1, contribution_marker_year, withdrawal_marker_year, supplemental_marker_year)
    st.plotly_chart(fig1, use_container_width=True)

    milestones = [0] + [y for y in MILESTONE_YEARS if y <= int(years)] + ([int(years)] if int(years) not in MILESTONE_YEARS else [])
    milestone_df = summary_real[summary_real["Year"].isin(milestones)][["Year", "P10", "P50", "P90", "Mean"]].round(0)
    milestone_df = milestone_df.rename(columns={"P10": "P10 (today's $)", "P50": "Median (today's $)", "P90": "P90 (today's $)", "Mean": "Mean (today's $)"})
    st.dataframe(milestone_df, use_container_width=True, hide_index=True)

    with st.expander("Full yearly table"):
        st.dataframe(
            summary_real[["Year", "P10", "P50", "P90", "Mean"]]
            .round(0)
            .rename(columns={"P10": "P10 (today's $)", "P50": "Median (today's $)", "P90": "P90 (today's $)", "Mean": "Mean (today's $)"}),
            use_container_width=True,
            hide_index=True,
        )

with tab2:
    fig2 = make_band_figure(summary_nom, title="Nominal portfolio value (future dollars)")
    add_timing_markers(fig2, contribution_marker_year, withdrawal_marker_year, supplemental_marker_year)
    st.plotly_chart(fig2, use_container_width=True)

    milestone_df_nom = summary_nom[summary_nom["Year"].isin(milestones)][["Year", "P10", "P50", "P90", "Mean"]].round(0)
    milestone_df_nom = milestone_df_nom.rename(columns={"P10": "P10 $", "P50": "Median $", "P90": "P90 $", "Mean": "Mean $"})
    st.dataframe(milestone_df_nom, use_container_width=True, hide_index=True)

    with st.expander("Full yearly table"):
        st.dataframe(
            summary_nom[["Year", "P10", "P50", "P90", "Mean"]]
            .round(0)
            .rename(columns={"P10": "P10 $", "P50": "Median $", "P90": "P90 $", "Mean": "Mean $"}),
            use_container_width=True,
            hide_index=True,
        )

with tab3:
    fig_hist = go.Figure()
    fig_hist.add_trace(
        go.Histogram(
            x=final_values_real,
            nbinsx=80,
            marker_color=PRIMARY_LINE,
            opacity=0.75,
            name="Final values",
        )
    )
    fig_hist.add_vline(
        x=goal,
        line_width=2,
        line_dash="dash",
        line_color=GOAL_LINE,
        annotation_text=f"Goal: {format_currency(goal)}",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color=GOAL_LINE,
    )
    fig_hist.add_vline(
        x=median_final,
        line_width=2,
        line_dash="solid",
        line_color=TEXT_COLOR,
        annotation_text=f"Median: {format_currency(median_final)}",
        annotation_position="top left",
        annotation_font_size=11,
        annotation_font_color=TEXT_COLOR,
    )
    fig_hist.update_layout(
        title="Distribution of Final Portfolio Values (today's dollars)",
        xaxis_title="Final portfolio value (today's $)",
        yaxis_title="Count",
        margin=dict(l=40, r=20, t=54, b=40),
        paper_bgcolor="#f7f8fa",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=12, color=TEXT_COLOR),
        title_font=dict(size=15, color=TEXT_COLOR),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        bargap=0.05,
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption(f"{prob_reach_goal:.1f}% of simulations reach or exceed {format_currency(goal)} in today's purchasing power.")

# Sample paths (kept as an expander)
with st.expander("Show a sample of individual simulation paths (nominal)"):
    n_show = st.slider("How many paths to overlay?", 1, 200, 20)
    yrs = np.arange(0, years + 1)
    fig_paths = go.Figure()
    for i in range(n_show):
        fig_paths.add_trace(go.Scatter(x=yrs, y=bal_nom[i, :], mode="lines", name=f"sim {i+1}", line=dict(width=1, color="rgba(111,130,149,0.28)")))
    fig_paths.add_trace(go.Scatter(x=summary_nom["Year"], y=summary_nom["P50"], mode="lines", name="Median", line=dict(width=3, color=PRIMARY_LINE)))
    apply_figure_style(fig_paths, "Sample simulation paths (nominal)")
    add_timing_markers(fig_paths, contribution_marker_year, withdrawal_marker_year, supplemental_marker_year)
    fig_paths.update_layout(showlegend=False)
    st.plotly_chart(fig_paths, use_container_width=True)

st.divider()

# Downloads
colA, colB = st.columns(2)
csv_nom = summary_nom.to_csv(index=False).encode("utf-8")
csv_real = summary_real.to_csv(index=False).encode("utf-8")
with colA:
    st.download_button("Download summary (Nominal $)", data=csv_nom, file_name="summary_nominal.csv", mime="text/csv")
with colB:
    st.download_button("Download summary (Real $)", data=csv_real, file_name="summary_real.csv", mime="text/csv")

# Methodology
with st.expander("Methodology"):
    st.markdown(
        """
        This tool runs a Monte Carlo simulation of portfolio growth under user-specified assumptions.
        Each simulation samples annual returns from the selected distribution, applies contributions
        (with optional growth), deducts expenses, and applies withdrawals when configured.

        **Key assumptions:**
        - Returns are independent year-to-year (no serial correlation)
        - Contributions and withdrawals occur at the specified timing within each year
        - Expense ratio is deducted annually from portfolio value
        - Inflation adjustment uses a constant annual rate for real-dollar conversion
        - The regime-t model calibrates ordinary-year returns so the long-run expectation matches the user's input

        Results show the distribution of outcomes across all simulations — not a single forecast.
        The 10th-90th percentile band captures the middle 80% of outcomes.
        """
    )
