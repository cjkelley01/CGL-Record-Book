# Moves That Mattered

## Editorial model

The public page is a curated collection of league-history stories, not a transaction leaderboard. Thresholds and counterfactual comparisons generate internal candidates only; crossing a threshold does not publish a story.

`scripts/moves_stories.py` contains the editorial manifest. Every entry has a stable story ID and type, supporting transaction IDs, expected manager and player identities, a display priority, headline, narrative sections, and selected evidence. Draft references validate the original manager, player, round and overall pick. Relevant seasons are derived from the supporting transactions; the current draft references occur in those same seasons. The build fails when an event disappears, identities no longer match, or two stories claim the same transaction.

The year filter includes single-season stories from that year. A cross-year story appears only when one of its supporting events occurred in the selected year, and its complete span and narrative remain visible. A season with no selected story shows an honest empty state.

## Current selection

- The 2025 six-player Charley–Emma trade and the three-game run that followed, paired with the eventual 6–8 and 5–9 outcomes.
- Charley’s Round 12 Hubbard pick becoming part of the 2024 four-player trade; both teams’ returns and eventual outcomes remain together.
- Timmy’s first-overall McCaffrey pick, Round 11 Brown pick, documented Brown–Akers reversal, and continued post-draft success in 2025. The Akers transaction is provenance, not a fourth successful acquisition.
- Alex’s two trades on November 22, 2024: Round 16 pick Mayfield becomes trade capital, five arrivals reach the quarterfinal lineup, and the team loses by 5.6 points. Both counterparties and the complete packages remain in one account.
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

The published stories favor actual contribution, verified records, and known season outcomes. Accuracy comes from describing what occurred and attributing actual contributions, without repetitive end-of-paragraph causation disclaimers. Combined trades, waiver reversals and draft-to-trade chains may form one story. Supporting events must not be counted as extra successes or retold as opposing-side stories. No story claims that a move secured a berth or championship.

## Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
corepack.cmd pnpm typecheck
corepack.cmd pnpm lint
corepack.cmd pnpm build
```

Tests cover story filtering, cross-year relevance, duplicate story coverage, side-specific success attribution, actual-drop qualification, duplicate transactions, incomplete trades, ownership stints, starter scoring, transaction timing, multi-player deals, and multiweek totals.


## External context

McCaffrey’s injury context is supported by the 49ers’ official announcements, not inferred from a fantasy roster absence:

- September 14, 2024: [placed on injured reserve](https://www.49ers.com/news/christian-mccaffrey-placed-on-injured-reserve-roster-moves-ahead-of-sfvsmin).
- November 8, 2024: [Achilles tendonitis and planned Week 10 debut](https://www.49ers.com/news/christian-mccaffrey-nick-bosa-questionable-for-week-10-vs-buccaneers-injury-report-sfvstb).
- November 9, 2024: [activated to the 53-man roster](https://www.49ers.com/news/49ers-activate-rb-christian-mccaffrey-to-the-53-man-roster-and-more-roster-moves).

The story does not assert that the injury was worse than Timmy expected or that every replacement was ineffective. Draft positions, transaction dates, contributions and team results come from the league archive.
