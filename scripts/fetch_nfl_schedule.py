"""Fetch NFL weekly game participants from ESPN's public scoreboard.

Schedule IDs are ESPN NFL proTeam IDs. Never infer a bye from missing data:
a week with fewer than 26 or more than 32 participating teams is rejected.
"""
import argparse
import json
from pathlib import Path
import requests


def fetch_schedule(season, weeks, output):
    session = requests.Session()
    result = {}
    for week in weeks:
        response = session.get(
            "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
            params={"dates": season, "seasontype": 2, "week": week, "limit": 100},
            timeout=45)
        response.raise_for_status()
        payload = response.json()
        ids = set()
        for event in payload.get("events", []):
            for competition in event.get("competitions", []):
                for competitor in competition.get("competitors", []):
                    ids.add(int(competitor["team"]["id"]))
        if not 26 <= len(ids) <= 32 or len(ids) % 2:
            raise ValueError(f"Week {week}: invalid NFL schedule ({len(ids)} teams)")
        result[str(week)] = sorted(ids)
        print(f"Week {week}: verified {len(ids)} NFL teams with games")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-week", type=int, default=8)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument("--output", type=Path, default=Path("data/raw/2026/nfl_schedule.json"))
    args = parser.parse_args()
    fetch_schedule(args.season, range(args.start_week, args.end_week + 1), args.output)


if __name__ == "__main__":
    main()
