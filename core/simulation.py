import numpy as np
import pandas as pd


def simulate_paths(
    initial_amount: float,
    annual_contribution: float,
    years: int,
    mean_return_pct: float,
    std_return_pct: float,
    n_sims: int,
    contrib_growth_pct: float = 0.0,
    expense_ratio_pct: float = 0.0,
    inflation_pct: float = 0.0,
    contribution_timing: str = "start",  # 'start' or 'end'
    contribution_stop_year: int | None = None,
    annual_withdrawal: float = 0.0,
    withdrawal_start_year: int = 1,
    withdrawal_growth_pct: float = 0.0,
    seed: int | None = 42,
    distribution: str = "regime-t",  # 'regime-t', 'normal', 't-distribution', 'mixture'
    t_df: float = 5.0,  # degrees of freedom for t-distribution
    crash_prob_pct: float = 8.0,  # probability of crash year (regime models)
    crash_mean_pct: float = -24.0,  # mean return in crash year
    crash_std_pct: float = 25.0,  # volatility in crash year
):
    """Return a (n_sims x (years+1)) array of portfolio values by year.

    Returns both nominal and real (inflation-adjusted) matrices.

    Distribution options:
    - 'regime-t': Student's t ordinary years plus random crash years
    - 'normal': IID normal annual returns (simple baseline)
    - 't-distribution': IID Student's t annual returns
    - 'mixture': IID normal ordinary years plus random crash years
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    mu = mean_return_pct / 100.0
    sigma = std_return_pct / 100.0
    er = expense_ratio_pct / 100.0
    infl = inflation_pct / 100.0
    cg = contrib_growth_pct / 100.0
    wg = withdrawal_growth_pct / 100.0

    # Precompute contributions each year (nominal)
    contribs = np.array([(annual_contribution * ((1 + cg) ** t)) for t in range(years)], dtype=float)
    if contribution_stop_year is not None:
        stop_year = max(0, min(int(contribution_stop_year), years))
        contribs[stop_year:] = 0.0

    withdrawals = np.zeros(years, dtype=float)
    if annual_withdrawal > 0:
        start_year = max(1, min(int(withdrawal_start_year), years))
        for year in range(start_year, years + 1):
            withdrawals[year - 1] = annual_withdrawal * ((1 + wg) ** (year - start_year))

    def draw_t_returns(loc: float, scale: float, size: tuple[int, int]) -> np.ndarray:
        t_samples = rng.standard_t(df=t_df, size=size)
        if t_df > 2:
            scale_factor = np.sqrt((t_df - 2) / t_df)
        else:
            scale_factor = 1.0
        return loc + scale * t_samples * scale_factor

    # Draw annual returns based on distribution type
    if distribution in {"regime-t", "mixture"}:
        crash_prob = crash_prob_pct / 100.0
        crash_mu = crash_mean_pct / 100.0
        crash_sigma = crash_std_pct / 100.0
        calm_mu = (mu - crash_prob * crash_mu) / (1 - crash_prob) if crash_prob < 1 else mu

        if distribution == "regime-t":
            rets = draw_t_returns(calm_mu, sigma, (n_sims, years))
            crash_rets = draw_t_returns(crash_mu, crash_sigma, (n_sims, years))
        else:
            rets = rng.normal(loc=calm_mu, scale=sigma, size=(n_sims, years))
            crash_rets = rng.normal(loc=crash_mu, scale=crash_sigma, size=(n_sims, years))

        is_crash = rng.random(size=(n_sims, years)) < crash_prob
        rets = np.where(is_crash, crash_rets, rets)
    elif distribution == "t-distribution":
        rets = draw_t_returns(mu, sigma, (n_sims, years))
    else:  # normal
        rets = rng.normal(loc=mu, scale=sigma, size=(n_sims, years))
    rets = np.clip(rets, -0.99, None)

    # Apply expense drag multiplicatively
    rets_net = (1 + rets) * (1 - er) - 1

    # Allocate array for balances
    bal = np.zeros((n_sims, years + 1), dtype=float)
    bal[:, 0] = initial_amount

    for t in range(years):
        if contribution_timing == "start":
            starting_balance = bal[:, t] + contribs[t]
            bal[:, t + 1] = starting_balance * (1 + rets_net[:, t])
        else:  # end
            bal[:, t + 1] = bal[:, t] * (1 + rets_net[:, t]) + contribs[t]
        if withdrawals[t] > 0:
            bal[:, t + 1] = np.maximum(bal[:, t + 1] - withdrawals[t], 0.0)

    # Real terms (deflate by cumulative inflation)
    infl_index = np.array([(1 + infl) ** t for t in range(years + 1)], dtype=float)
    bal_real = bal / infl_index

    return bal, bal_real


def summarize_paths(bal: np.ndarray) -> pd.DataFrame:
    years = bal.shape[1] - 1
    percentiles = [10, 25, 50, 75, 90]
    pct = np.percentile(bal, q=percentiles, axis=0)
    mean = bal.mean(axis=0)

    df = pd.DataFrame({
        "Year": np.arange(0, years + 1),
        "Mean": mean,
        "P10": pct[0, :],
        "P25": pct[1, :],
        "P50": pct[2, :],
        "P75": pct[3, :],
        "P90": pct[4, :],
    })
    return df
