# CGL Analytics — implementation plan

## Objective
Extend the existing Record Book with auditable league-wide statistics and season forecasts. Keep the historical record and current-season ESPN standings as the source of truth. The analytics layer must not overwrite official results.

## Architecture
- Source: existing normalized `app/data/core_history.json` generated from ESPN snapshots.
- Calculation: isolated Python analytics modules under `scripts/analytics/`, with regression tests in `tests/`.
- Output: versioned analytics section in the generated public-safe JSON, including model version, snapshot week, assumptions, and simulation count.
- Presentation: a new Playoff Race section integrated into `app/page.tsx`, then luck and power-ranking views.
- Deployment: existing GitHub Actions and Pages pipeline; do not require a live backend.

## Phase 1 — historical, deterministic metrics
For each team in each completed scoring week:
1. **All-play wins/losses/ties:** compare that team's score with every other team's score in the same week, regardless of scheduled opponent. Exclude missing or unfinalized scores.
2. **Expected wins:** sum weekly all-play winning fractions, counting ties as half. Denominator is the number of other teams with valid scores in that week.
3. **Luck differential:** actual completed head-to-head wins plus half of ties, minus expected wins.
4. **Weekly rank:** rank scores within the week, with equal scores tied.
5. **Schedule swap:** replay each team's weekly scores against each other team's actual weekly opponents only when both teams have valid scores in that week. Label incomplete comparisons explicitly.

Never treat unplayed games as zero scores. Regular season only for these metrics.

## Phase 2 — probabilistic forecast
- Simulate remaining *regular-season* matchups from a team-strength model calibrated to completed scores; sample scores with a defensible uncertainty distribution and document all assumptions.
- Determine final standings using the actual league tiebreaker hierarchy, not an assumed one.
- Report playoff qualification (top 6), bye qualification (top 2), expected seed, and projected record for all 14 teams.
- Model the actual four-week postseason, including two-week championship, before reporting title odds.
- Add Monte Carlo seed stability checks and reproducible random seeds.
- Distinguish mathematical clinch/elimination from probabilistic near-certainty.

## Phase 3 — scenarios and reporting
- Condition on user-selected matchup results and rerun the forecast; ensure scenario constraints do not conflict.
- Preserve week-by-week forecast snapshots for probability history.
- Add weekly matchup leverage, rooting interests, power ratings, and commissioner report exports.

## Data validation gates
- Validate 14 current-season teams, schedule completeness, unique matchup identities, no duplicate week scores, no future games treated as decided.
- Cross-check calculated completed records and points against ESPN standings.
- Confirm regular-season length and playoff settings from archived league settings before forecasting.
- Handle tied scores, byes, missing weeks, and ESPN corrections.
- No displayed odds until these checks pass.

## Rollout
1. Add deterministic all-play and expected-win computations with tests.
2. Expose those metrics on a new League Analytics view.
3. Implement and test the season simulator.
4. Publish playoff probabilities and scenario tooling.

This is a planning baseline; it does not claim that forecasts are implemented.
