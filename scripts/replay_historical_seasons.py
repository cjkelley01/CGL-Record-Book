"""Leakage-controlled historical CGL season replay.

All simulated future-week means are constructed from PREVIOUS completed weeks.
The last observed ESPN projected starter score is a labeled persistence proxy,
NOT an actual future-week ESPN projection or a validated future lineup.
"""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
from scripts.analytics.weekly_forecast import simulate

def truth(season):
    games=[g for g in season["matchups"] if g["stage"]=="regular_season"]
    if not games or any(not g["decided"] or g["home_score"] is None or g["away_score"] is None for g in games):
        return None
    wins=defaultdict(float);points=defaultdict(float)
    for g in games:
        a,b=int(g["home_team_id"]),int(g["away_team_id"])
        x,y=float(g["home_score"]),float(g["away_score"])
        wins[a]+=(x>y)+.5*(x==y);wins[b]+=(y>x)+.5*(x==y)
        points[a]+=x;points[b]+=y
    ids=[int(t["team_id"]) for t in season["teams"]]
    ordered=sorted(ids,key=lambda tid:(-wins[tid],-points[tid],tid))
    return {"playoffs":set(ordered[:6]),"bye":set(ordered[:2]),"rank":{tid:i for i,tid in enumerate(ordered,1)}}


def historical_bracket(season,actual):
    """Accept only a verifiable six-team, three-round historical championship."""
    games=[g for g in season["matchups"] if g.get("stage")=="championship_playoffs"]
    if int(season.get("settings",{}).get("playoff_team_count") or 0)!=6:
        return None,None,"historical playoff field is not six teams"
    groups=defaultdict(list)
    for g in games:
        if g.get("playoff_round") is not None:
            groups[int(g["playoff_round"])].append(g)
    if len(groups)!=3:
        return None,None,"cannot verify three championship rounds"
    rounds=[]
    for rnd in sorted(groups):
        periods={int(p) for g in groups[rnd] for p in g.get("scoring_periods",[])}
        if not periods:
            return None,None,"missing playoff scoring periods"
        rounds.append(tuple(sorted(periods)))
    if any(set(rounds[i])&set(rounds[j]) for i in range(3) for j in range(i+1,3)):
        return None,None,"overlapping playoff rounds"
    if not (max(rounds[0])<min(rounds[1]) and max(rounds[1])<min(rounds[2])):
        return None,None,"nonchronological playoff rounds"
    final=groups[max(groups)]
    if len(final)!=1 or final[0].get("winner") not in ("HOME","AWAY") or not final[0].get("decided"):
        return None,None,"missing unambiguous completed championship final"
    champion=int(final[0][final[0]["winner"].lower()+"_team_id"])
    if champion not in actual["playoffs"]:
        return None,None,"champion not in reconstructed top six"
    # Validate actual recorded opening round against 3v6 and 4v5 pairings.
    rank={v:k for k,v in actual["rank"].items()}
    expected={frozenset((rank[3],rank[6])),frozenset((rank[4],rank[5]))}
    observed={frozenset((int(g["home_team_id"]),int(g["away_team_id"]))) for g in groups[min(groups)]
              if g.get("home_team_id") is not None and g.get("away_team_id") is not None}
    if observed!=expected:
        return None,None,"historical opening bracket differs from simulator's seeded bracket"
    return tuple(rounds),champion,None

