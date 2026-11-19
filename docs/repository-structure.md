# Repository structure

## Website

- `app/page.tsx` composes the current page and resolves shared filter values.
- `components/record-book/record-book-navigation.tsx` defines the page list shared by the desktop sidebar and mobile drawer. Overview is a standalone link above Season, History, and Analytics.
- `lib/record-book/navigation.ts` reads and updates URL fragments for shareable pages and filters on static hosting.
- `components/record-book/`: record-book features, including standings, manager profiles, head-to-head history, drafts, season archives, and record cards.
- `lib/record-book/history.ts`: the dataset import, shared domain types, and display formatting helpers.
- `app/globals.css`: site styling and responsive layouts.
- `components/ui/` contains reusable UI primitives.
- `app/data/core_history.json` contains generated, committed league history. `app/data/playoff_forecast.json` contains the published forecast. Make statistical changes in the Python pipeline, then regenerate the relevant dataset.

When adding a page, register it in the shared page list and compose its content in `app/page.tsx`. Keep existing section IDs stable so shared links continue to work. Keep record calculations in the Python pipeline where practical.

## Data pipeline

- `scripts/discover_espn_history.py`: downloads and reports on ESPN source data.
- `scripts/build_core_history.py`: normalizes history and calculates records.
- `scripts/update_current_season.py`: coordinates downloading and rebuilding.
- `scripts/moves_analysis.py`: deduplicates transactions, separates ownership stints, and calculates starter-only move impact.
- `scripts/moves_stories.py`: validates the curated editorial manifest and resolves story facts from supporting events.
- `data/raw/` and `data/processed/` hold local archive and generated data excluded from Git.
- `data/forecasts/` contains committed forecast snapshots. The two committed projection coverage and lineup readiness reports live in `data/reports/` alongside ignored local reports.
- `docs/record-book-scope.md`: historical boundaries, identities, and verification rules.
- `docs/moves-that-mattered.md`: source coverage, metrics, thresholds, validation, and counterfactual limits.

## Development, preview, and deployment

`index.html` and `src/pages-main.tsx` render the React app. `vite.config.ts` is the single configuration for every mode:

- `pnpm dev`: live local development with automatic browser opening and hot updates.
- `pnpm preview`: builds the production site and then serves it locally, opening the browser. A failed build stops the preview.
- `pnpm build`: produces `dist-pages/`, which the [GitHub Pages deployment workflow](../.github/workflows/deploy-pages.yml) publishes after pushes to `main`, successful season refreshes, or manual runs.
- `pnpm build:pages`: compatibility alias for the same build.

The development and preview commands call `scripts/website.mjs`, which also supports `--no-open` for automated checks. Preview commands never push or deploy.

The site uses the `/CGL-Record-Book/` base path locally and on GitHub Pages. No server-side framework, database, authentication service, or Cloudflare account is required. Website metadata and the favicon link live in `index.html`.

Run `pnpm typecheck`, `pnpm lint`, and `pnpm preview` before publishing changes. The Python archive and calculation scripts remain independent of the website runtime.

## Future organization

When extending statistical calculations, consider splitting `build_core_history.py` into normalization, identity mapping, and record calculation modules, with regression coverage for statistical rules first. The current cleanup intentionally preserves those calculations.
