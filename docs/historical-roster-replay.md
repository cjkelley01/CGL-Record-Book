# Batch 2: Cutoff-roster historical replay

This research compares two models at the **same historical checkpoints**:
the existing last-observed team projection baseline and a new roster-based
scoring-capacity proxy.

The roster proxy reconstructs each team's player membership and observed
starter-slot requirements from ESPN's historical `mRoster` data for the
checkpoint week. It estimates each player's points from completed weeks
**strictly before** that checkpoint, then uses the existing optimal legal
lineup optimizer and the existing playoff/championship simulator.

## Safeguards and exclusions

- No target-week ESPN projections or future-week player actuals enter the
  scoring estimate.
- Players with fewer than two observed prior games are excluded from the
  lineup optimizer; missing legal lineups invalidate the checkpoint.
- No imputation of missing player data as zero; no assumed waiver acquisition.
- Roster membership is retrieved retrospectively and is **not** a verified
  timestamped snapshot from the actual historical decision point.
- Future byes, injuries, changes of ownership and free-agent availability are
  not reconstructed. The estimated lineup is a fixed scoring-capacity proxy.
- The experiment is **not** a validation of historical ESPN forward projections.
- Comparisons use only checkpoints for which **both** models produce outputs.

## Execution

Run **Historical CGL Season Replay (manual)** after merging. The workflow now
extracts historical player weeks, runs regression/leakage tests, and uploads
`historical-roster-replay/summary.json` plus paired model probabilities.
If no historical cutoff produces a complete legal roster, the job fails
explicitly with coverage diagnostics rather than inventing results.

## What Batch 3 can evaluate

If adequate paired coverage exists, compare playoff, bye and championship
Brier scores while respecting the small number of independent seasons.
If coverage is poor, prioritize better historical player history/position
coverage and prospective 2026 captures before tuning production weights.

**No production forecasts or weight settings are changed by this PR.**
