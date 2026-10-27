"""Fetch ESPN free-agent/waiver candidates for each forecast week.

Candidates must be explicitly unrostered in ESPN's response; failed or ambiguous
responses are left unavailable rather than manufacturing replacement scores.
"""
import argparse
import json
from pathlib import Path

from scripts.discover_espn_history import build_session, endpoint, DEFAULT_LEAGUE_ID


def fetch_pool(session, league_id, season, week, output):
    url = endpoint(league_id, season) + "/players"
    filters = {"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
                           "limit": 1000, "offset": 0}}
    response = session.get(url, params={"view": "kona_player_info",
                           "scoringPeriodId": week},
                           headers={"x-fantasy-filter": json.dumps(filters)}, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Unexpected ESPN free-agent pool shape")
    # Never save a misleading partial pool: the ESPN API may cap responses.
    if len(payload) >= 1000:
        raise ValueError("ESPN pool reached page limit; cannot verify completeness")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload), encoding="utf-8")
    return len(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-id", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=9)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()
    session = build_session()
    for week in range(args.start_week, args.end_week + 1):
        path = args.data_root / "raw" / str(args.season) / "weeks" / f"{week:02d}" / "free_agents.json"
        try:
            count = fetch_pool(session, args.league_id, args.season, week, path)
            print(f"Week {week}: {count} free-agent candidates")
        except (ValueError, Exception) as exc:
            path.unlink(missing_ok=True)
            print(f"Week {week}: waiver pool unavailable ({type(exc).__name__})")


if __name__ == "__main__":
    main()
