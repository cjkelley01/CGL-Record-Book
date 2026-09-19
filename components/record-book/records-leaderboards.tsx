"use client";

import { TeamLink } from "@/components/record-book/team-link";

import type { LeaderRow, RecordLeaderboards } from "@/lib/record-book/history";
import { data, fmt, names } from "@/lib/record-book/history";

export function LeaderboardCard({
  title,
  rows,
  format,
  note,
}: {
  title: string;
  rows: LeaderRow[];
  format?: "percent" | "points" | "streak";
  note?: string;
}) {
  const value = (row: LeaderRow) =>
    format === "percent"
      ? `${(row.value * 100).toFixed(1)}%`
      : format === "points"
        ? fmt.format(row.value)
        : format === "streak"
          ? `${row.value} games`
          : fmt.format(row.value);
  return (
    <article className="leaderboard-card">
      <header>
        <h3>{title}</h3>
        {note && <small>{note}</small>}
      </header>
      <ol>
        {rows.map((row) => (
          <li key={`${row.rank}:$<TeamLink season={row.season}>{row.team_name}</TeamLink>:${row.season ?? "career"}`}>
            <span>{row.rank}</span>
            <div>
              <b><TeamLink season={row.season} managerId={data.manager_history.standings.find((manager) => manager.manager_name === row.manager_name)?.manager_id}>{row.team_name}</TeamLink></b>
              <small>
                {row.manager_name ?? names(row.manager_names)}
                {row.season ? ` · ${row.season}` : ""}
                {row.record ? ` · ${row.record}` : ""}
              </small>
            </div>
            <strong>{value(row)}</strong>
          </li>
        ))}
      </ol>
    </article>
  );
}

export function RecordsLeaderboards({
  boards,
}: {
  boards?: RecordLeaderboards;
}) {
  if (!boards) return null;
  return (
    <section className="leaderboard-section">
      <div className="section-title compact">
        <div>
          <p className="eyebrow">The chase</p>
          <h2>Career leaders</h2>
        </div>
        <p>Current team names represent each manager&apos;s full CGL career.</p>
      </div>
      <div className="leaderboard-grid">
        <LeaderboardCard title="Most wins" rows={boards.career.wins} />
        <LeaderboardCard
          title="Winning percentage"
          rows={boards.career.winning_percentage}
          format="percent"
          note={`${boards.minimum_games_for_percentage}-game minimum`}
        />
        <LeaderboardCard
          title="Championships"
          rows={boards.career.championships}
        />
        <LeaderboardCard
          title="Playoff appearances"
          rows={boards.career.playoff_appearances}
        />
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Volume records</p>
          <h2>Career scoring</h2>
        </div>
        <p>Regular-season points only.</p>
      </div>
      <div className="leaderboard-grid two">
        <LeaderboardCard
          title="Most points scored"
          rows={boards.career.points_for}
          format="points"
        />
        <LeaderboardCard
          title="Most points allowed"
          rows={boards.career.points_against}
          format="points"
        />
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">One-year peaks</p>
          <h2>Single-season leaders</h2>
        </div>
        <p>Completed seasons only; historical team names are preserved.</p>
      </div>
      <div className="leaderboard-grid">
        <LeaderboardCard title="Most wins" rows={boards.single_season.wins} />
        <LeaderboardCard
          title="Best record"
          rows={boards.single_season.winning_percentage}
          format="percent"
        />
        <LeaderboardCard
          title="Most points"
          rows={boards.single_season.points_for}
          format="points"
        />
        <LeaderboardCard
          title="Highest weekly average"
          rows={boards.single_season.average_points}
          format="points"
        />
        <LeaderboardCard
          title="Most points allowed"
          rows={boards.single_season.points_against}
          format="points"
        />
        <LeaderboardCard
          title="Lowest winning percentage"
          rows={boards.single_season.lowest_winning_percentage}
          format="percent"
        />
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Momentum</p>
          <h2>Longest streaks</h2>
        </div>
        <p>Regular-season games across season boundaries.</p>
      </div>
      <div className="leaderboard-grid two">
        <LeaderboardCard
          title="Winning streaks"
          rows={boards.streaks.winning}
          format="streak"
        />
        <LeaderboardCard
          title="Losing streaks"
          rows={boards.streaks.losing}
          format="streak"
        />
      </div>
    </section>
  );
}