def replay(seasons,team_rows,*,cutoffs=(4,7,10,12),trials=2000,weights=(0,.1,.2,.4),deviation=18):
    observed=defaultdict(dict)
    for r in team_rows:
        if r["reconciled"].lower()=="true":
            observed[(int(r["season"]),int(r["week"]))][int(r["team_id"])]=float(r["projected"])
    rows=[];skips=[]
    for season in seasons:
        yr=season["season"];actual=truth(season)
        if actual is None:
            skips.append({"season":yr,"reason":"regular season incomplete"});continue
        bracket,champion,bracket_reason=historical_bracket(season,actual)
        if bracket_reason:
            skips.append({"season":yr,"championship_validation":bracket_reason})
        regular=[g for g in season["matchups"] if g["stage"]=="regular_season"]
        final_week=max(int(g["matchup_period"]) for g in regular)
        ids=[int(t["team_id"]) for t in season["teams"]]
        for cutoff in cutoffs:
            if cutoff>=final_week:continue
            past=[g for g in regular if int(g["matchup_period"])<=cutoff]
            if not past or any(not g["decided"] for g in past):
                skips.append({"season":yr,"cutoff":cutoff,"reason":"missing prior results"});continue
            history=defaultdict(list)
            for g in past:
                for side in ("home","away"):
                    history[int(g[side+"_team_id"])].append(float(g[side+"_score"]))
            if any(not history[tid] for tid in ids):
                skips.append({"season":yr,"cutoff":cutoff,"reason":"incomplete team scoring history"});continue
            # Last available past-week ESPN starter projection, never a future value.
            last={}
            for week in range(1,cutoff+1):
                for tid,projected in observed[(yr,week)].items():last[tid]=projected
            if any(tid not in last for tid in ids):
                skips.append({"season":yr,"cutoff":cutoff,"reason":"missing prior ESPN projection baseline"});continue
            partial={**season,"matchups":[{**g,"decided":False,"home_score":None,"away_score":None}
                if g["stage"]=="regular_season" and int(g["matchup_period"])>cutoff else g
                for g in season["matchups"]]}
            future_weeks=set(int(g["matchup_period"]) for g in regular if int(g["matchup_period"])>cutoff)
            future_weeks.update(week for round_weeks in (bracket or ((15,),(16,),(17,18))) for week in round_weeks)
            for weight in weights:
                means={tid:{week:weight*(sum(history[tid])/len(history[tid]))+
                          (1-weight)*last[tid] for week in future_weeks} for tid in ids}
                result=simulate(partial,means,trials=trials,seed=2026+yr*100+cutoff,deviation=deviation,
                    playoff_weeks=bracket or ((15,),(16,),(17,18)))
                for t in result["teams"]:
                    tid=t["team_id"]
                    rows.append({"season":yr,"cutoff":cutoff,"team_id":tid,
                        "weight":weight,"playoff_probability":t["playoff_probability"],
                        "bye_probability":t["bye_probability"],
                        "championship_probability":t["championship_probability"],
                        "playoff_actual":int(tid in actual["playoffs"]),
                        "bye_actual":int(tid in actual["bye"]),
                        "actual_seed":actual["rank"][tid],
                        "championship_actual":int(tid==champion) if bracket else None,
                        "championship_bracket_verified":bool(bracket),
                        "future_projection_source":"last observed completed-week ESPN starter projection (persistence proxy)"})
    return rows,skips

def metrics(rows,pred,actual):
    if not rows:return {"n":0}
    return {"n":len(rows),"brier":round(sum((float(r[pred])-int(r[actual]))**2 for r in rows)/len(rows),6),
            "mean_predicted":round(sum(float(r[pred]) for r in rows)/len(rows),4),
            "observed_rate":round(sum(int(r[actual]) for r in rows)/len(rows),4)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="app/data/core_history.json")
    p.add_argument("--team-csv",default="team-uncertainty-research/team_reconciliation.csv")
    p.add_argument("--output",default="historical-season-replay")
    p.add_argument("--trials",type=int,default=2000)
    a=p.parse_args()
    seasons=json.loads(Path(a.history).read_text())["seasons"]
    with open(a.team_csv,newline="",encoding="utf-8") as f:teams=list(csv.DictReader(f))
    rows,skips=replay(seasons,teams,trials=a.trials)
    if not rows:raise SystemExit("No eligible historical replay cutoffs")
    result={"cutoffs":sorted({(r["season"],r["cutoff"]) for r in rows}),
      "scores_by_weight":{str(w):{"playoffs":metrics([r for r in rows if r["weight"]==w],
          "playoff_probability","playoff_actual"),"byes":metrics([r for r in rows if r["weight"]==w],
          "bye_probability","bye_actual")} for w in sorted({r["weight"] for r in rows})},
      "championship_scores_by_weight":{str(w):metrics([r for r in rows if r["weight"]==w and r["championship_bracket_verified"]],
          "championship_probability","championship_actual") for w in sorted({r["weight"] for r in rows})},
      "skips":skips,
      "championship_validation":"Scored only where the historical championship has a verified six-team, three-round bracket with matching opening seeds; otherwise excluded.",
      "limitations":["All future projections are prior-week persistence proxies; actual future-week ESPN projections and future rosters are NOT reconstructed.",
       "Multiple cutoffs from the same season are correlated; team rows are not independent trials.",
       "Weights are exploratory; no weight selection should be made from these same evaluation outcomes.",
       "Playoff and bye outcomes are computed from final regular-season wins and points for, not ESPN playoff-seed metadata.",
       "Historical championship probabilities are scored only for verified compatible brackets; others are diagnostic simulations.",
       "Only completed historical seasons are scored."]}
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"
")
    with (out/"team_probabilities.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
