#!/usr/bin/env python3
"""Download and inventory historical ESPN fantasy-football league data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

DEFAULT_LEAGUE_ID = 1877457250
DEFAULT_SEASONS = (2024, 2025, 2026)
DEFAULT_WEEKS = range(1, 19)
BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"

LEAGUE_VIEWS = (
    "mSettings",
    "mStatus",
    "mTeam",
    "mRoster",
    "mMatchup",
    "mMatchupScore",
    "mStandings",
    "mDraftDetail",
    "mTransactions2",
)
WEEKLY_VIEWS = (
    "mMatchup",
    "mMatchupScore",
    "mBoxscore",
    "mRoster",
)


@dataclass
class Result:
    season: int
    scope: str
    view: str
    ok: bool
    status_code: int | None
    path: str | None
    top_level: str | None
    item_count: int | None
    keys: list[str]
    error: str | None


def endpoint(league_id: int, season: int) -> str:
    return (
        f"{BASE_URL}/seasons/{season}/segments/0/"
        f"leagues/{league_id}"
    )


def summarize(payload: Any) -> tuple[str, int | None, list[str]]:
    if isinstance(payload, dict):
        return "object", len(payload), sorted(str(key) for key in payload.keys())
    if isinstance(payload, list):
        keys: list[str] = []
        if payload and isinstance(payload[0], dict):
            keys = sorted(str(key) for key in payload[0].keys())
        return "array", len(payload), keys
    return type(payload).__name__, None, []


def fetch(
    session: requests.Session,
    url: str,
    view: str,
    output_path: Path,
    season: int,
    scope: str,
    scoring_period: int | None = None,
) -> Result:
    params: list[tuple[str, str | int]] = [("view", view)]
    if scoring_period is not None:
        params.append(("scoringPeriodId", scoring_period))

    try:
        response = session.get(url, params=params, timeout=45)
        response.raise_for_status()
        payload = response.json()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        top_level, item_count, keys = summarize(payload)
        return Result(
            season, scope, view, True, response.status_code,
            str(output_path), top_level, item_count, keys, None,
        )
    except (requests.RequestException, ValueError) as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return Result(
            season, scope, view, False, status,
            None, None, None, [], str(exc),
        )


def load_env_file(path: Path) -> None:
    """Load simple KEY=value entries without another dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "CGL-Record-Book/0.1 (+historical league archive)",
        "Accept": "application/json",
    })
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("ESPN_SWID") or os.getenv("SWID")
    if espn_s2 and swid:
        session.cookies.update({"espn_s2": espn_s2, "SWID": swid})
    return session


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# ESPN Historical Discovery",
        "",
        f"- Generated: {report['generated_at']}",
        f"- League ID: {report['league_id']}",
        f"- Seasons: {', '.join(map(str, report['seasons']))}",
        "",
        "| Season | Scope | View | Result | HTTP | Shape | Items |",
        "|---:|---|---|---|---:|---|---:|",
    ]
    for row in report["results"]:
        result = "available" if row["ok"] else "failed"
        lines.append(
            f"| {row['season']} | {row['scope']} | {row['view']} | "
            f"{result} | {row['status_code'] or ''} | "
            f"{row['top_level'] or ''} | {row['item_count'] if row['item_count'] is not None else ''} |"
        )
    lines.extend([
        "",
        "A view marked available returned valid JSON; it still needs field-level inspection before record calculations are implemented.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league-id", type=int, default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--seasons", type=int, nargs="+", default=list(DEFAULT_SEASONS))
    parser.add_argument("--start-week", type=int, default=1)
    parser.add_argument("--end-week", type=int, default=18)
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--delay", type=float, default=0.15)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.start_week < 1 or args.end_week < args.start_week:
        raise SystemExit("Invalid week range.")

    load_env_file(args.env_file)
    session = build_session()
    if not (os.getenv("ESPN_S2") and (os.getenv("ESPN_SWID") or os.getenv("SWID"))):
        print(
            "Warning: ESPN credentials were not found. "
            "Public leagues may work; private leagues will fail.",
            file=sys.stderr,
        )
    results: list[Result] = []

    for season in args.seasons:
        url = endpoint(args.league_id, season)
        for view in LEAGUE_VIEWS:
            path = args.output / "raw" / str(season) / "league" / f"{view}.json"
            result = fetch(session, url, view, path, season, "league")
            results.append(result)
            detail = "" if result.ok else f" ({result.status_code or 'error'}: {result.error})"
            print(f"{season} league {view}: {'OK' if result.ok else 'FAILED'}{detail}")
            time.sleep(args.delay)

        for week in range(args.start_week, args.end_week + 1):
            for view in WEEKLY_VIEWS:
                path = (
                    args.output / "raw" / str(season) / "weeks"
                    / f"{week:02d}" / f"{view}.json"
                )
                result = fetch(
                    session, url, view, path, season,
                    f"week-{week:02d}", week,
                )
                results.append(result)
                print(
                    f"{season} week {week:02d} {view}: "
                    f"{'OK' if result.ok else 'FAILED'}"
                    f"{'' if result.ok else ' (' + str(result.status_code or 'error') + ': ' + str(result.error) + ')'}"
                )
                time.sleep(args.delay)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "league_id": args.league_id,
        "seasons": args.seasons,
        "week_range": [args.start_week, args.end_week],
        "results": [asdict(result) for result in results],
    }
    reports = args.output / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "espn_history_discovery.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (reports / "espn_history_discovery.md").write_text(
        markdown_report(report), encoding="utf-8"
    )

    successes = sum(result.ok for result in results)
    print(f"Completed: {successes}/{len(results)} requests returned JSON.")
    print(f"Report: {reports / 'espn_history_discovery.md'}")
    return 0 if successes else 1


if __name__ == "__main__":
    sys.exit(main())
