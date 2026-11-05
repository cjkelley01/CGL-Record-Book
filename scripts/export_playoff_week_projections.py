"""Export team-level playoff-week ESPN lineup projections, without player details."""
import json
from pathlib import Path
from scripts.analytics.espn_projections import extract_weekly_means

def main():
    root = Path("data")
    teams = json.loads((root / "raw/2026/league/mTeam.json").read_text())["teams"]
    names = {int(t["id"]): t.get("name") or (str(t.get("location", "")) + " " + str(t.get("nickname", ""))).strip() for t in teams}
    result = extract_weekly_means(root, 2026, range(15, 19), sorted(names))
    output = {"season": 2026, "weeks": [15, 16, 17, 18], "coverage": [
        {"week": row["week"], "status": row["status"], "valid_lineups": row.get("teams_with_valid_lineups", 0),
         "expected_teams": row.get("teams_expected", len(names)),
         "teams_without_valid_lineups": row.get("teams_without_valid_lineups", [])}
        for row in result["coverage"]],
        "teams": [{"team_id": tid, "team_name": names[tid],
                   "projected_points": {str(w): round(result["means"][tid][w], 2)
                                        if w in result["means"][tid] else None for w in range(15, 19)}}
                  for tid in sorted(names)]}
    path = Path("data/reports/playoff_week_team_projections.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
