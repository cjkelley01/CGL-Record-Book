# Moves That Mattered

## Coverage and sources

Official analysis begins in 2024. The refresh archives three ESPN routes:

1. `mTransactions2`, which supplies recent activity and non-completed statuses in the active season but returned no completed-season detail in the current verification.
2. `kona_league_communication`, requested in 250-topic pages. It currently supplies the active-season activity feed but returned an empty object for 2024 and 2025.
3. `kona_playercard`, which currently preserves completed historical transactions. A transaction appears on every involved player's card, so normalization deduplicates exact transaction IDs before analysis.

An empty route is recorded as a coverage gap, not evidence that no moves occurred. Historical player cards expose completed transactions only; rejected, canceled, proposed, and failed historical moves cannot currently be reconstructed. Recent non-completed transactions are retained in the raw `mTransactions2` archive but never promoted to completed moves. A trade qualifies only when the executed record contains assets moving in both directions; incomplete details are excluded.

The generated dataset reports source counts and removed duplicates by season. Raw responses remain local under `data/raw/<season>/transactions/`; public-safe normalized results are written to `app/data/core_history.json`.

## Contribution metric

Contribution is the sum of a player's actual ESPN fantasy points in weeks when all of the following are true:

- the player is on the acquiring team's archived weekly roster;
- the player occupies a starting slot, not bench or injured reserve;
- the week falls inside that acquisition's ownership stint; and
- the week is regular season or a championship-bracket game.

Bench points, consolation games, playoff-bye scores, and production outside the ownership stint do not count. A drop and later reacquisition create separate episodes. Weekly values come from the exact `statSourceId = 0` scoring-period stat; ESPN's `appliedStatTotal` is not used because it can be cumulative across multiweek matchups.

Trades are one deal per manager regardless of player count. Every recovered asset and both teams appear together. The page reports received lineup production without naming a winner from raw points alone.

## Qualification thresholds

Thresholds live in `scripts/moves_analysis.py` and are emitted with the dataset. They were selected after inspecting observed distributions, and categories remain hidden when nobody qualifies.

- Waiver Wire Gold: at least 100 regular-season starter points and six regular-season starts.
- The Ones That Got Away: a dropped player later supplies at least 80 starter points and five starts for another team.
- Deal Makers: at least one trade side receives 100 starter points and six starts.
- Buyer's Remorse: one side receives no more than 35 starter points while the other side receives at least 100.
- Championship Reinforcements: at least 25 points in two championship-bracket starts.
- Turning Points: at least 120 total starter points, seven starts, and one potentially changed matchup in the comparison below.

The Front Office requires at least two distinct qualifying moves for Waiver Whisperer, Deal Architect, or playoff-acquisition recognition. Total completed acquisition volume is context only; it is not treated as failed attempts or used as the primary ranking.

## Counterfactual limits

For an acquired starter, the comparison chooses the eligible bench player with the highest archived pregame projection and substitutes that player's actual score. A recorded win is labeled “potentially swung” only when the point difference exceeds the recorded margin. The page also tests the three highest-projected eligible alternatives and reports robustness where all available comparisons agree.

This is a transparent lineup comparison, not proof of causation. It does not remodel injuries, schedule strength, later acquisitions, outgoing assets beyond the historical roster that remained, changed seeding, or an alternate playoff bracket. Move-level comparisons must not be added together as independent wins. The site therefore uses qualified language and does not claim alternate champions or unsupported “Wrong Turns.”

## Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
corepack.cmd pnpm typecheck
corepack.cmd pnpm lint
corepack.cmd pnpm build
```

Regression tests cover duplicate player-card references, incomplete and pending trades, repeated ownership stints, bench-versus-starter scoring, transaction timing, multi-player trade counting, and exact weekly totals inside multiweek matchups.
