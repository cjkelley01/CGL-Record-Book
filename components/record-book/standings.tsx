"use client";

import { TeamLink } from "@/components/record-book/team-link";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Standing } from "@/lib/record-book/history";
import { fmt } from "@/lib/record-book/history";

type StandingsProps = {
  rows: Standing[];
  qualificationGames?: number;
};

const gamesPlayed = (standing: Standing) =>
  standing.wins + standing.losses + standing.ties;

export function Standings({ rows, qualificationGames }: StandingsProps) {
  const qualified = qualificationGames
    ? rows
        .filter((standing) => gamesPlayed(standing) >= qualificationGames)
        .sort(
          (a, b) =>
            (b.winning_percentage ?? 0) - (a.winning_percentage ?? 0) ||
            gamesPlayed(b) - gamesPlayed(a) ||
            b.wins - a.wins ||
            b.points_for - a.points_for,
        )
    : rows;
  const provisional = qualificationGames
    ? rows
        .filter((standing) => gamesPlayed(standing) < qualificationGames)
        .sort(
          (a, b) =>
            gamesPlayed(b) - gamesPlayed(a) ||
            (b.winning_percentage ?? 0) - (a.winning_percentage ?? 0) ||
            b.wins - a.wins ||
            b.points_for - a.points_for,
        )
    : [];

  const renderRow = (m: Standing, rank: number | "—") => {
    const currentTeam =
      [...m.team_names].sort((a, b) => b.season - a.season)[0]?.team_name ??
      "—";
    return (
      <TableRow key={m.manager_id}>
        <TableCell className="rank">{rank}</TableCell>
        <TableCell>
          <strong><TeamLink managerId={m.manager_id}>{currentTeam}</TeamLink></strong>
          <small>{m.manager_name}</small>
        </TableCell>
        <TableCell>{m.seasons}</TableCell>
        <TableCell>
          {m.wins}–{m.losses}
        </TableCell>
        <TableCell>
          <strong>
            {((m.winning_percentage ?? 0) * 100).toFixed(1)}%
          </strong>
        </TableCell>
        <TableCell>{fmt.format(m.points_for)}</TableCell>
        <TableCell>{m.playoff_appearances}</TableCell>
        <TableCell>{m.runner_up_finishes + m.championships}</TableCell>
        <TableCell className="titles">{m.championships || "—"}</TableCell>
      </TableRow>
    );
  };

  return (
    <div className={`table-shell${qualificationGames ? " percentage-standings" : ""}`}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>#</TableHead>
            <TableHead>Current team</TableHead>
            <TableHead>Seasons</TableHead>
            <TableHead>Record</TableHead>
            <TableHead>Win %</TableHead>
            <TableHead>Points</TableHead>
            <TableHead>Playoffs</TableHead>
            <TableHead>Finals</TableHead>
            <TableHead>Titles</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {qualified.map((standing) => {
            const firstAtPercentage = qualified.findIndex(
              (row) => row.winning_percentage === standing.winning_percentage,
            );
            return renderRow(standing, firstAtPercentage + 1);
          })}
          {qualificationGames && provisional.length > 0 ? (
            <TableRow className="provisional-divider">
              <TableCell colSpan={9}>
                Provisional — fewer than {qualificationGames} regular-season games
              </TableCell>
            </TableRow>
          ) : null}
          {provisional.map((standing) => renderRow(standing, "—"))}
        </TableBody>
      </Table>
    </div>
  );
}
