"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { EnrichedSeason, Season } from "@/lib/record-book/history";
import { fmt, names } from "@/lib/record-book/history";

export function CurrentSeason({ season }: { season?: Season }) {
  if (!season)
    return (
      <section className="empty-live">
        <p className="eyebrow gold">2026 Live</p>
        <h2>Current-season data is ready to be pulled.</h2>
        <p>
          Run the 2026 ESPN discovery and rebuild the history to activate this
          page.
        </p>
      </section>
    );
  const standings = [...season.teams].sort(
    (a, b) => (a.playoff_seed ?? 99) - (b.playoff_seed ?? 99),
  );
  const complete = season.matchups.filter(
    (m) =>
      m.stage === "regular_season" &&
      m.decided &&
      m.home_team_id !== null &&
      m.away_team_id !== null,
  );
  const completedIds = new Set(complete.map((m) => m.matchup_id));
  const scores = season.weekly_scores.filter((s) =>
    completedIds.has(s.matchup_id),
  );
  const weeklyHigh = scores.length
    ? [...scores].sort((a, b) => b.points - a.points)[0]
    : undefined;
  const latestGames = complete.filter(
    (m) => m.matchup_period === season.through_week,
  );
  const pointsLeader = [...season.teams].sort(
    (a, b) => b.regular_season.points_for - a.regular_season.points_for,
  )[0];
  const liveStories =
    (season as EnrichedSeason).storylines?.filter(
      (story) =>
        story.label === "Expansion" || story.label === "New identities",
    ) ?? [];
  return (
    <>
      <section className="live-banner">
        <div>
          <p className="eyebrow">Current season</p>
          <h2>{season.season} Live</h2>
          <p>
            {season.through_week
              ? `Standings and official results through Week ${season.through_week}.`
              : "Standings are live; Week 1 results are not final yet."}
          </p>
        </div>
        <span className="live-pill">
          <i />
          In progress
        </span>
      </section>
      <section className="live-cards">
        <article>
          <p className="eyebrow">Current leader</p>
          <strong>{standings[0]?.team_name}</strong>
          <span>
            {names(standings[0]?.manager_names)} ·{" "}
            {standings[0]?.regular_season.wins}–
            {standings[0]?.regular_season.losses}
          </span>
        </article>
        <article>
          <p className="eyebrow">Points leader</p>
          <strong>{pointsLeader?.team_name}</strong>
          <span>
            {names(pointsLeader?.manager_names)} ·{" "}
            {fmt.format(pointsLeader?.regular_season.points_for ?? 0)} points
          </span>
        </article>
        <article>
          <p className="eyebrow">Season high</p>
          <strong>{weeklyHigh ? fmt.format(weeklyHigh.points) : "—"}</strong>
          <span>
            {weeklyHigh
              ? `${weeklyHigh.team_name} · ${names(weeklyHigh.manager_names)} · Week ${weeklyHigh.scoring_period}`
              : "No completed games"}
          </span>
        </article>
      </section>
      {liveStories.length ? (
        <section className="live-notes">
          {liveStories.map((story) => (
            <article key={story.label}>
              <p className="eyebrow">{story.label}</p>
              <h3>{story.title}</h3>
              <p>{story.text}</p>
            </article>
          ))}
        </section>
      ) : null}
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Playoff picture</p>
          <h2>Current standings</h2>
        </div>
        <p>Seeds reflect ESPN&apos;s current league order.</p>
      </div>
      <div className="table-shell">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Seed</TableHead>
              <TableHead>Team</TableHead>
              <TableHead>Record</TableHead>
              <TableHead>PF</TableHead>
              <TableHead>PA</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {standings.map((t) => (
              <TableRow key={t.team_season_id}>
                <TableCell className="rank">#{t.playoff_seed}</TableCell>
                <TableCell>
                  <strong>{t.team_name}</strong>
                  <small>{names(t.manager_names)}</small>
                </TableCell>
                <TableCell>
                  {t.regular_season.wins}–{t.regular_season.losses}
                </TableCell>
                <TableCell>{fmt.format(t.regular_season.points_for)}</TableCell>
                <TableCell>
                  {fmt.format(t.regular_season.points_against)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {season.through_week > 0 && (
        <>
          <div className="section-title compact">
            <div>
              <p className="eyebrow">Latest completed week</p>
              <h2>Week {season.through_week} results</h2>
            </div>
          </div>
          <section className="score-grid">
            {latestGames.map((g) => (
              <article key={g.matchup_key}>
                <div
                  className={
                    (g.winner === "HOME" ? "winner " : "") + "score-side"
                  }
                >
                  <span>
                    <b>{g.home_team_name}</b>
                    <small>{names(g.home_manager_names)}</small>
                  </span>
                  <strong>{fmt.format(g.home_score ?? 0)}</strong>
                </div>
                <div
                  className={
                    (g.winner === "AWAY" ? "winner " : "") + "score-side"
                  }
                >
                  <span>
                    <b>{g.away_team_name}</b>
                    <small>{names(g.away_manager_names)}</small>
                  </span>
                  <strong>{fmt.format(g.away_score ?? 0)}</strong>
                </div>
              </article>
            ))}
          </section>
        </>
      )}
    </>
  );
}
