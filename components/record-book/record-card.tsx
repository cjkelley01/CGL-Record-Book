"use client";

import { TeamLink } from "@/components/record-book/team-link";

import type { RecordEntry } from "@/lib/record-book/history";
import { names } from "@/lib/record-book/history";

export function RecordCard({
  label,
  title,
  record,
  value,
}: {
  label: string;
  title: string;
  record: RecordEntry;
  value: string;
}) {
  const matchup =
    record.points === undefined &&
    record.home_team_name &&
    record.away_team_name;
  const homeResult =
    (record.home_score ?? 0) === (record.away_score ?? 0)
      ? "T"
      : (record.home_score ?? 0) > (record.away_score ?? 0)
        ? "W"
        : "L";
  const awayResult = homeResult === "T" ? "T" : homeResult === "W" ? "L" : "W";
  return (
    <article className="record-card">
      <p className="eyebrow">{label}</p>
      <div className="record-value">{value}</div>
      {matchup ? (
        <div className="record-matchup">
          <div>
            <b><TeamLink season={record.season}>{record.home_team_name}</TeamLink></b>
            <i className={`result-${homeResult.toLowerCase()}`}>{homeResult}</i>
            <small>{names(record.home_manager_names)}</small>
          </div>
          <span>vs.</span>
          <div>
            <b><TeamLink season={record.season}>{record.away_team_name}</TeamLink></b>
            <i className={`result-${awayResult.toLowerCase()}`}>{awayResult}</i>
            <small>{names(record.away_manager_names)}</small>
          </div>
        </div>
      ) : (
        <>
          <h3>
            <TeamLink season={record.season}>{title}</TeamLink>
            {record.result && (
              <i className={`result-${record.result.toLowerCase()}`}>
                {record.result}
              </i>
            )}
          </h3>
          <p>{names(record.manager_names)}</p>
        </>
      )}
      <small>
        {record.season} · Week {record.scoring_period ?? record.matchup_period}
      </small>
    </article>
  );
}
