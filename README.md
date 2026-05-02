# Monte Carlo Investment Planner (Streamlit)

A Streamlit app for Monte Carlo portfolio simulations with interactive controls, percentile bands, and CSV exports.

This repo contains only the Streamlit dashboard and simulation engine from the original `investment-simulations` project (no Chainlit/LLM code).

## Features

- Portfolio growth simulation with yearly contributions
- Return model options: regime-aware fat tails, normal IID, Student's t IID, and crash-regime mixture
- Inflation-adjusted and nominal views
- Optional contribution stop year
- Optional yearly withdrawals starting in a chosen year
- Chart markers for contribution-stop and withdrawal-start timing
- Goal probability tracking
- Interactive Plotly charts and CSV downloads

## Modeling notes

The default return model is `Regime-aware fat tails (recommended)`. It uses Student's t ordinary-year returns plus randomly occurring crash years. The ordinary-year mean is calibrated so the user-entered expected annual return remains the long-run target after accounting for crash years. This is intended to be a more realistic educational default than IID normal sampling while still keeping the model transparent.

Contributions can be stopped before the end of the simulation by setting `Last contribution year`. A value of 10 means contributions are made through Year 10, then stop before Year 11.

Withdrawals are applied at the end of each selected simulation year and balances are floored at zero when depleted. If withdrawals are enabled, the app also runs the same simulation settings without withdrawals so the median withdrawal impact can be shown using the same random seed. The charts show timing markers when contributions stop before the horizon or withdrawals begin.

Known limitations from the statistical audit that are intentionally not implemented yet:

- Single blended portfolio return instead of explicit asset allocation.
- No asset correlations, covariance matrix, or rebalancing logic.
- Deterministic inflation rather than stochastic inflation.
- No taxes, account types, RMDs, Social Security, pensions, or other income sources.
- No historical bootstrap or historical stress-scenario engine.
- No uncertainty model around the expected return, volatility, or inflation inputs.
- No dynamic retirement spending rules such as guardrails or probability-based spending adjustments.

## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open: `http://localhost:8501`

## Deploy (VPS + GitHub Actions)

On push to `main`, GitHub Actions deploys to the VPS using the same pattern as other norangio.dev apps.

### Required GitHub Actions secrets

- `VPS_HOST` (example: `5.78.109.38`)
- `VPS_USER` (example: `root`)
- `VPS_SSH_KEY` (private key with access to the VPS)

### One-time VPS setup

1. Add the domain A record in Cloudflare:
   - `investment-sim.norangio.dev -> <your-vps-ip>`
2. Add the Caddy block from `deploy/Caddyfile.snippet` to `/etc/caddy/Caddyfile`
3. Reload Caddy:
   - `sudo systemctl reload caddy`

The deploy workflow manages `/opt/investment-simulations-streamlit`, installs dependencies, and restarts the `investment-simulations-streamlit` systemd service.

## Project structure

```text
core/
  simulation.py                 # Monte Carlo engine
streamlit_app.py               # Streamlit UI
deploy/
  server-deploy.sh             # Runs on VPS
  investment-simulations-streamlit.service
  Caddyfile.snippet
.github/workflows/deploy.yml   # Auto-deploy on push to main
```
