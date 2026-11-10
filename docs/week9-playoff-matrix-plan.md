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
