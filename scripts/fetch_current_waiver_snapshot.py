"""Save an ESPN free-agent snapshot for current-week top-three replacement estimates."""
import argparse
import json
from pathlib import Path

from scripts.discover_espn_history import DEFAULT_LEAGUE_ID, build_session
from scripts.fetch_waiver_pool import fetch_pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-id", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--projection-week", type=int, required=True,
                        help="ESPN current scoring week with published free-agent projections")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()
    root = args.data_root / "raw" / str(args.season)
    temporary = root / "free_agent_snapshot_download.json"
    try:
        count = fetch_pool(build_session(), args.league_id, args.season,
                           args.projection_week, temporary)
        players = json.loads(temporary.read_text(encoding="utf-8"))
        target = root / "current_week_free_agents.json"
        target.write_text(json.dumps({"projection_week": args.projection_week,
                                      "players": players}), encoding="utf-8")
        print(f"Saved {count} ESPN free agents; projection source week {args.projection_week}")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
