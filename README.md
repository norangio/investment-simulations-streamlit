# Monte Carlo Investment Planner (Streamlit)

A Streamlit app for Monte Carlo portfolio simulations with interactive controls, percentile bands, and CSV exports.

This repo contains only the Streamlit dashboard and simulation engine from the original `investment-simulations` project (no Chainlit/LLM code).

## Features

- Portfolio growth simulation with yearly contributions
- Return model options: normal, Student's t, and crash-regime mixture
- Inflation-adjusted and nominal views
- Goal probability tracking
- Interactive Plotly charts and CSV downloads

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
