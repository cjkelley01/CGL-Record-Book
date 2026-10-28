"""Targeted, non-production inspection of ESPN player projection response shapes.

Run manually with ESPN_S2/ESPN_SWID credentials. Prints aggregate counts only.
No raw ESPN data, cookies, or player identifiers are written to disk.
"""
import argparse
import json
from collections import Counter

from scripts.discover_espn_history import build_session, endpoint, DEFAULT_LEAGUE_ID


def summarize(entries, week):
    result = {"entries": len(entries), "with_stats": 0, "source_periods": Counter(),
              "target_week_projections": 0, "stat_fields": Counter()}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        player = entry.get("player") or (entry.get("playerPoolEntry") or {}).get("player") or {}
        stats = player.get("stats") or []
        if stats:
            result["with_stats"] += 1
        for stat in stats:
            if not isinstance(stat, dict):
                continue
            result["source_periods"][f"{stat.get('statSourceId')}:{stat.get('scoringPeriodId')}"] += 1
            result["stat_fields"][",".join(sorted(stat))] += 1
            if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == week and isinstance(stat.get("appliedTotal"), (int, float)):
                result["target_week_projections"] += 1
    return {k: dict(v) if isinstance(v, Counter) else v for k, v in result.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-id", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=9)
    args = parser.parse_args()
    session = build_session()
    url = endpoint(args.league_id, args.season) + "/players"
    scenarios = [
        ("baseline", {"view": "kona_player_info", "scoringPeriodId": args.week}, None),
        ("filter_scoring_period", {"view": "kona_player_info", "scoringPeriodId": args.week},
         {"players": {"limit": 150, "offset": 0, "filterStatsForScoringPeriodIds": {"value": [args.week]}}}),
        ("playercard", {"view": "kona_playercard", "scoringPeriodId": args.week},
         {"players": {"limit": 150, "offset": 0, "filterStatsForScoringPeriodIds": {"value": [args.week]}}}),
    ]
    for name, params, filter_value in scenarios:
        try:
            headers = {"x-fantasy-filter": json.dumps(filter_value)} if filter_value else {}
            response = session.get(url, params=params, headers=headers, timeout=45)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                print(json.dumps({"scenario": name, "error": "non-list response"}))
                continue
            print(json.dumps({"scenario": name, **summarize(payload, args.week)}, sort_keys=True))
        except Exception as exc:
            print(json.dumps({"scenario": name, "error_type": type(exc).__name__,
                              "status_code": getattr(getattr(exc, "response", None), "status_code", None)}))


if __name__ == "__main__":
    main()
