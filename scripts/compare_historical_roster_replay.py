"""Paired replay comparison with cutoff-only roster estimates."""
import argparse
import csv
import json
from pathlib import Path
from scripts.historical_roster_proxy import cutoff_lineup_estimates, load_player_rows
from scripts.replay_historical_seasons import replay, metrics

def summarize(rows):
    return {str(w): {name: metrics(
        [r for r in rows if r["weight"] == w and
         (name != "championship" or r["championship_bracket_verified"])],
        pred, actual)
        for name, pred, actual in (
            ("playoffs", "playoff_probability", "playoff_actual"),
            ("byes", "bye_probability", "bye_actual"),
            ("championship", "championship_probability", "championship_actual"))}
        for w in sorted({r["weight"] for r in rows})}

def compare(seasons, team_rows, player_rows, *, cutoffs=(4,7,10,12), trials=2000):
    baseline, baseline_skips = replay(seasons, team_rows, cutoffs=cutoffs, trials=trials)
    proxy_inputs, coverage = [], []
    for season in seasons:
        yr = int(season["season"])
        ids = [int(t["team_id"]) for t in season["teams"]]
        for cutoff in cutoffs:
            estimates, report = cutoff_lineup_estimates(player_rows, yr, cutoff, ids)
            coverage.append(report)
            if estimates is not None:
                proxy_inputs.extend({"season":yr, "week":cutoff, "team_id":tid,
                                     "reconciled":"true", "projected":value}
                                    for tid,value in estimates.items())
    proxy, proxy_skips = replay(seasons, proxy_inputs, cutoffs=cutoffs, trials=trials)
    paired = {(r["season"],r["cutoff"]) for r in proxy}
    baseline = [r for r in baseline if (r["season"],r["cutoff"]) in paired]
    proxy = [r for r in proxy if (r["season"],r["cutoff"]) in paired]
    result = {
        "paired_cutoffs": sorted(paired),
        "baseline_scores": summarize(baseline),
        "roster_proxy_scores": summarize(proxy),
        "roster_coverage": coverage,
        "baseline_skips": baseline_skips,
        "roster_skips": proxy_skips,
        "limitations": [
            "Historical roster ownership is retrospectively observed, not timestamp verified.",
            "Only pre-cutoff actuals are used for player scoring estimates.",
            "Future byes, injuries, waiver moves and roster changes are not modeled.",
            "These are not historical ESPN future-week projections.",
            "Comparison uses identical cutoffs; do not tune weights on these same results."
        ]}
    return result, baseline, proxy

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="app/data/core_history.json")
    p.add_argument("--team-csv",default="team-uncertainty-research/team_reconciliation.csv")
    p.add_argument("--player-csv",default="historical-player-dataset/player_weeks.csv")
    p.add_argument("--output",default="historical-roster-replay")
    p.add_argument("--trials",type=int,default=2000)
    a=p.parse_args()
    seasons=json.loads(Path(a.history).read_text())["seasons"]
    with Path(a.team_csv).open(newline="",encoding="utf-8") as f:
        team_rows=list(csv.DictReader(f))
    result,baseline,proxy=compare(seasons,team_rows,load_player_rows(a.player_csv),trials=a.trials)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    for name,rows in (("baseline",baseline),("roster_proxy",proxy)):
        if rows:
            with (out/(name+"_probabilities.csv")).open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]))
                writer.writeheader();writer.writerows(rows)
    print(json.dumps(result,indent=2))
    if not result["paired_cutoffs"]:
        raise SystemExit("No paired eligible checkpoints; inspect coverage in summary.json")

if __name__=="__main__":main()
