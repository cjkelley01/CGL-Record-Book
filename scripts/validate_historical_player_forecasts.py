"""Research-only, chronological ESPN projection validation and rolling backtest."""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

STARTER_SLOTS = {0, 2, 4, 6, 16, 17, 18, 23}
# ESPN slot 23 may be FLEX in some configurations; verify against league settings before production use.
def number(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def metrics(items):
    if not items:
        return {"n": 0}
    errors = [a-p for p,a in items]
    return {"n":len(items), "bias":round(sum(errors)/len(errors),4),
            "mae":round(sum(map(abs,errors))/len(errors),4),
            "rmse":round(math.sqrt(sum(e*e for e in errors)/len(errors)),4)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="historical-player-dataset/player_weeks.csv")
    ap.add_argument("--output",default="historical-validation")
    args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with open(args.input,encoding="utf-8",newline="") as f: rows=list(csv.DictReader(f))
    for r in rows:
        r["season"]=int(r["season"]);r["week"]=int(r["week"])
        r["projected"]=number(r["projected"]);r["actual"]=number(r["actual"])
    rows.sort(key=lambda r:(r["season"],r["week"]))
    duplicates=Counter((r["season"],r["week"],r["team_id"],r["player_id"]) for r in rows)
    duplicate_keys=sum(v>1 for v in duplicates.values())
    position=defaultdict(list);season=defaultdict(list);all_pairs=[]
    for r in rows:
        if r["projected"] is None or r["actual"] is None:continue
        pair=(r["projected"],r["actual"])
        position[r["position_id"]].append(pair)
        season[str(r["season"])].append(pair)
        all_pairs.append(pair)
    # Only use previous weeks, never another player's actual from the current week.
    history=defaultdict(list); pos_history=defaultdict(list)
    predictions=[]; team_groups=defaultdict(list)
    for key in sorted({(r["season"],r["week"]) for r in rows}):
        week_rows=[r for r in rows if (r["season"],r["week"])==key]
        pending=[]
        for r in week_rows:
            p,a=r["projected"],r["actual"]
            if p is None or a is None:continue
            player=r["player_id"]; pos=r["position_id"]
            prior=history[player]; prior_pos=pos_history[pos]
            # shrink individual residual to zero, position residual to zero
            player_adj=sum(prior)/(len(prior)+12)
            pos_adj=sum(prior_pos)/(len(prior_pos)+100)
            adjusted=p+player_adj+pos_adj
            predictions.append({"season":r["season"],"week":r["week"],"player_id":player,
                                "position_id":pos,"espn":p,"adjusted":adjusted,"actual":a,
                                "prior_player_weeks":len(prior)})
            pending.append((player,pos,a-p))
            if str(r["lineup_slot_id"]) not in ("20","21","22","24","25","26"):
                team_groups[(r["season"],r["week"],r["team_id"])].append((p,a))
        for player,pos,residual in pending:
            history[player].append(residual)
            pos_history[pos].append(residual)
    # Evaluate only weeks with at least 4 prior weeks in same season.
    test=[r for r in predictions if r["week"]>=5]
    baseline=metrics([(r["espn"],r["actual"]) for r in test])
    adjusted=metrics([(r["adjusted"],r["actual"]) for r in test])
    team_counts=Counter(len(v) for v in team_groups.values())
    result={
        "rows":len(rows),"unique_players":len({r["player_id"] for r in rows}),
        "duplicate_player_team_week_keys":duplicate_keys,
        "paired":metrics(all_pairs),
        "by_position":{k:metrics(v) for k,v in sorted(position.items())},
        "by_season":{k:metrics(v) for k,v in sorted(season.items())},
        "rolling_test_scope":"weeks >=5, historical weeks only; pooled past seasons and weeks",
        "rolling_espn_only":baseline,
        "rolling_player_plus_position_residual":adjusted,
        "team_candidate_slot_counts":dict(sorted(team_counts.items())),
        "warnings":[
            "Historical ESPN projections have NOT been verified as pregame snapshots.",
            "Team lineup slot classification and official matchup totals are NOT validated here.",
            "Week 8 2026 may have incomplete scores; exclude until verified.",
            "Rolling player adjustment is a research baseline, not a recommended production model."
        ]}
    (out/"validation.json").write_text(json.dumps(result,indent=2))
    with (out/"rolling_predictions.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(predictions[0]) if predictions else ["season"])
        writer.writeheader();writer.writerows(predictions)
    print(json.dumps(result,indent=2))
    if duplicate_keys:raise SystemExit("Duplicate player-team-week rows detected")

if __name__=="__main__":
    main()
