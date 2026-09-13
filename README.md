# CGL Record Book

The official historical record for **CGL — Charley’s Gonna Lose**, a 14-team PPR fantasy football league.

## Official history

- Official statistical history begins with the **2024 season**.
- Earlier stories may be preserved as **League Legend**, but are not included in official all-time calculations.
- ESPN league ID: `1877457250`
- This project is independent from Fantasy Football Edge.

## Current milestone: browsable record book

The project preserves ESPN history, builds a public-safe normalized dataset, and presents it in a local web record book. Raw responses remain unchanged so every calculation can be audited.

## Set up the repository

Follow these steps in order on Windows. All commands below are entered in PowerShell.

1. **Get the repository.** If you already have this folder open in your editor, skip this step. Otherwise, with Git installed, run:

   ```powershell
   git clone https://github.com/cjkelley01/CGL-Record-Book.git
   cd CGL-Record-Book
   ```

2. **Open a terminal in the repository folder.** In your editor, choose **Terminal → New Terminal**. Confirm that you are in the right folder:

   ```powershell
   Get-Location
   Test-Path package.json
   ```

   The second command should print `True`. If needed, use `cd "C:\path\to\CGL-Record-Book"`, replacing the example with your actual folder path.

3. **Install or locate Node.js.** Follow [One-time website setup](#one-time-website-setup) below, including the PATH troubleshooting steps if `node --version` is not recognized.
4. **Install the website dependencies**, then start the local website:

   ```powershell
   corepack.cmd pnpm install --frozen-lockfile
   corepack.cmd pnpm dev
   ```

   Wait for installation to finish successfully before running the second command. Keep the terminal open while using the website; press **Ctrl+C** to stop it.

5. **Optional: set up ESPN updates.** Follow [One-time data-update setup](#one-time-data-update-setup) to install Python dependencies and download the historical archive. You can skip this when viewing or editing the website using its saved data.

The `.cmd` suffix on `corepack.cmd` runs the installed Windows command directly and avoids PowerShell script execution-policy issues. It is not a repository shortcut. On macOS/Linux, use `corepack` instead.

## Everyday commands

Run these commands from a terminal in the repository folder.

| Task | Command |
| --- | --- |
| Open the website while editing | `corepack pnpm dev` |
| Build and preview before publishing | `corepack pnpm preview` |
| Refresh current-season ESPN results locally | `.\.venv\Scripts\python.exe scripts/update_current_season.py` (after data setup) |
| Check TypeScript | `corepack pnpm typecheck` |
| Check code style and common errors | `corepack pnpm lint` |
| Build without opening a browser | `corepack pnpm build` |
| Reinstall website dependencies after dependency changes | `corepack pnpm install --frozen-lockfile` |


## One-time website setup

**22.13 is the minimum version, not an exact version you need to find.** A newer LTS release is suitable.

On Windows:

1. Visit the [official Node.js download page](https://nodejs.org/en/download).
2. Select an **LTS** release, **Windows**, and **Windows Installer (.msi)**. Choose **x64** for a typical Intel/AMD PC, or **ARM64** for an ARM-based PC.
3. Run the downloaded installer. Keep the default Node.js, npm, and **Add to PATH** options enabled.
4. Close and reopen your editor completely, then open a new PowerShell terminal. This lets the editor pick up the updated PATH.
5. Check the installation:

```powershell
node --version
npm.cmd --version
```

If `node` is not recognized, check whether it is already installed at the standard location:

```powershell
& "C:\Program Files\nodejs\node.exe" --version
```

If that works, Node.js is installed but your terminal cannot find it. Restart your editor first. To make it available immediately in the current PowerShell session, run:

```powershell
$env:Path = "C:\Program Files\nodejs;" + $env:Path
```

For a permanent PATH fix, search Windows Start for **Edit environment variables for your account**. Under **User variables**, select **Path → Edit → New**, add `C:\Program Files\nodejs`, and click **OK** to save. Completely close and reopen your editor afterward. If the executable does not exist, follow the installation steps above.

Once `node --version` works, run this from the repository folder:

```powershell
node --version
corepack.cmd pnpm install --frozen-lockfile
```

If `corepack.cmd` is not recognized but Node.js and npm work, run `npm.cmd install --global corepack`, then retry. A separate global pnpm installation or `corepack enable` is not required when using `corepack pnpm`. On macOS/Linux, omit the `.cmd` suffixes.

You can now run `corepack pnpm dev`. The repository includes saved website data, so **Python and ESPN downloads are not required just to view or edit the website**.

## One-time data-update setup

Only needed if you want to fetch fresh ESPN results on your computer. Install Python 3.10 or newer, then run these commands in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No Python environment activation is required. Next, download the historical archive. Wait for this command to finish successfully before continuing:

```powershell
.\.venv\Scripts\python.exe scripts/discover_espn_history.py --seasons 2024 2025 2026
```

If it reports failed requests, fix the issue and rerun it. After a successful download, rebuild the website data:

```powershell
.\.venv\Scripts\python.exe scripts/build_core_history.py
```

This initial archive download is required because raw files are excluded from Git. The current-season updater downloads **2026 only**, while rebuilding uses **2024, 2025, and 2026**. It does not bootstrap the older seasons on a fresh clone.

On macOS/Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe` for the remaining Python commands.

Raw responses are saved under `data/raw/`; download reports are in `data/reports/`. Both are local and excluded from Git. The generated `app/data/core_history.json` is the website dataset and is committed when publishing data changes.

## Preview before publishing

Complete the website setup above first. No database or hosting account is needed for local preview.

For live editing with automatic browser updates:

```sh
corepack pnpm dev
```

For a fresh production build and local preview before publishing:

```sh
corepack pnpm preview
```

Keep the terminal open while using either preview. Press Ctrl+C to stop it. Both commands open your browser automatically. Development normally uses port 5173; production preview uses 4173. Vite chooses an available port if either is busy.

Both previews use `/CGL-Record-Book/`, the same base path as GitHub Pages. Neither command pushes commits or deploys the site. Production preview rebuilds each time it starts; restart it after further edits. Use the live preview for continuous editing.

Before publishing, run:

```sh
corepack pnpm typecheck
corepack pnpm lint
corepack pnpm preview
```

Review the production preview, then commit and push when ready. `pnpm build` and the compatibility alias `pnpm build:pages` both generate `dist-pages/` using the same Vite configuration as deployment.

## Update the current season

After completing the data-update setup, run this in PowerShell to refresh 2026 results and rebuild the record book:

```powershell
.\.venv\Scripts\python.exe scripts/update_current_season.py
```

The updater stops if any ESPN request fails, so incomplete downloads cannot silently replace the site data. When it finishes, it reports the latest completed week. Starting the website remains a separate command:

```powershell
corepack pnpm dev
```

If the live preview is already open, it should reload the updated data; restart production preview to rebuild its saved output. On macOS/Linux, use `.venv/bin/python scripts/update_current_season.py` to update results.

## Publish changes

Updating data or opening a preview only changes your local copy. Review the production preview before publishing.

The generated `app/data/core_history.json` is public-safe website data and should be committed after a successful update. GitHub Pages automatically rebuilds and publishes the site whenever `main` receives a push.

For a data-only update, after checking the preview:

```powershell
git status
git add app\data\core_history.json
git commit -m "Update 2026 results"
git push
```

The example above stages only the dataset. For code or styling changes, also stage the specific changed files you intend to publish. A push to `main` triggers deployment; work on another branch if you want to push work without publishing it. GitHub Actions handles the website build and deployment after the push to `main`.

The `Refresh 2026 Season` workflow also runs automatically every Tuesday at 11:00 AM Eastern. It downloads a fresh copy of all three official seasons, rebuilds the data, commits any changes, and deploys the site. It can be started manually from the repository's Actions tab at any time.

## Other useful commands

- `corepack pnpm start` is an alias for the production-preview command and rebuilds before serving.
- `corepack pnpm build:pages` is an alias for `corepack pnpm build`.
- `node scripts/website.mjs dev --no-open` or `node scripts/website.mjs preview --no-open` starts a preview without automatically opening the browser.
- `.\.venv\Scripts\python.exe scripts/build_core_history.py` rebuilds records from the existing archive. Missing draft-player details may still require ESPN lookups.
- `.\.venv\Scripts\python.exe scripts/discover_espn_history.py --help` and `.\.venv\Scripts\python.exe scripts/update_current_season.py --help` show advanced options. The default updater targets 2026; changing to a future season also requires reviewing the builder's season list and identity mappings.
- Rerun `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` after Python dependency changes.

## Roadmap

See [Repository structure](docs/repository-structure.md) for the code layout, data pipeline, build paths, and further cleanup candidates.

1. Historical ESPN discovery and preservation
2. Normalized managers, franchises, seasons, matchups, standings, rosters, drafts, and transactions
3. Verified regular-season and playoff calculations
4. All-time records, head-to-head history, streaks, awards, and season recaps
5. A browsable CGL record-book website — initial version complete

## Data caution

ESPN's fantasy endpoints are unofficial and can change. A successful HTTP response does not prove that a view contains useful historical data, so the discovery report records both availability and top-level structure. Private leagues may require `ESPN_S2` and `SWID` environment variables; never commit those values.
