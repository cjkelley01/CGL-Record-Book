# Week 9 playoff seed matrix — implementation plan

Status: planning / no simulated probabilities published from this branch.

## Baseline
2026 CGL after completed Week 9: 14 teams, 6 playoff teams, top two byes, regular-season Weeks 1–14, playoff Week 15 (3v6, 4v5), Week 16 (1 vs 4/5 winner; 2 vs 3/6 winner), Weeks 17+18 combined championship. Standings ties use cumulative points for. Freeze actual Week 9 records, scores, and PF before any simulation. Verify against ESPN export, never treat projections as actual results.

## Work plan
1. Refresh authenticated ESPN snapshots for Weeks 10–18 on the user's computer or a credentialed GitHub Action. Never commit ESPN credentials.
2. Generate 70 team-week legal lineup projections for Weeks 10–14. Existing lineup_projection_readiness.json reports 19 incomplete team-weeks: W10 seven, W11 seven, W13 three, W14 two. Recheck after refresh.
3. For missing starters, use (a) legal roster replacement with valid week projection, (b) verified available waiver candidates with valid week projection, (c) a flagged estimate derived from player history adjusted for playing status/bye and role, (d) flagged conservative positional estimate only when credible eligibility and playing status are verified. Do not assume a team can start a free agent without an acquisition. Never silently count an unfilled position as zero or as a guaranteed signing. Compare conservative/base/optimistic waiver scenarios.
4. Validate every simulated team-week: exactly one QB, two RB, two WR, one TE, one FLEX, one D/ST, one K; no duplicated players; NFL bye and injury status accounted for; projected scores finite and nonnegative; record data provenance and fallback counts.
5. Simulate at least 200,000 full league regular seasons with weekly correlated team scoring where appropriate, using the exact Weeks 10–14 schedule. Carry forward actual Week 9 PF and W/L. Sort by wins then PF, assign seeds 1–6, and record all 14 teams' seed 1–6 and miss frequencies. Every team's seven probabilities must sum to 1 within rounding.
6. Simulate Week 15, Week 16, and the two-week combined Week 17+18 final using separately validated projected rosters. Track title, finalist, bye, opponents, and bracket composition. Ensure bracket routes correctly.
7. Produce a machine-readable JSON artifact plus human-readable 14-team matrix and Charley-specific opponent / bracket paths. Include model timestamp, inputs, assumptions, random seed, sample count, and sensitivity to waiver fallback / score variance.
8. Add regression tests for tiebreakers, seed totals, bye logic, two-week final, incomplete projections, and determinism; run tests, lint, and website build before opening a PR. Do not merge without review.

## Acceptance criteria
- All 70 regular-season team-week means are available with provenance, or the report explicitly marks itself blocked.
- No missing projections are disguised as ESPN data.
- Seed matrix rows sum to 100%, playoff qualification equals sum(seeds 1..6), and bye equals sum(seeds 1..2).
- Reproducible outputs, no production changes until tests pass.

