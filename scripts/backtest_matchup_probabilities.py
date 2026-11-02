"""Read-only chronological CGL matchup probability research.

Uses reconciled team-week scores; excludes incomplete matchups. Models are
calibrated using earlier weeks only, evaluated on identical held-out games.
"""
import argparse,csv,json,math
from collections import defaultdict,Counter
from pathlib import Path

SQRT2=math.sqrt(2)
def normcdf(x):return .5*math.erfc(-x/SQRT2)
def sd(values):
    if len(values)<2:return None
    m=sum(values)/len(values)
    return math.sqrt(sum((x-m)**2 for x in values)/(len(values)-1))
def clip(p):return max(1e-6,min(1-1e-6,p))
def score(games):
    if not games:return {"n":0}
    bs=sum((p-y)**2 for p,y in games)/len(games)
    ll=-sum(y*math.log(clip(p))+(1-y)*math.log(clip(1-p)) for p,y in games)/len(games)
    bins=[]
    for lo in (0,.1,.2,.3,.4,.5,.6,.7,.8,.9):
        vals=[(p,y) for p,y in games if lo<=p<(lo+.1 if lo<.9 else 1.000001)]
        if vals:bins.append({"predicted_bin":f"{lo:.1f}-{lo+.1:.1f}","n":len(vals),
                             "mean_predicted":round(sum(p for p,y in vals)/len(vals),4),
                             "actual_win_rate":round(sum(y for p,y in vals)/len(vals),4)})
    return {"n":len(games),"brier":round(bs,5),"log_loss":round(ll,5),
            "calibration_bins":bins}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--team-csv",default="team-uncertainty-research/team_reconciliation.csv")
    ap.add_argument("--output",default="matchup-probability-research")
    ap.add_argument("--min-history",type=int,default=60)
    args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with open(args.team_csv,newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    def valid(r):return r["reconciled"].lower()=="true"
    # Weekly actual scores, paired by matchup. Matchup membership must be obtained
    # from ESPN schedule; never infer opponents from score ordering.
    from scripts.discover_espn_history import build_session,endpoint
    import requests,time
    session=build_session()
    seasons=sorted({int(r["season"]) for r in rows})
    schedule={};errors=[]
    for season in seasons:
        try:
            response=session.get(endpoint(1877457250,season),params={"view":"mMatchupScore"},timeout=60)
            response.raise_for_status()
            games=response.json().get("schedule",[])
            schedule[season]=games
        except (requests.RequestException,ValueError) as exc:
            errors.append({"season":season,"error":str(exc)[:150]})
    by_team={(int(r["season"]),int(r["week"]),str(r["team_id"])):r for r in rows if valid(r)}
    matchup_rows=[]
    for season,games in schedule.items():
        for g in games:
            home=g.get("home") or {};away=g.get("away") or {}
            if home.get("teamId") is None or away.get("teamId") is None:continue
            period=int(g.get("matchupPeriodId") or 0)
            for week in range(1,19):
                # Explicit weekly scoring maps are authoritative for multiweek rounds.
                # For normal single-week matchups, period == week.
                if week!=period and not (str(week) in (home.get("pointsByScoringPeriod") or {})
                                         and str(week) in (away.get("pointsByScoringPeriod") or {})):
                    continue
                a=by_team.get((season,week,str(home["teamId"])))
                b=by_team.get((season,week,str(away["teamId"])))
                if not a or not b:continue
                ah=float(a["reconstructed_actual"]);bh=float(b["reconstructed_actual"])
                # Exclude ties from binary win-probability scoring.
                if abs(ah-bh)<1e-8:continue
                matchup_rows.append({"season":season,"week":week,"matchup_id":g.get("id"),
                    "home_team":home["teamId"],"away_team":away["teamId"],
                    "home_projected":float(a["projected"]),"away_projected":float(b["projected"]),
                    "home_actual":ah,"away_actual":bh,"home_win":int(ah>bh)})
    # Guard against schedule duplicates.
    uniq={}
    for r in matchup_rows:uniq[(r["season"],r["week"],r["matchup_id"])]=r
    matchup_rows=sorted(uniq.values(),key=lambda r:(r["season"],r["week"],r["matchup_id"]))
    teams_by_week=defaultdict(list)
    for r in rows:
        if valid(r):teams_by_week[(int(r["season"]),int(r["week"]))].append(
            float(r["reconstructed_actual"])-float(r["projected"]))
    models={m:[] for m in ("fixed18","fixed21_12","rolling_team_sd","rolling_matchup_sd")}
    records=[];past_team=[];past_matchup=[]
    for season,week in sorted(set(teams_by_week)|{(r["season"],r["week"]) for r in matchup_rows}):
        group=[r for r in matchup_rows if (r["season"],r["week"])==(season,week)]
        team_sd=sd(past_team);match_sd=sd(past_matchup)
        for r in group:
            diff=r["home_projected"]-r["away_projected"]
            outcomes={}
            for name,denom in (("fixed18",18*SQRT2),("fixed21_12",21.12*SQRT2),
                               ("rolling_team_sd",team_sd*SQRT2 if team_sd is not None else None),
                               ("rolling_matchup_sd",match_sd)):
                if name.startswith("rolling") and len(past_team if name=="rolling_team_sd" else past_matchup)<args.min_history:continue
                if denom is None or denom<=0:continue
                p=clip(normcdf(diff/denom))
                outcomes[name]=p
                models[name].append((p,r["home_win"]))
            records.append({**r,**{name:outcomes.get(name) for name in models}})
        # Only incorporate outcomes AFTER all same-week predictions have been made.
        past_team.extend(teams_by_week.get((season,week),[]))
        past_matchup.extend(r["home_actual"]-r["home_projected"]-(r["away_actual"]-r["away_projected"]) for r in group)
    # Fair paired evaluation: compare models on the same games where all four exist.
    paired=[r for r in records if all(r.get(name) is not None for name in models)]
    result={"source_team_weeks":len(rows),"complete_matchups":len(matchup_rows),
            "schedule_fetch_errors":errors,"min_history":args.min_history,
            "model_scores_all_available":{name:score(games) for name,games in models.items()},
            "model_scores_common_test":{name:score([(r[name],r["home_win"]) for r in paired]) for name in models},
            "common_test_games":len(paired),
            "warnings":["Historical ESPN projections may have been revised after games.",
                        "21.12 is an in-sample historical reference, NOT an honest pregame-calibrated model.",
                        "Matchup errors may be correlated; rolling matchup SD measures historical difference errors.",
                        "Does not yet evaluate player-position-specific uncertainty or actual pregame lineup decisions.",
                        "Do not deploy until point-in-time projections and out-of-sample validation are established."]}
    (out/"summary.json").write_text(json.dumps(result,indent=2))
    if records:
        with (out/"matchup_predictions.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(json.dumps(result,indent=2))
    if errors or not paired:raise SystemExit("Missing schedule or no common held-out matchup sample")
if __name__=="__main__":main()
