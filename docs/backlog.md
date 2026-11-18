# CGL Record Book backlog

Track proposed changes here. Each entry should explain the problem and what would count as done. Link to a GitHub issue or pull request when work needs a discussion or implementation. Remove completed entries once the change lands and the relevant guide reflects it.

## Next

- [ ] **Bring the published playoff forecast up to date.** The forecast on `main` is based on Week 7, while the season refresh continues to update results. Use the [lineup-readiness report](../data/reports/lineup_projection_readiness.json) and [projection-coverage report](../data/reports/forecast_projection_coverage.json) to identify missing inputs. Done when the forecast uses a current completed week with validated lineup coverage, or the site clearly shows why the forecast is held and which week it represents.
- [ ] **Add a season maintenance runbook.** Document the annual season rollover, routine refresh and deployment checks, how to diagnose a failed refresh or held forecast, and how to recover. Link to the commands in the [README](../README.md).
- [ ] **Refresh the [repository structure guide](repository-structure.md).** Document the forecast dataset, tracked aggregate reports, and the single GitHub Pages deployment workflow. Keep the guide focused on where code and data live.
- [ ] **Update the [analytics roadmap](analytics-roadmap.md).** Mark all-play, schedule luck, power rankings, and the published forecast as implemented. Record the remaining work on scenario controls, probability history, and validation, with links back here for actionable changes.

## Needs investigation

- [ ] **Consolidate the manual ESPN projection probes.** Review the unique work on `research/espn-future-week-projections` and its local edits and stash before retiring anything. Decide whether a single manual workflow can cover both current uses.
- [ ] **Review standalone diagnostic scripts.** Check for manual use of `diagnose_future_lineups.py`, `fetch_current_waiver_snapshot.py`, and `validate_waiver_forecast.py`. Document the invocation for anything still used and remove scripts whose purpose has been covered elsewhere.
- [ ] **Decide whether to continue historical roster replay.** The live run for [PR #37](https://github.com/cjkelley01/CGL-Record-Book/pull/37) found zero paired cutoffs. The best historical cutoffs had legal lineups for 11 of 12 teams. Resume model comparison once both models have enough shared checkpoints, or archive the experiment if those inputs are unavailable.

## Later

- [ ] **Add matchup scenarios and weekly leverage.** Let readers see how selected results change playoff or bye odds once the baseline forecast is current and validated.
- [ ] **Show forecast history.** Use archived snapshots to show how odds changed by week, with the snapshot date, completed-through week, and model visible.
