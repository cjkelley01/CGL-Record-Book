# CGL Record Book

The official historical record for **CGL — Charley’s Gonna Lose**, a 14-team PPR fantasy football league.

## Official history

- Official statistical history begins with the **2024 season**.
- Earlier stories may be preserved as **League Legend**, but are not included in official all-time calculations.
- ESPN league ID: `1877457250`
- This project is independent from Fantasy Football Edge.

## Current milestone: browsable record book

The project preserves ESPN history, builds a public-safe normalized dataset, and presents it in a local web record book. Raw responses remain unchanged so every calculation can be audited.

## Quick start

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\discover_espn_history.py
python scripts\build_core_history.py
```

On macOS or Linux, activate with `source .venv/bin/activate` and use forward slashes.

The discovery script writes:

- `data/raw/<season>/league/<view>.json`
- `data/raw/<season>/weeks/<week>/<view>.json`
- `data/reports/espn_history_discovery.json`
- `data/reports/espn_history_discovery.md`

Raw downloads are intentionally excluded from Git because ESPN responses can be large. The generated report is also local until reviewed for personal information.

## Run the website locally

Install Node.js 22 or newer, then run:

```powershell
corepack enable
pnpm install
pnpm dev
```

Open the local address shown in the terminal. Re-running `build_core_history.py` updates both the private processed file and the website's local data.

## Update the current season

From PowerShell, refresh ESPN results and rebuild the entire record book with one command:

```powershell
.\update-record-book.cmd
```

The updater stops if any ESPN request fails, so incomplete downloads cannot silently replace the site data. When it finishes, it reports the latest completed week. Starting the website remains a separate command:

```powershell
corepack pnpm dev
```

The generated `app/data/core_history.json` is public-safe website data and should be committed after a successful update. GitHub Pages automatically rebuilds and publishes the site whenever `main` receives a push.

```powershell
.\update-record-book.cmd
git add app\data\core_history.json
git commit -m "Update 2026 results"
git push
```

GitHub Actions handles the website build and deployment after the push.

## Roadmap

1. Historical ESPN discovery and preservation
2. Normalized managers, franchises, seasons, matchups, standings, rosters, drafts, and transactions
3. Verified regular-season and playoff calculations
4. All-time records, head-to-head history, streaks, awards, and season recaps
5. A browsable CGL record-book website — initial version complete

## Data caution

ESPN's fantasy endpoints are unofficial and can change. A successful HTTP response does not prove that a view contains useful historical data, so the discovery report records both availability and top-level structure. Private leagues may require `ESPN_S2` and `SWID` environment variables; never commit those values.
