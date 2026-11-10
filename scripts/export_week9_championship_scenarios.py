"""Championship scenarios using audited ESPN target-week lineups through Week 18.

Week-18 haircuts are hypothetical sensitivities, not player-level rest forecasts.
"""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from scripts.analytics.weekly_forecast import simulate


def build_championship_scenarios(history, projections, *, simulations=200000,
                                 seed=2026, deviation=18.0,
                                 week18_haircuts=(0.0, 0.10, 0.20)):
    season = next(s for s in history["seasons"] if s["season"] == 2026)
    regular = [m for m in season["matchups"] if m.get("stage") == "regular_season"]
    if {int(m["matchup_period"]) for m in regular if m.get("decided")} != set(range(1, 10)):
        raise ValueError("Expected frozen Week-9 completed results")
    if {int(m["matchup_period"]) for m in regular if not m.get("decided")} != set(range(10, 15)):
        raise ValueError("Expected exactly Weeks 10-14 undecided")
    if not projections.get("ready") or projections.get("weeks") != list(range(10, 19)):
        raise ValueError("Incomplete Week 10-18 projections")
    if projections.get("baseline_policy") != "roster_preservation" or projections.get("comparison_policy") != "full_waiver_optimization":
        raise ValueError("Expected two distinct waiver policies")
    ids = {int(t["team_id"]) for t in season["teams"]}
    if len(ids) != 14 or {int(t["team_id"]) for t in projections["teams"]} != ids:
        raise ValueError("Team IDs differ between historical snapshot and projection report")
    if simulations < 1 or deviation <= 0:
        raise ValueError("Invalid simulation settings")
    models = {}
    for policy, field in (("roster_preservation", "projected_points"),
                          ("full_waiver_optimization", "full_optimization_projected_points")):
        base = {}
        for team in projections["teams"]:
            tid = int(team["team_id"])
            base[tid] = {}
            for week in range(10, 19):
                value = team[field].get(str(week))
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"Invalid {policy} team {tid} Week {week} projection")
                base[tid][week] = float(value)
        for haircut in week18_haircuts:
            if not isinstance(haircut, (int, float)) or isinstance(haircut, bool) or not 0 <= haircut < 1:
                raise ValueError("Week 18 haircut must be between 0 and 1")
            means = {tid: dict(scores) for tid, scores in base.items()}
            for tid in ids:
                means[tid][18] = base[tid][18] * (1 - haircut)
            result = simulate(season, means, trials=simulations, seed=seed,
                              deviation=deviation, playoff_weeks=((15,), (16,), (17, 18)))
            models[f"{policy}__week18_{int(round(haircut * 100)):02d}pct"] = result
    return {"season": 2026, "as_of_week": 9,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "simulations_per_scenario": simulations, "seed": seed,
            "scenarios": models,
            "assumptions": {
                "playoff_weeks": {"quarterfinal": [15], "semifinal": [16], "final": [17, 18]},
                "weekly_score_sd": deviation,
                "playoff_projection_source": "Audited ESPN target-week roster projections for Weeks 15-18; hypothetical waiver substitutions explicitly marked in lineup audits",
                "week18_haircuts": list(week18_haircuts),
                "week18_haircut_scope": "Uniform percentage reduction to all teams' Week-18 projected means; not player-specific rest modeling",
                "limitations": "ESPN forecasts may change; roster-preservation and waiver optimization use hypothetical lineup policies, not actual transactions. Week-18 haircut is uniform rather than player-specific rest exposure. NFL rest decisions, injuries and future transactions are uncertain."
            }}


def write_outputs(report, json_path, csv_path):
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        columns = ["scenario", "team_id", "team_name", "playoff_probability", "bye_probability",
                   "final_probability", "championship_probability", "expected_seed", "expected_wins"]
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for name, model in report["scenarios"].items():
            for team in model["teams"]:
                writer.writerow({"scenario": name, **{key: team[key] for key in columns[1:]}})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history", type=Path, default=Path("data/reports/week9_history_snapshot.json"))
    p.add_argument("--projections", type=Path, default=Path("data/reports/remaining_week_team_projections.json"))
    p.add_argument("--output", type=Path, default=Path("data/reports/week9_championship_scenarios.json"))
    p.add_argument("--csv", type=Path, default=Path("data/reports/week9_championship_scenarios.csv"))
    p.add_argument("--simulations", type=int, default=200000)
    args = p.parse_args()
    result = build_championship_scenarios(json.loads(args.history.read_text()),
                                          json.loads(args.projections.read_text()),
                                          simulations=args.simulations)
    write_outputs(result, args.output, args.csv)
    print(f"Generated {len(result['scenarios'])} championship sensitivity scenarios at {args.simulations:,} trials each")


if __name__ == "__main__":
    main()
