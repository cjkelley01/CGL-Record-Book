# Moves That Mattered

## Editorial model

The public page is a curated collection of league-history stories, not a transaction leaderboard. Thresholds and counterfactual comparisons generate internal candidates only; crossing a threshold does not publish a story.

`scripts/moves_stories.py` contains the editorial manifest. Every entry has a stable story ID and type, supporting transaction IDs, expected manager and player identities, a display priority, headline, narrative sections, and selected evidence. Relevant seasons are derived from the supporting transactions. The build fails when an event disappears, identities no longer match, or two stories claim the same transaction.

The year filter includes single-season stories from that year. A cross-year story appears only when one of its supporting events occurred in the selected year, and its complete span and narrative remain visible. A season with no selected story shows an honest empty state.

## Current selection

- The 2025 six-player Charley–Emma trade and the three-game run that followed, paired with the eventual 6–8 and 5–9 outcomes.
- The 2024 four-player Charley–Charley trade that supplied substantial starter production to both teams and became part of the champion’s season.
- Timmy’s three distinct high-value additions across 2024–2025.
- Flux Capacitors’ four-defense rotation during the 2025 championship bracket.
- Tee Higgins’ actual 2024 drop and subsequent Timberwolves acquisition.
- Bucky Irving’s strong 2024 contribution within a team season that still ended outside the playoffs.

These stories were selected for distinct narrative value. Managers, seasons, and old category labels are not quotas.

## Coverage and contribution rules

Official analysis begins in 2024. The refresh archives `mTransactions2`, paginated `kona_league_communication`, and `kona_playercard`. Historical player cards currently provide completed transaction detail; rejected, canceled, proposed, and failed historical moves remain unavailable. Empty route responses are coverage gaps, not proof that no moves occurred.

Contribution includes actual ESPN points only when the player was in the acquiring team’s starting lineup during that ownership stint. Bench production, consolation games, playoff-bye scores, and production outside the stint do not count. A drop and reacquisition form separate episodes. Exact scoring-period stats avoid ESPN’s cumulative totals in multiweek matchups.

Trades retain both sides and all recovered assets. A multi-player trade is one deal. “Got away” candidates require an actual drop; traded assets do not qualify under that description.

## Corrected candidate logic

- Trade success is evaluated independently for each side. One qualifying return does not credit both managers.
- Repeated-success seasons come from qualifying events, not general transaction activity.
- Public year filtering operates on story support events and never presents career totals as one-year accomplishments.
- Replacement candidates require a positive archived pregame projection.
- Each matchup can count at most once, even when multiple acquired players started. Multiweek playoff matchups are evaluated at series level.
- Trade comparisons do not restore outgoing assets and are marked as incomplete no-trade scenarios. They are not used for definitive trade-generated win claims.

The published stories favor actual contribution, verified records, and known season outcomes. They use qualified language when timing is notable but causation is unsupported. No story claims that a move secured a berth or championship.

## Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
corepack.cmd pnpm typecheck
corepack.cmd pnpm lint
corepack.cmd pnpm build
```

Tests cover story filtering, cross-year relevance, duplicate story coverage, side-specific success attribution, actual-drop qualification, duplicate transactions, incomplete trades, ownership stints, starter scoring, transaction timing, multi-player deals, and multiweek totals.
