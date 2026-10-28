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
    limit, offset, entries, seen = 250, 0, [], set()
    for _ in range(80):
        filters = {"players": {"filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
                               "limit": limit, "offset": offset}}
        response = session.get(url, params={"view": "kona_player_info",
                               "scoringPeriodId": week},
                               headers={"x-fantasy-filter": json.dumps(filters)}, timeout=45)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected ESPN free-agent response type: {type(payload).__name__}")
        if not payload:
            break
        ids = []
        for entry in payload:
            if not isinstance(entry, dict):
                raise ValueError("Unexpected ESPN player entry type")
            player = entry.get("player") or (entry.get("playerPoolEntry") or {}).get("player") or {}
            pid = player.get("id")
            if pid is None:
                raise ValueError("ESPN waiver entry missing player ID")
            ids.append(int(pid))
        if len(ids) != len(set(ids)) or any(pid in seen for pid in ids):
            raise ValueError("ESPN repeated player page; refusing incomplete waiver pool")
        seen.update(ids)
        entries.extend(payload)
        offset += len(payload)
        if len(payload) < limit:
            break
    else:
        raise ValueError("ESPN player pagination exceeded safety limit")
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