## November 10 first GitHub Actions export
- Run [42889006172](https://github.com/cjkelley01/CGL-Record-Book/actions/runs/42889006172) succeeded and generated a team-only artifact.
- Actual legal lineup coverage: 59 of 70 team-weeks. W10: 14/14 (eight waiver estimates), W11: 9/14, W12: 14/14, W13: 10/14, W14: 12/14.
- Missing: W11 teams 2,3,13,17,20; W13 teams 2,9,14,17; W14 teams 4,19.
- First correction implemented: after target-week waiver replacement fails, use Week 10 ESPN-projected, status-confirmed free agents as a reference-week estimate for a later week, checking independent NFL target-week schedule and byes. The mean of the three highest eligible reference-week projections is **not** represented as an ESPN target-week forecast, real acquisition, or assured score. Teams using this tier are enumerated in report metadata.
- This correction is *not yet verified by a completed GitHub Actions run*. The main launcher now runs tests first. Re-run the workflow, examine remaining null entries and fallback counts, then make sensitivity cases before publishing probabilities.

## Lineup-level audit requirement
Every valid team-week now exports slot IDs, player names, projected points, and whether each starter is a hypothetical waiver replacement. The model uses optimized legal lineups, which may differ from ESPN's displayed starters. Before publication, reconcile Week 10 Charley (team 1) against the ESPN displayed ~112 points excluding TE; an expected ~7 point TE waiver estimate implies ~119, not the earlier 124.46. Do not equate the optimized projection with ESPN's current starting lineup. Verify on the next workflow run.

## Dual waiver forecast policies (2026-11-10)

The Week 10 audit showed that an earlier 124.13-point estimate for Charley selected hypothetical TE, K and FLEX options. The engine now calculates **both** policies independently for every team/week:

- **Roster preservation (baseline):** maximize the number of verified rostered starters in a legal lineup, then maximize projected points. This fills unplayable/bye/missing-position gaps with synthetic top-three waiver estimates without replacing a playable rostered kicker/FLEX just to improve points.
- **Full waiver optimization (upside):** maximize projected points across rostered and hypothetical waiver options; it may replace playable rostered starters. This is a scenario, not a transaction recommendation or guaranteed waiver availability.

The export retains `projected_points` and `lineup_audit` as the baseline for downstream compatibility, and adds `full_optimization_projected_points`, `full_optimization_lineup_audit`, and `full_optimization_uplift`. Audit flags identify synthetic additions by roster membership, not by negative player IDs (real ESPN D/ST IDs can be negative).

**Important model limitations:** synthetic replacements are slot-specific averages of the top three ESPN-confirmed available candidates; they do not represent actual player acquisitions, and independent teams may be modeled using the same candidate pool. Target-week ESPN projections are preferred, while cross-week estimates are marked separately. A projection is not ready if a legal lineup cannot be constructed. Re-run GitHub validation and the manual launcher before relying on the Week 10 comparison or publishing probabilities.

## Dual-model seed matrix workflow integration

The manual GitHub Actions launcher on `main` checks out this development branch, exports both Week 10–14 forecast policies, then runs `python -m scripts.export_week9_seed_matrix --simulations 200000`. The artifact now includes `week9_seed_matrix.json`, `week9_seed_matrix.csv`, and the source projection report. The generator uses `app/data/core_history.json` as historical inputs and **refuses** to run if that history is no longer frozen at Week 9. This is deliberate: later actual results must not leak into a Week-9 probability estimate. If that guard fails, create a verified frozen Week-9 history snapshot; do not weaken the guard.

The generator currently models **regular-season seeds and playoff qualification**, not playoff-week championship outcomes. Weeks 15–18 require separately validated inputs. The 18-point score SD and independent weekly Gaussian draws remain explicit assumptions. Run the launcher and inspect artifacts before calling the new integration verified.

## Week 9 history sync fix (2026-11-10)

The first combined export run [42896562947](https://github.com/cjkelley01/CGL-Record-Book/actions/runs/42896562947) passed all Python tests and produced 70/70 valid projected lineups. The matrix job then correctly refused a history snapshot where all seven Week 9 games were still marked undecided. The checked-in `app/data/core_history.json` currently reflects only Weeks 1–8.

The launcher now creates `data/reports/week9_history_snapshot.json` from the checked-in history plus **only** the authenticated ESPN final Week 9 matchup scores fetched in the same run. The freezer checks seven matchups, matchup IDs, team pairings, actual positive scores, and matching winner flags, and rejects any decided Week 10–14 games in the checked-in source. It does not change or publish the site's `core_history.json`. The matrix consumes this isolated snapshot. The report artifact includes the snapshot for reproducibility. New regression tests cover the score transfer, unfinalized games, opponent mismatch and future-result leakage. Re-run the manual workflow to validate the integration.

## Exploratory championship sensitivity (2026-11-10)

The manual launcher also runs `scripts/export_week9_championship_scenarios.py` against the same authenticated, frozen Week-9 history and dual-policy Week 10–14 projections. It produces six scenarios: roster-preserving and full-waiver-optimized policies, each with 0%, 10%, and 20% **uniform Week-18 projected team-score haircuts**, using 200,000 trials per scenario. The bracket is six qualifiers, #1/#2 byes, Week 15 quarterfinal, Week 16 semifinal, and combined Weeks 17+18 championship.

**These are explicitly exploratory, not verified Week 15–18 player forecasts.** Each team's Week-14 projection is carried forward to Weeks 15, 16, and 17; Week 18 is reduced by the indicated uniform haircut. The haircut is a sensitivity analysis, not a claim that any specific NFL player will rest, and cannot measure differential Week-18 rest exposure across teams. The simulator uses independent Gaussian weekly scores with SD 18. Outputs are `data/reports/week9_championship_scenarios.json` and `.csv`. Before treating championship probabilities as decision-grade, build validated playoff-week player projections and a player-level Week-18 risk model.

Tests check six scenarios, sum of championship odds = 1, finalist odds = 2, playoff odds = 6, missing projections fail closed, and later-results leakage is rejected.
