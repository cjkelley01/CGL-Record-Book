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
