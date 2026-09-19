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

export function Standings({ rows }: { rows: Standing[] }) {
  return (
    <div className="table-shell">
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
          {rows.map((m, i) => {
            const currentTeam =
              [...m.team_names].sort((a, b) => b.season - a.season)[0]
                ?.team_name ?? "—";
            return (
              <TableRow key={m.manager_id}>
                <TableCell className="rank">{i + 1}</TableCell>
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
                <TableCell className="titles">
                  {m.championships || "—"}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
