"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { data, fmt } from "@/lib/record-book/history";

export function ManagerProfile({
  managerId,
  setManagerId,
}: {
  managerId: string;
  setManagerId: (id: string) => void;
}) {
  const managers = data.manager_history.standings;
  const manager =
    managers.find((m) => m.manager_id === managerId) ?? managers[0];
  const currentTeam =
    [...manager.team_names].sort((a, b) => b.season - a.season)[0]?.team_name ??
    "—";
  const seasonRows = data.seasons.flatMap((season) =>
    season.teams
      .filter((team) => team.manager_ids.includes(manager.manager_id))
      .map((team) => ({ season, team })),
  );
  const completedIds = new Set(
    data.seasons.flatMap((season) =>
      season.matchups
        .filter((m) => m.stage === "regular_season" && m.decided)
        .map((m) => `${season.season}:${m.matchup_id}`),
    ),
  );
  const scores = data.seasons.flatMap((season) =>
    season.weekly_scores.filter(
      (score) =>
        score.manager_ids.includes(manager.manager_id) &&
        score.stage === "regular_season" &&
        completedIds.has(`${season.season}:${score.matchup_id}`),
    ),
  );
  const high = scores.length
    ? [...scores].sort((a, b) => b.points - a.points)[0]
    : undefined;
  const low = scores.length
    ? [...scores].sort((a, b) => a.points - b.points)[0]
    : undefined;
  const streak = data.streaks.find((s) => s.manager_id === manager.manager_id);
  const opponentRows = data.head_to_head
    .filter(
      (h) =>
        h.manager_1_id === manager.manager_id ||
        h.manager_2_id === manager.manager_id,
    )
    .map((h) => {
      const isFirst = h.manager_1_id === manager.manager_id;
      const opponentId = isFirst ? h.manager_2_id : h.manager_1_id;
      const opponent = managers.find((m) => m.manager_id === opponentId);
      const opponentTeam = opponent
        ? [...opponent.team_names].sort((a, b) => b.season - a.season)[0]
            ?.team_name
        : "—";
      return {
        opponentId,
        opponentName: isFirst ? h.manager_2_name : h.manager_1_name,
        opponentTeam,
        wins: isFirst ? h.manager_1_wins : h.manager_2_wins,
        losses: isFirst ? h.manager_2_wins : h.manager_1_wins,
        ties: h.ties,
        games: h.games,
      };
    })
    .sort(
      (a, b) =>
        b.games - a.games ||
        b.wins - a.wins ||
        a.opponentName.localeCompare(b.opponentName),
    );
  const finish = (rank: number | null, complete: boolean) =>
    !complete
      ? "In progress"
      : rank === 1
        ? "Champion"
        : rank === 2
          ? "Runner-up"
          : rank
            ? `#${rank}`
            : "—";
  return (
    <>
      <section className="manager-hero">
        <div>
          <p className="eyebrow">Manager profile</p>
          <h2>{currentTeam}</h2>
          <p>{manager.manager_name}</p>
        </div>
        <Select value={manager.manager_id} onValueChange={setManagerId}>
          <SelectTrigger aria-label="Select manager">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {managers.map((m) => {
              const team = [...m.team_names].sort(
                (a, b) => b.season - a.season,
              )[0]?.team_name;
              return (
                <SelectItem key={m.manager_id} value={m.manager_id}>
                  {team} · {m.manager_name}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </section>
      <section className="profile-stats">
        <article>
          <span>Career record</span>
          <strong>
            {manager.wins}–{manager.losses}
            {manager.ties ? `–${manager.ties}` : ""}
          </strong>
          <small>
            {((manager.winning_percentage ?? 0) * 100).toFixed(1)}% winning
            percentage
          </small>
        </article>
        <article>
          <span>Postseason</span>
          <strong>{manager.championships}</strong>
          <small>
            {manager.championships === 1 ? "championship" : "championships"} ·{" "}
            {manager.playoff_appearances} playoff appearances
          </small>
        </article>
        <article>
          <span>Career points</span>
          <strong>{fmt.format(manager.points_for)}</strong>
          <small>{fmt.format(manager.points_against)} points allowed</small>
        </article>
        <article>
          <span>Best week</span>
          <strong>{high ? fmt.format(high.points) : "—"}</strong>
          <small>
            {high
              ? `${high.team_name} · ${high.season} Week ${high.scoring_period}`
              : "No completed games"}
          </small>
        </article>
        <article>
          <span>Lowest week</span>
          <strong>{low ? fmt.format(low.points) : "—"}</strong>
          <small>
            {low
              ? `${low.team_name} · ${low.season} Week ${low.scoring_period}`
              : "No completed games"}
          </small>
        </article>
        <article>
          <span>Streaks</span>
          <strong>
            {streak?.longest_winning_streak ?? 0}W /{" "}
            {streak?.longest_losing_streak ?? 0}L
          </strong>
          <small>Longest winning / losing streak</small>
        </article>
      </section>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Year by year</p>
          <h2>Season history</h2>
        </div>
      </div>
      <div className="table-shell">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Season</TableHead>
              <TableHead>Team</TableHead>
              <TableHead>Record</TableHead>
              <TableHead>PF</TableHead>
              <TableHead>Regular finish</TableHead>
              <TableHead>Final finish</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {seasonRows
              .sort((a, b) => b.season.season - a.season.season)
              .map(({ season, team }) => (
                <TableRow key={team.team_season_id}>
                  <TableCell className="rank">{season.season}</TableCell>
                  <TableCell>
                    <strong>{team.team_name}</strong>
                  </TableCell>
                  <TableCell>
                    {team.regular_season.wins}–{team.regular_season.losses}
                  </TableCell>
                  <TableCell>
                    {fmt.format(team.regular_season.points_for)}
                  </TableCell>
                  <TableCell>#{team.playoff_seed}</TableCell>
                  <TableCell>
                    {finish(team.final_rank, season.is_complete)}
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Regular season</p>
          <h2>Record by opponent</h2>
        </div>
        <p>
          Postseason meetings are excluded from career head-to-head records.
        </p>
      </div>
      <div className="table-shell">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Opponent team</TableHead>
              <TableHead>Manager</TableHead>
              <TableHead>Series</TableHead>
              <TableHead>Record</TableHead>
              <TableHead>Games</TableHead>
              <TableHead>Win %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {opponentRows.map((row) => {
              const series =
                row.wins === row.losses
                  ? "T"
                  : row.wins > row.losses
                    ? "W"
                    : "L";
              return (
                <TableRow key={row.opponentId}>
                  <TableCell>
                    <strong>{row.opponentTeam}</strong>
                  </TableCell>
                  <TableCell>{row.opponentName}</TableCell>
                  <TableCell>
                    <i className={`result-${series.toLowerCase()}`}>{series}</i>
                  </TableCell>
                  <TableCell>
                    {row.wins}–{row.losses}
                    {row.ties ? `–${row.ties}` : ""}
                  </TableCell>
                  <TableCell>{row.games}</TableCell>
                  <TableCell>
                    <strong>
                      {(
                        ((row.wins + 0.5 * row.ties) / row.games) *
                        100
                      ).toFixed(1)}
                      %
                    </strong>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </>
  );
}
