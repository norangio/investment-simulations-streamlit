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
