"""Export team-only Week 10-14 ESPN projections and explicit readiness diagnostics.

Incomplete team-weeks remain null; never invent projections or silently use zero.
"""
import json
from pathlib import Path

from scripts.analytics.espn_projections import extract_weekly_means


def build_report(data_root=Path("data"), season=2026, weeks=range(10, 15)):
    root = Path(data_root)
    teams = json.loads((root / "raw" / str(season) / "league" / "mTeam.json").read_text())["teams"]
    names = {
        int(team["id"]): team.get("name") or
        (str(team.get("location", "")) + " " + str(team.get("nickname", ""))).strip()
        for team in teams
    }
    if len(names) != 14:
        raise ValueError(f"Expected 14 distinct teams; got {len(names)}")
    weeks = list(weeks)
    result = extract_weekly_means(root, season, weeks, sorted(names))
    coverage = []
    for row in result["coverage"]:
        coverage.append({
            "week": row["week"],
            "status": row["status"],
            "valid_lineups": row.get("teams_with_valid_lineups", 0),
            "expected_teams": row.get("teams_expected", len(names)),
            "teams_using_waiver_replacements": row.get("teams_using_waiver_replacements", 0),
            "teams_using_cross_week_waiver_estimates": row.get("teams_using_cross_week_waiver_estimates", []),
            "cross_week_waiver_reference_week": row.get("cross_week_waiver_reference_week"),
            "waiver_projection_source_week": row.get("waiver_projection_source_week"),
            "teams_without_valid_lineups": row.get("teams_without_valid_lineups", []),
        })
    return {
        "season": season,
        "weeks": weeks,
        "ready": result["ready"],
        "baseline_policy": "roster_preservation",
        "comparison_policy": "full_waiver_optimization",
        "coverage": coverage,
        "teams": [{
            "team_id": tid,
            "team_name": names[tid],
            "lineup_audit": {str(week): result["lineup_audit"][tid].get(week) for week in weeks},
            "full_optimization_lineup_audit": {str(week): result["optimized_audit"][tid].get(week) for week in weeks},
            "full_optimization_projected_points": {
                str(week): round(result["optimized_means"][tid][week], 2)
                if week in result["optimized_means"][tid] else None for week in weeks
            },
            "full_optimization_uplift": {
                str(week): round(result["optimized_means"][tid][week] - result["means"][tid][week], 2)
                if week in result["means"][tid] and week in result["optimized_means"][tid] else None
                for week in weeks
            },
            "projected_points": {
                str(week): round(result["means"][tid][week], 2)
                if week in result["means"][tid] else None for week in weeks
            },
        } for tid in sorted(names)],
    }


def main():
    report = build_report()
    path = Path("data/reports/remaining_week_team_projections.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Projection coverage: {sum(r['valid_lineups'] for r in report['coverage'])}/70; ready={report['ready']}")
    print(f"Report: {path}")
    if not report["ready"]:
        print("WARNING: Incomplete projections; do not publish seed odds from this export.")


if __name__ == "__main__":
    main()
