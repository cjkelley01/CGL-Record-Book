# Repository structure

## Website

- `app/page.tsx`: tab navigation, shared selection state, and page composition.
- `components/record-book/`: record-book features, including standings, manager profiles, head-to-head history, drafts, season archives, and record cards.
- `lib/record-book/history.ts`: the dataset import, shared domain types, and display formatting helpers.
- `app/globals.css`: site styling and responsive layouts.
- `components/ui/`: reusable shadcn UI primitives. Only the tabs, tables, and selects used by the site are retained.
- `app/data/core_history.json`: generated, committed website data. Make statistical changes in the Python pipeline, then regenerate this file.

Feature components may import shared helpers and UI primitives. Keep navigation and cross-tab selection state in `app/page.tsx`, and keep record calculations in the Python pipeline where practical.

## Data pipeline

- `scripts/discover_espn_history.py`: downloads and reports on ESPN source data.
- `scripts/build_core_history.py`: normalizes history and calculates records.
- `scripts/update_current_season.py`: coordinates downloading and rebuilding.
- `data/raw/`, `data/processed/`, and `data/reports/`: local archives and generated output, excluded from Git.
- `docs/record-book-scope.md`: historical boundaries, identities, and verification rules.

## Development, preview, and deployment

`index.html` and `src/pages-main.tsx` render the React app. `vite.config.ts` is the single configuration for every mode:

- `pnpm dev`: live local development with automatic browser opening and hot updates.
- `pnpm preview`: builds the production site and then serves it locally, opening the browser. A failed build stops the preview.
- `pnpm build`: produces `dist-pages/`, which both GitHub Actions deployment workflows publish.
- `pnpm build:pages`: compatibility alias for the same build.

The development and preview commands call `scripts/website.mjs`, which also supports `--no-open` for automated checks. Preview commands never push or deploy.

The site uses the `/CGL-Record-Book/` base path locally and on GitHub Pages. No server-side framework, database, authentication service, or Cloudflare account is required. Website metadata and the favicon link live in `index.html`.

Run `pnpm typecheck`, `pnpm lint`, and `pnpm preview` before publishing changes. The Python archive and calculation scripts remain independent of the website runtime.

## Future organization

When extending statistical calculations, consider splitting `build_core_history.py` into normalization, identity mapping, and record calculation modules, with regression coverage for statistical rules first. The current cleanup intentionally preserves those calculations.
