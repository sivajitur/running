# 🏃 Running Analytics + AI Marathon Coach

<img width="1862" height="994" alt="Screenshot 2026-06-15 at 9 42 13 PM" src="https://github.com/user-attachments/assets/55faa579-5584-4ae0-97c0-b99e25ce277a" />


This project pulls your running data from the Strava API, stores it locally, visualizes it in a clean Streamlit dashboard, and — the fun part — exposes it to AI as a set of [Model Context Protocol (MCP)](https://modelcontextprotocol.io) tools. 

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-server-000000">
  <img alt="Strava" src="https://img.shields.io/badge/Strava-API-FC4C02?logo=strava&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-persistence-003B57?logo=sqlite&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

<!--
  📸 SCREENSHOT: drop a dashboard image at docs/dashboard.png, then delete this
  comment and uncomment the line below. (Drag-and-drop into the GitHub README
  editor also works and will auto-upload the image.)
-->
<!-- <p align="center"><img src="docs/dashboard.png" alt="Running Analytics dashboard" width="800"></p> -->

---

## ✨ What makes this interesting

Most Strava projects stop at a dashboard. This one does two things well:

1. **A polished analytics dashboard** — OAuth login, interactive Plotly charts, and filtering across your entire running history.
2. **An MCP server that makes your data conversational** — instead of reading charts, you *ask questions*. The MCP server gives Claude (or any MCP client) typed tools to query your runs, so the AI grounds every answer in your real numbers instead of guessing.

The codebase is intentionally built like production software: a layered architecture, OAuth with automatic token refresh, a SQLite persistence layer, and a clean separation between data, analysis, and UI.

---

## 🎬 Two ways to use it

### 1. The Streamlit dashboard

```bash
streamlit run app.py
```

- 🔐 **One-click Strava OAuth** — log in with your own Strava account; tokens refresh automatically
- 📈 **Distance over time** — grouped by day, week, or month
- 🗓️ **Day-of-week analysis** — find out which days you actually train
- 📋 **Sortable run log** with pace, heart rate, and elevation — exportable to CSV
- 📉 **Distribution & heart-rate-vs-distance** scatter plots
- 💬 **In-app AI coaching tab** that answers questions using your data as context

### 2. The MCP server (the cool part)

Add the server to Claude Desktop and your running history becomes a set of tools the model can call:

| Tool | What it does |
|------|--------------|
| `sync_from_strava` | Pull the latest activities from Strava into the local DB |
| `get_recent_runs` | Most recent runs with pace, HR, and elevation |
| `get_runs_in_range` | Every run between two dates |
| `get_long_runs` | Runs over a distance threshold — track long-run progression |
| `get_run_detail` | Full splits, cadence, calories, and suffer score for one run |
| `get_training_summary` | Total mileage, average pace, and heart-rate trends |
| `get_weekly_mileage_trend` | Week-by-week mileage to judge ramp rate and taper |
| `get_db_status` | How much data is stored and how fresh it is |

Now you can ask Claude things like:

> *"Compare my average pace over the last 4 weeks to the month before — am I getting faster?"*
> *"Is my weekly mileage ramping too aggressively for a March marathon?"*
> *"Pull my longest run this month and break down the splits."*

Claude calls the tools, reads your real data, and coaches you on it.

---

## 🏗️ Architecture

A clean, layered design with one-directional dependencies — easy to extend (swap Strava for Garmin, add a new chart, plug in a different AI provider).

```
running_mcp/
├── app.py                  # Streamlit entry point
├── mcp_server.py           # MCP server — exposes running data as AI tools
└── src/
    ├── config/             # Centralized settings & env/secrets handling
    ├── auth/               # Strava OAuth handler + token model
    ├── data/
    │   ├── strava_client.py    # Strava API client (pagination, refresh)
    │   ├── database.py         # SQLite persistence layer
    │   └── data_processor.py   # Unit conversions, DataFrame & exports
    ├── analysis/
    │   ├── analyzer.py         # Stats, filtering, weekly aggregation
    │   └── ai_client.py        # AI coaching client + context builder
    └── ui/
        ├── app.py              # Dashboard orchestration
        ├── pages/auth.py       # Login flow
        └── components/         # metrics, charts, AI tab
```

**Highlights for the curious:**
- **OAuth done right** — authorization-code flow, token persistence, and automatic refresh when the access token expires.
- **Local-first persistence** — activities are upserted into SQLite so the dashboard loads instantly and the MCP server works offline between syncs.
- **Typed MCP tools** — built on `FastMCP`, each tool has a docstring the model reads to decide when and how to call it.

---

## 🚀 Quick start

```bash
# 1. Clone & install
git clone https://github.com/sivajitur/running.git
cd running
pip install -r requirements.txt

# 2. Add your Strava credentials (see below)
cp .env.example .env        # then edit .env

# 3. Run the dashboard
streamlit run app.py        # → http://localhost:8501
```

### Get Strava API credentials

1. Go to <https://www.strava.com/settings/api>
2. **Create New App** → set the Authorization Callback Domain to `localhost`
3. Copy your **Client ID** and **Client Secret** into `.env`:

```env
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
PERPLEXITY_API_KEY=your_api_key   # optional — powers the in-app coaching tab
```

> Prefer Streamlit secrets? Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` instead — no code changes needed.

### Connect the MCP server to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "marathon-coach": {
      "command": "python",
      "args": ["/absolute/path/to/running/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, then ask it about your training. It will call `sync_from_strava` and the query tools automatically.

---

## 🛠️ Tech stack

| Layer | Tools |
|-------|-------|
| Language | Python 3.10+ |
| Dashboard | Streamlit, Plotly, pandas |
| Data source | Strava REST API (OAuth 2.0) |
| Persistence | SQLite |
| AI / agents | Model Context Protocol (FastMCP), Perplexity |

---

## 🔒 Security & privacy

- Secrets live in `.env` / `.streamlit/secrets.toml` — both gitignored, never committed.
- Your activity data (`running.db`, exports) is gitignored and stays on your machine.
- OAuth tokens refresh automatically and are never written to the repo.

---

## 📄 License

MIT — see below. Built as a portfolio project to explore Strava data, MCP tooling, and clean Python architecture.
