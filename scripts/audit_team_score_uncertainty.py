"""Read-only team score reconciliation and chronological uncertainty backtest."""
import argparse, csv, json, math, time
from collections import defaultdict, Counter
from pathlib import Path
from scripts.discover_espn_history import build_session, endpoint

BENCH={20,21}
def num(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

def fetch(session,league,season,week):
    last=None
    for attempt in range(3):
        try:
            r=session.get(endpoint(league,season),params=[("view","mMatchup"),("view","mMatchupScore"),("scoringPeriodId",week)],timeout=60)
            r.raise_for_status();return r.json()
        except Exception as e:
            last=e;time.sleep(attempt+1)
    raise last

def official_scores(payload, week):
    """Only consider the requested matchup period; never read an unrelated game.

    For single-week periods, totalPoints is eligible for comparison. For multiweek
    periods, only explicitly reported week-level points may be used.
    Non-matching/zero-valued totals are still audited, never silently accepted.
    """
    result = {}
    audit = Counter()
    games = payload.get("schedule", [])
    selected = [g for g in games if (
        g.get("matchupPeriodId") == week
        or any(str(week) in ((g.get(side) or {}).get("pointsByScoringPeriod") or {})
               for side in ("home", "away"))
    )]
    audit["all_schedule_games"] = len(games)
    audit["matching_period_games"] = len(selected)
    for game in selected:
        for side in ("home", "away"):
            obj = game.get(side) or {}
            tid = obj.get("teamId")
            if tid is None:
                continue
            period = obj.get("pointsByScoringPeriod") or {}
            numeric_periods = {int(k): num(v) for k, v in period.items()
                               if str(k).isdigit()}
            val = numeric_periods.get(week)
            source = "pointsByScoringPeriod"
            if val is None:
                if game.get("matchupPeriodId") != week:
                    source = "other_period_no_weekly"
                elif numeric_periods and len(numeric_periods) > 1:
                    source = "multiweek_missing_weekly"
                else:
                    val = num(obj.get("totalPoints"))
                    source = "single_period_totalPoints_CANDIDATE"
            if val is not None:
                result[str(tid)] = (val, source)
                audit["candidate_" + source] += 1
            else:
                audit["missing_score"] += 1
    return result, dict(audit)

def stdev(xs):
    return math.sqrt(sum((x-sum(xs)/len(xs))**2 for x in xs)/(len(xs)-1)) if len(xs)>1 else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="historical-player-dataset/player_weeks.csv")
    ap.add_argument("--output",default="team-uncertainty-research")
    ap.add_argument("--league-id",type=int,default=1877457250)
    args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    with open(args.input,newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    groups=defaultdict(list)
    for r in rows:groups[(int(r["season"]),int(r["week"]),r["team_id"])].append(r)
    session=build_session()
    weeks=sorted({(s,w) for s,w,t in groups})
    official={};fetch_errors=[];source_audit={}
    for season,week in weeks:
        try:official[(season,week)],source_audit[f'{season}:{week}']=official_scores(fetch(session,args.league_id,season,week),week)
        except Exception as exc:
            fetch_errors.append({"season":season,"week":week,"error":str(exc)[:180]})
        time.sleep(.1)
    team_rows=[];all_errors=[];by_season=defaultdict(list);by_week=defaultdict(list)
    for (season,week,team),members in sorted(groups.items()):
        starters=[r for r in members if int(r["lineup_slot_id"]) not in BENCH]
        missing=[r["player_name"] for r in starters if num(r["actual"]) is None or num(r["projected"]) is None]
        projected=sum(num(r["projected"]) or 0 for r in starters)
        actual=sum(num(r["actual"]) or 0 for r in starters)
        off,source=official.get((season,week),{}).get(team,(None,"missing"))
        diff=actual-off if off is not None and not missing else None
        valid=(not missing and off is not None
               and source in ("pointsByScoringPeriod", "single_period_totalPoints_CANDIDATE")
               and abs(diff)<.02)
        record={"season":season,"week":week,"team_id":team,"starter_count":len(starters),
                "missing_starter_count":len(missing),"projected":round(projected,4),
                "reconstructed_actual":round(actual,4),"official":off,"official_source":source,
                "reconciliation_delta":round(diff,4) if diff is not None else None,
                "reconciled":valid}
        team_rows.append(record)
        if valid:
            error=actual-projected
            all_errors.append(error);by_season[season].append(error);by_week[(season,week)].append(error)
    # Prequential uncertainty: calibrate SD only from prior weeks; assess empirical interval coverage.
    historical=[];coverage={18:{"n":0,"within":0}, "rolling":{"n":0,"within":0}}
    for season,week in weeks:
        current=[r for r in team_rows if (r["season"],r["week"])==(season,week) and r["reconciled"]]
        past_sd=stdev(historical)
        for r in current:
            err=r["reconstructed_actual"]-r["projected"]
            coverage[18]["n"]+=1;coverage[18]["within"]+=abs(err)<=18*1.96
            if past_sd is not None and len(historical)>=40:
                coverage["rolling"]["n"]+=1;coverage["rolling"]["within"]+=abs(err)<=past_sd*1.96
        historical.extend(r["reconstructed_actual"]-r["projected"] for r in current)
    with (out/"team_reconciliation.csv").open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(team_rows[0]));wr.writeheader();wr.writerows(team_rows)
    summary={"team_weeks":len(team_rows),"official_weeks_fetched":len(official),"fetch_errors":fetch_errors,
             "reconciled_team_weeks":sum(r["reconciled"] for r in team_rows),
             "missing_official":sum(r["official"] is None for r in team_rows),
             "unverified_official_period":sum(r["official_source"]=="single_period_totalPoints_CANDIDATE" and not r["reconciled"] for r in team_rows),
             "source_audit":source_audit,
             "nonmatching_complete":sum(r["reconciliation_delta"] is not None and abs(r["reconciliation_delta"])>=.02 for r in team_rows),
             "matched_explicit_period":sum(r["reconciled"] and r["official_source"]=="pointsByScoringPeriod" for r in team_rows),
             "matched_single_period_totals":sum(r["reconciled"] and r["official_source"]=="single_period_totalPoints_CANDIDATE" for r in team_rows),
             "incomplete_starter_rows":sum(r["missing_starter_count"]>0 for r in team_rows),
             "starter_count_distribution":dict(Counter(r["starter_count"] for r in team_rows)),
             "reconciled_error_sd":stdev(all_errors),
             "reconciled_error_bias":sum(all_errors)/len(all_errors) if all_errors else None,
             "reconciled_error_by_season":{str(k):{"n":len(v),"sd":stdev(v)} for k,v in by_season.items()},
             "interval_95_coverage":{str(k):{"n":v["n"],"fraction":v["within"]/v["n"] if v["n"] else None} for k,v in coverage.items()},
             "warnings":["Historical ESPN projections not verified as pregame snapshots.",
                         "This tests team scoring-error dispersion, not full matchup probability calibration.",
                         "Two-week playoff totalPoints never used for verified reconciliation.",
                         "Do not deploy a new variance assumption without out-of-sample matchup validation."]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    if not official:raise SystemExit("No official scores available")
if __name__=="__main__":main()
