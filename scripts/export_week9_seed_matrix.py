"""Build reproducible Week-9 seed matrices from the two validated waiver policies."""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from scripts.analytics.playoff_simulator import simulate_regular_season


def build_matrices(history, projections, *, simulations=200000, seed=2026, deviation=18.0):
    season = next(s for s in history["seasons"] if s["season"] == 2026)
    completed = [m for m in season["matchups"] if m.get("stage") == "regular_season" and m.get("decided")]
    future = [m for m in season["matchups"] if m.get("stage") == "regular_season" and not m.get("decided")]
    if {int(m["matchup_period"]) for m in completed} != set(range(1, 10)):
        raise ValueError("Not a Week-9-frozen historical snapshot; refuse to mix later results")
    if {int(m["matchup_period"]) for m in future} != set(range(10, 15)):
        raise ValueError("Remaining schedule must contain exactly Weeks 10-14")
    if not projections.get("ready") or projections.get("weeks") != list(range(10, 15)):
        raise ValueError("Projection report is not complete for Weeks 10-14")
    if projections.get("baseline_policy") != "roster_preservation" or projections.get("comparison_policy") != "full_waiver_optimization":
        raise ValueError("Expected dual-policy projection report")
    if len(projections["teams"]) != 14:
        raise ValueError("Expected 14 teams")
    models = {}
    for model, field in (("roster_preservation", "projected_points"),
                         ("full_waiver_optimization", "full_optimization_projected_points")):
        means = {}
        for team in projections["teams"]:
            tid = int(team["team_id"])
            means[tid] = {}
            for week in range(10, 15):
                value = team[field].get(str(week))
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"Missing/invalid {model} projection for team {tid} week {week}")
                means[tid][week] = float(value)
        result = simulate_regular_season(season, means, simulations=simulations,
                                         seed=seed, standard_deviation=deviation)
        for team in result["teams"]:
            probabilities = team["seed_probabilities"]
            if abs(sum(probabilities.values()) - 1) > 0.002:
                raise ValueError("Seed probabilities do not sum to one")
            if abs(sum(probabilities.get(str(k), 0) for k in range(1, 7)) - team["playoff_probability"]) > 0.002:
                raise ValueError("Playoff probability mismatch")
            if abs(sum(probabilities.get(str(k), 0) for k in (1, 2)) - team["bye_probability"]) > 0.002:
                raise ValueError("Bye probability mismatch")
        models[model] = result
    return {"season": 2026, "completed_through_week": 9,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "simulations_per_model": simulations, "seed": seed,
            "weekly_score_standard_deviation": deviation,
            "note": "Seed probabilities only; playoff-week championship probabilities require separate projections.",
            "models": models}


def write_outputs(report, json_path, csv_path):
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as output:
        fields = ["model", "team_id", "team_name", "playoff_probability",
                  "bye_probability", "expected_seed", "expected_wins"] + [f"seed_{i}" for i in range(1, 15)]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for model, result in report["models"].items():
            for team in result["teams"]:
                writer.writerow({"model": model, **{k: team[k] for k in fields[1:7]},
                                 **{f"seed_{i}": team["seed_probabilities"].get(str(i), 0)
                                    for i in range(1, 15)}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, default=Path("app/data/core_history.json"))
    parser.add_argument("--projections", type=Path, default=Path("data/reports/remaining_week_team_projections.json"))
    parser.add_argument("--output", type=Path, default=Path("data/reports/week9_seed_matrix.json"))
    parser.add_argument("--csv", type=Path, default=Path("data/reports/week9_seed_matrix.csv"))
    parser.add_argument("--simulations", type=int, default=200000)
    args = parser.parse_args()
    report = build_matrices(json.loads(args.history.read_text()),
                            json.loads(args.projections.read_text()), simulations=args.simulations)
    write_outputs(report, args.output, args.csv)
    print(f"Generated two {args.simulations:,}-trial seed matrices: {args.output} and {args.csv}")


if __name__ == "__main__":
    main()
