"""Chronological weight sweep with a prior-week-only weight selector.

Uses the existing reconciled team projections and matchup outcomes. Research
only: lineup is historical actual lineup, not a reconstructed future optimizer.
"""
import argparse,csv,json,math
from collections import defaultdict,Counter
from pathlib import Path

WEIGHTS=(0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1)
def probability(diff):return max(1e-6,min(1-1e-6,.5*math.erfc(-diff/36)))
def brier(p,y):return (p-y)**2
def loss(p,y):return -(y*math.log(p)+(1-y)*math.log(1-p))
def summary(rows):
    if not rows:return {"n":0}
    return {"n":len(rows),"brier":round(sum(x["brier"] for x in rows)/len(rows),6),
            "log_loss":round(sum(x["log_loss"] for x in rows)/len(rows),6)}
def replay(team_rows,matchups,min_train):
    team=defaultdict(dict)
    for r in team_rows:
        if r["reconciled"].strip().lower()!="true":continue
        team[(int(r["season"]),int(r["week"]))][str(r["team_id"])]=r
    by_week=defaultdict(list)
    for g in matchups:
        by_week[(int(g["season"]),int(g["week"]))].append(g)
    history=defaultdict(list);train=defaultdict(list);out=[];selection=[]
    for season,week in sorted(set(team)|set(by_week)):
        eligible=[]
        for g in by_week[(season,week)]:
            h,a=str(g["home_team"]),str(g["away_team"])
            if h not in team[(season,week)] or a not in team[(season,week)]:continue
            if not history[(season,h)] or not history[(season,a)]:continue
            hr,ar=team[(season,week)][h],team[(season,week)][a]
            hist=sum(history[(season,h)])/len(history[(season,h)])-sum(history[(season,a)])/len(history[(season,a)])
            espn=float(hr["projected"])-float(ar["projected"])
            y=int(g["home_win"])
            eligible.append((g,hist,espn,y))
        # Select weight using only outcomes of earlier weeks. No same-week leakage.
        chosen=None
        if len(train[season][0])>=min_train:
            chosen=min(WEIGHTS,key=lambda w:(sum(train[season][w])/len(train[season][w]),w))
        for g,hist,espn,y in eligible:
            for w in WEIGHTS:
                p=probability(w*hist+(1-w)*espn)
                row={"season":season,"week":week,"matchup_id":g["matchup_id"],
                     "historical_weight":w,"home_win":y,"home_probability":round(p,8),
                     "brier":brier(p,y),"log_loss":loss(p,y)}
                out.append(row)
            if chosen is not None:
                p=probability(chosen*hist+(1-chosen)*espn)
                selection.append({"season":season,"week":week,"matchup_id":g["matchup_id"],
                    "chosen_weight":chosen,"home_win":y,"home_probability":round(p,8),
                    "brier":brier(p,y),"log_loss":loss(p,y),
                    "prior_training_matchups":len(train[season][0])})
        for g,hist,espn,y in eligible:
            for w in WEIGHTS:train[season][w].append(brier(probability(w*hist+(1-w)*espn),y))
        for tid,r in team[(season,week)].items():
            history[(season,tid)].append(float(r["reconstructed_actual"]))
    return out,selection

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--team-csv",default="team-uncertainty-research/team_reconciliation.csv")
    ap.add_argument("--matchup-csv",default="matchup-probability-research/matchup_predictions.csv")
    ap.add_argument("--min-train",type=int,default=30)
    ap.add_argument("--output",default="chronological-weight-research")
    args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with open(args.team_csv,newline="",encoding="utf-8") as f:teams=list(csv.DictReader(f))
    with open(args.matchup_csv,newline="",encoding="utf-8") as f:games=list(csv.DictReader(f))
    rows,selected=replay(teams,games,args.min_train)
    if not rows:raise SystemExit("No complete chronological matchups")
    scores={str(w):summary([r for r in rows if r["historical_weight"]==w]) for w in WEIGHTS}
    selected_keys={(r["season"],r["week"],r["matchup_id"]) for r in selected}
    comparable={str(w):summary([r for r in rows if r["historical_weight"]==w and
        (r["season"],r["week"],r["matchup_id"]) in selected_keys]) for w in WEIGHTS}
    result={"historical_weight_scores_all":scores,
            "walk_forward_selected":summary(selected),
            "common_sample_fixed_weights":comparable,
            "selected_weight_counts":dict(Counter(str(r["chosen_weight"]) for r in selected)),
            "walk_forward_min_prior_matchups_per_season":args.min_train,
            "caveats":["The 0-100% sweep is descriptive/in-sample; choosing the best sweep weight is hindsight.",
                       "Walk-forward selector only uses earlier matchup results in the SAME season; it has no selected prediction until minimum prior sample is reached.",
                       "ESPN projected totals come from retrospective API records; projection locking is not independently established by this test.",
                       "Historical starters are observed after the games, not reconstructed from a fixed pregame roster cutoff.",
                       "This is a matchup-score weight backtest, not the full future-week playoff simulation."]}
    (out/"summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for name,records in (("weight_predictions.csv",rows),("walk_forward_selected.csv",selected)):
        if records:
            with (out/name).open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
