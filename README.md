# CGL Record Book

The official historical record for **CGL — Charley’s Gonna Lose**, a 14-team PPR fantasy football league.

## Official history

- Official statistical history begins with the **2024 season**.
- Earlier stories may be preserved as **League Legend**, but are not included in official all-time calculations.
- ESPN league ID: `1877457250`
- This project is independent from Fantasy Football Edge.

## Current milestone: preserve the source data

Before building leaderboards, records, and season stories, this project downloads and preserves every historical ESPN view that is still available for 2024 and 2025. Raw responses remain unchanged so later calculations can be audited.

## Quick start

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\discover_espn_history.py
```

On macOS or Linux, activate with `source .venv/bin/activate` and use forward slashes.

The discovery script writes:

- `data/raw/<season>/league/<view>.json`
- `data/raw/<season>/weeks/<week>/<view>.json`
- `data/reports/espn_history_discovery.json`
- `data/reports/espn_history_discovery.md`

Raw downloads are intentionally excluded from Git because ESPN responses can be large. The generated report is also local until reviewed for personal information.

## Roadmap

1. Historical ESPN discovery and preservation
2. Normalized managers, franchises, seasons, matchups, standings, rosters, drafts, and transactions
3. Verified regular-season and playoff calculations
4. All-time records, head-to-head history, streaks, awards, and season recaps
5. A browsable CGL record-book website

## Data caution

ESPN's fantasy endpoints are unofficial and can change. A successful HTTP response does not prove that a view contains useful historical data, so the discovery report records both availability and top-level structure. Private leagues may require `ESPN_S2` and `SWID` environment variables; never commit those values.
