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
    seed: int | None = 42,
    distribution: str = "normal",  # 'normal', 't-distribution', 'mixture'
    t_df: float = 5.0,  # degrees of freedom for t-distribution
    crash_prob_pct: float = 10.0,  # probability of crash year (mixture model)
    crash_mean_pct: float = -20.0,  # mean return in crash year
    crash_std_pct: float = 25.0,  # volatility in crash year
):
    """Return a (n_sims x (years+1)) array of portfolio values by year.

    Returns both nominal and real (inflation-adjusted) matrices.

    Distribution options:
    - 'normal': Standard normal distribution (may underestimate tail risk)
    - 't-distribution': Student's t with fatter tails (df controls tail thickness)
    - 'mixture': Normal most years, but crash_prob% chance of crash regime
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

    # Precompute contributions each year (nominal)
    contribs = np.array([(annual_contribution * ((1 + cg) ** t)) for t in range(years)], dtype=float)

    # Draw annual returns based on distribution type
    if distribution == "t-distribution":
        # Student's t-distribution: fatter tails than normal
        # Scale t samples to have desired mean and std
        t_samples = rng.standard_t(df=t_df, size=(n_sims, years))
        # Adjust variance: Var(t) = df/(df-2) for df > 2
        if t_df > 2:
            scale_factor = np.sqrt((t_df - 2) / t_df)
        else:
            scale_factor = 1.0
        rets = mu + sigma * t_samples * scale_factor
    elif distribution == "mixture":
        # Mixture model: normal most years, crash distribution some years
        crash_prob = crash_prob_pct / 100.0
        crash_mu = crash_mean_pct / 100.0
        crash_sigma = crash_std_pct / 100.0

        # Draw from normal distribution
        rets = rng.normal(loc=mu, scale=sigma, size=(n_sims, years))

        # Determine which years are crash years
        is_crash = rng.random(size=(n_sims, years)) < crash_prob

        # Replace crash years with draws from crash distribution
        crash_rets = rng.normal(loc=crash_mu, scale=crash_sigma, size=(n_sims, years))
        rets = np.where(is_crash, crash_rets, rets)
    else:  # normal
        rets = rng.normal(loc=mu, scale=sigma, size=(n_sims, years))
    # Apply expense drag multiplicatively
    rets_net = (1 + rets) * (1 - er) - 1

    # Allocate array for balances
    bal = np.zeros((n_sims, years + 1), dtype=float)
    bal[:, 0] = initial_amount

    for t in range(years):
        if contribution_timing == "start":
            bal[:, t] = bal[:, t] + contribs[t]
            bal[:, t + 1] = bal[:, t] * (1 + rets_net[:, t])
        else:  # end
            bal[:, t + 1] = bal[:, t] * (1 + rets_net[:, t]) + contribs[t]

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
