# CGL Record Book

The official historical record for **CGL — Charley’s Gonna Lose**, a 14-team PPR fantasy football league. [View the public record book](https://cjkelley01.github.io/CGL-Record-Book/).

Official statistics begin with the **2024 season**. Earlier stories belong to **League Legend** and are excluded from official calculations. The ESPN league ID is `1877457250`. This project is independent from Fantasy Football Edge.

## What’s in the record book

- Current-season results, standings, champions, playoff brackets, and season archives
- Manager profiles, head-to-head matchups, draft history, and all-time records
- League analytics, including all-play records, schedule luck, and power rankings
- Moves That Mattered, which measures transaction impact using points scored in starting lineups
- Playoff, bye, finalist, and championship probabilities from the saved forecast

Overview is the landing page and appears above the Season, History, and Analytics groups. Use the sidebar on desktop or open **Menu** on a smaller screen.

The URL saves the selected section and filters, so you can share a specific season, matchup, manager, or draft view. Use a link from the published site when sharing with the league. Underlined team names open the manager profile for that season’s owner. Shared teams open the first listed owner.

## Run the website locally

Install Node.js 22.13 or newer and Corepack. The repository pins pnpm to 11.19.0. GitHub Actions uses Node.js 22. On Windows, if `corepack.cmd` is missing, install Corepack with `npm.cmd install --global corepack`. Open a new terminal after installing Node.js if `node --version` is unavailable.

```powershell
git clone https://github.com/cjkelley01/CGL-Record-Book.git
cd CGL-Record-Book
corepack.cmd pnpm install --frozen-lockfile
corepack.cmd pnpm dev
```

Use `corepack` in place of `corepack.cmd` on macOS and Linux. The website uses committed data, so local development needs only the JavaScript dependencies. Python and ESPN credentials are for refreshing the data.

| Task | Windows PowerShell command |
| --- | --- |
| Develop with live reload | `corepack.cmd pnpm dev` |
| Build and preview the production site | `corepack.cmd pnpm preview` |
| Build static files in `dist-pages/` | `corepack.cmd pnpm build` |
| Check TypeScript | `corepack.cmd pnpm typecheck` |
| Run ESLint | `corepack.cmd pnpm lint` |
| Run Python regression tests | `.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v` |

Vite uses `/CGL-Record-Book/` locally and on GitHub Pages. Development defaults to port 5173 and production preview to 4173. Both commands open the browser automatically. Press **Ctrl+C** to stop the server. For a browser-free run, use `node scripts/website.mjs dev --no-open` or `node scripts/website.mjs preview --no-open`. The preview rebuilds on startup. `start` is a preview alias and `build:pages` is a build alias.

## Refresh ESPN data locally

GitHub Actions uses Python 3.13 for season refreshes and Python 3.12 for regression tests. Create a local environment and install dependencies in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS and Linux, use `python3 -m venv .venv` and substitute `.venv/bin/python` in the commands below.

For a private league, set `ESPN_S2` and `ESPN_SWID` in the environment or the ignored `.env` file. The local ESPN discovery script also accepts `SWID` as an alias. Set the exact names `ESPN_S2` and `ESPN_SWID` as repository secrets for GitHub Actions. Keep credential values outside Git.

On a fresh checkout, download the three official seasons before rebuilding the site data. The raw archive is excluded from Git.

```powershell
.\.venv\Scripts\python.exe scripts/discover_espn_history.py --seasons 2024 2025 2026
.\.venv\Scripts\python.exe scripts/build_core_history.py
```

Check `data/reports/espn_history_discovery.json` for failed requests before rebuilding. ESPN endpoints are unofficial and a successful response can still lack the historical fields a calculation needs.

After the initial archive download, use the updater for routine local results:

```powershell
.\.venv\Scripts\python.exe scripts/update_current_season.py
```

The updater downloads 2026 data, stops if acquisition fails, and rebuilds all three seasons into `app/data/core_history.json`. It reports the last completed week. For the full refresh, including the playoff forecast, use the GitHub Actions workflow below.

## Publish and maintain the site

| Workflow | What it does |
| --- | --- |
| [Validate CGL Record Book](.github/workflows/validate.yml) | Runs Python regression tests, TypeScript checks, ESLint, and the Vite build on pushes and PRs targeting `main`. |
| [Deploy CGL Record Book](.github/workflows/deploy-pages.yml) | Publishes `dist-pages/` to GitHub Pages after a push to `main` or a successful season refresh. Also supports manual runs. |
| [Refresh 2026 Season](.github/workflows/refresh-season.yml) | Runs Tuesdays at 11 a.m. Eastern, on relevant pipeline changes to `main`, or on demand. Fetches the archive, NFL schedule, and waiver projections, checks lineup coverage, rebuilds results and forecasts, and commits eligible updates. |

For a manual local results update, preview the site and check `git status`, then stage `app/data/core_history.json` explicitly. Published datasets live in `app/data/`. Forecast snapshots in `data/forecasts/` and the two aggregate projection coverage reports in `data/reports/` are also tracked. Raw ESPN responses and other local reports stay out of Git.

## Forecasts and research

The forecast compares historical scoring, ESPN roster-aware projections, and a blend of 40% historical scoring and 60% roster projections. The production model carries the last remaining regular-season roster estimate into the playoff weeks. The six-team playoff bracket has two byes, fixed semifinal pairings, and a two-week final. If roster-aware or blended projections are unavailable during refresh, the workflow keeps the previously published forecast. The forecast’s completed-through week can therefore lag behind the results.

- To investigate a held forecast, check the [projection coverage report](data/reports/forecast_projection_coverage.json) and [lineup readiness report](data/reports/lineup_projection_readiness.json).
- [Export playoff-week team projections](.github/workflows/export-playoff-projections.yml) runs on demand and uploads a separate Weeks 15–18 team-level artifact.
- The [future-projection diagnostic](.github/workflows/diagnose-espn-future-projections.yml) inspects ESPN’s response. The [branch-selectable probe](.github/workflows/manual-espn-projection-probe.yml) supports research against a specific ref.
- Historical audits, backtests, and [season replay](.github/workflows/historical-season-replay.yml) are manual research runs. Retrospective ESPN projections may have changed since game time, so replay results should not be treated as verified pregame forecasts.

## Project guides

- [Backlog](docs/backlog.md) for proposed changes and priorities
- [Repository structure](docs/repository-structure.md) for the frontend and Python pipeline
- [Record-book scope](docs/record-book-scope.md) for historical boundaries and verification rules
- [Moves That Mattered](docs/moves-that-mattered.md) for transaction methodology
- [Analytics roadmap](docs/analytics-roadmap.md) and [historical ESPN availability audit](docs/historical-espn-availability-audit.md) for research context
