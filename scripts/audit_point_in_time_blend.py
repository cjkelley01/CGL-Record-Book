"""Audit point-in-time evidence and chronologically backtest CGL's 40/60 blend.

This is a research approximation, NOT a reproduction of live future-roster
optimization. Missing pregame snapshots must not be relabeled as verified.
"""
import argparse,csv,json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

def cdf(x):return .5*math.erfc(-x/math.sqrt(2))
def metrics(items):
    if not items:return {"n":0}
    n=len(items)
    return {"n":n,"brier":round(sum((p-y)**2 for p,y in items)/n,6),
            "log_loss":round(-sum(y*math.log(max(1e-8,min(1-1e-8,p)))+
                              (1-y)*math.log(max(1e-8,min(1-1e-8,1-p))) for p,y in items)/n,6)}
def provenance(path):
    found=[]
    for file in sorted(Path(path).glob("*.json")):
        try:
            data=json.loads(file.read_text(encoding="utf-8"))
            at=data.get("generated_at")
            generated=datetime.fromisoformat(at.replace("Z","+00:00")) if at else None
            found.append({"file":str(file),"generated_at":at,
                "completed_through_week":data.get("completed_through_week"),
                "model_names":sorted((data.get("models") or {}).keys()),
                "has_player_level_pregame_snapshot":False,
                "has_team_level_future_forecast":bool(data.get("models")),
                "note":"Archived forecast summary; cannot establish historical ESPN player projection provenance."})
        except (OSError,ValueError,TypeError) as e:
            found.append({"file":str(file),"error":str(e)[:150]})
    return found

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--team-csv",default="team-uncertainty-research/team_reconciliation.csv")
    ap.add_argument("--matchup-csv",default="matchup-probability-research/matchup_predictions.csv")
    ap.add_argument("--archive",default="data/forecasts")
    ap.add_argument("--output",default="point-in-time-research")
    args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with open(args.team_csv,newline="",encoding="utf-8") as f:team=list(csv.DictReader(f))
    with open(args.matchup_csv,newline="",encoding="utf-8") as f:games=list(csv.DictReader(f))
    valid=defaultdict(dict)
    for r in team:
        if r["reconciled"].lower()=="true":
            valid[(int(r["season"]),int(r["week"]))][str(r["team_id"])]=r
    history=defaultdict(list);results=[];by_model=defaultdict(list)
    for season,week in sorted(valid):
        for g in (x for x in games if int(x["season"])==season and int(x["week"])==week):
            h,a=str(g["home_team"]),str(g["away_team"])
            if h not in valid[(season,week)] or a not in valid[(season,week)]:continue
            if not history[(season,h)] or not history[(season,a)]:continue
            home=valid[(season,week)][h];away=valid[(season,week)][a]
            hm=sum(history[(season,h)])/len(history[(season,h)])
            am=sum(history[(season,a)])/len(history[(season,a)])
            hp=float(home["projected"]);ap=float(away["projected"])
            y=int(g["home_win"])
            for model,diff in (("espn_only",hp-ap),("historical_only",hm-am),
                               ("blend_40_60",.4*(hm-am)+.6*(hp-ap))):
                p=cdf(diff/(18*math.sqrt(2)))
                by_model[model].append((p,y))
                results.append({"season":season,"week":week,"matchup_id":g["matchup_id"],
                                "model":model,"home_probability":round(p,6),"home_win":y,
                                "historical_games_home":len(history[(season,h)]),
                                "historical_games_away":len(history[(season,a)])})
        # No current week scoring leaks into its own pre-week historical mean.
        for tid,r in valid[(season,week)].items():
            history[(season,tid)].append(float(r["reconstructed_actual"]))
    archives=provenance(args.archive)
    summary={"archived_forecasts":archives,"archived_forecast_count":len(archives),
             "verified_player_pregame_snapshots":0,
             "chronological_blend_comparison":{k:metrics(v) for k,v in by_model.items()},
             "comparability":"All three methods evaluated on the same eligible matchups; historical means trained on earlier completed weeks in same season.",
             "critical_limitations":[
                 "ESPN historical player projections are retrieved after games; point-in-time correctness unverified.",
                 "Archived aggregate forecast outputs do not prove player-level pregame projection provenance.",
                 "Historical-only and 40/60 models are an approximation of production; live roster selection, future weeks, waiver replacement, byes, and playoff simulation are NOT reproduced.",
                 "Uses fixed 18-point Gaussian error and a shared eligible subset; no production model changes warranted.",
                 "Weeks without at least one earlier completed team score are excluded."]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    if results:
        with (out/"chronological_blend_predictions.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    print(json.dumps(summary,indent=2))
    if not results:raise SystemExit("No eligible chronological matchups")
if __name__=="__main__":main()
