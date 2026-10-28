"""Fetch ESPN free-agent/waiver candidates for each forecast week.

Candidates must be explicitly unrostered in ESPN's response; failed or ambiguous
responses are left unavailable rather than manufacturing replacement scores.
"""
import argparse
import json
from pathlib import Path

from scripts.discover_espn_history import build_session, endpoint, DEFAULT_LEAGUE_ID


def fetch_pool(session, league_id, season, week, output):
    """Fetch every ESPN page; never treat a truncated player pool as complete."""
    url = endpoint(league_id, season) + "/players"
    # ESPN has been observed ignoring the offset and repeating the first page.
    # Request the entire candidate set at once, and reject a capped response
    # rather than silently treating a partial waiver pool as complete.
    limit = 10000
    filters = {"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
                           "limit": limit, "offset": 0}}
    response = session.get(url, params={"view": "kona_player_info",
                           "scoringPeriodId": week},
                           headers={"x-fantasy-filter": json.dumps(filters)}, timeout=90)
    response.raise_for_status()
    entries = response.json()
    if not isinstance(entries, list):
        raise ValueError(f"Unexpected ESPN free-agent response type: {type(entries).__name__}")
    if len(entries) >= limit:
        raise ValueError("ESPN waiver response reached requested limit; refusing possibly truncated pool")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Unexpected ESPN player entry type")
        player = entry.get("player") or (entry.get("playerPoolEntry") or {}).get("player") or {}
        pid = player.get("id")
        if pid is None:
            raise ValueError("ESPN waiver entry missing player ID")
        if int(pid) in seen:
            raise ValueError("ESPN waiver response contains duplicate player IDs")
        seen.add(int(pid))
    if not entries:
        raise ValueError("ESPN returned no free-agent candidates")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries), encoding="utf-8")
    return len(entries)


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
        except Exception as exc:
            path.unlink(missing_ok=True)
            print(f"Week {week}: waiver pool unavailable ({type(exc).__name__}: {str(exc)[:180]})")


if __name__ == "__main__":
    main()
