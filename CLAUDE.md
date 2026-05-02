# Project: Investment Simulations (Streamlit)

## Scope

This repository contains only the Streamlit dashboard and simulation engine.

- `streamlit_app.py` — Streamlit UI and charts
- `core/simulation.py` — Monte Carlo simulation and summary logic

The chatbot/LLM functionality is intentionally excluded.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deployment

- Host: Hetzner VPS
- Domain: `investment-sim.norangio.dev`
- Reverse proxy/TLS: Caddy
- Process manager: systemd (`investment-simulations-streamlit`)
- CI/CD: GitHub Actions (`.github/workflows/deploy.yml`)

Deployment flow:

1. Push to `main`
2. GitHub Action SSHes to VPS
3. Repo syncs to `/opt/investment-simulations-streamlit`
4. `deploy/server-deploy.sh` installs deps and restarts service

## Notes

- Streamlit binds to `127.0.0.1:8501`
- Caddy reverse proxies public traffic to the app

## Simulation Model Notes

- Default return sampling is `regime-t`: Student's t ordinary years plus random crash years. The ordinary-year return mean is calibrated so the user-entered expected return remains the long-run target after crash years.
- `normal` is kept as a simple IID baseline, not the preferred modeling default.
- Contributions can stop before the horizon. `Last contribution year = 10` means contributions are made through Year 10, then stop before Year 11.
- Withdrawals are optional, begin in a user-selected simulation year, are applied at year end, and floor balances at zero when depleted.
- Charts show timing markers for contribution stops and withdrawal starts when those events apply.
- Deferred audit items: explicit asset allocation, asset correlations, rebalancing, stochastic inflation, historical bootstrap/stress tests, taxes/account types/RMDs, income sources, uncertainty around capital market assumptions, and dynamic withdrawal rules.
