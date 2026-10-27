"use client";

import { useState } from "react";
import { data, fmt } from "@/lib/record-book/history";
import { PageHead } from "@/components/record-book/page-head";

type AnalyticsRow = {
  team_id: number;
  team_name: string;
  weeks: number;
  all_play_wins: number;
  all_play_losses: number;
  all_play_ties: number;
  expected_wins: number;
  actual_win_equivalents: number;
  luck_differential: number;
};
type AnalyticsSeason = {
  season: number;
  completed_weeks: number[];
  teams: AnalyticsRow[];
};

type ScheduleRow = {
  team_id: number; team_name: string; weeks: number;
  points_against: number; points_against_per_week: number;
  average_opponent_weekly_rank: number | null;
  actual_wins: number; average_schedule_wins: number;
  schedule_luck: number;
  schedule_swap: { schedule_team_id: number; schedule_team_name: string; wins: number }[];
};
type ScheduleSeason = { season: number; completed_weeks: number[]; teams: ScheduleRow[] };

export function LeagueAnalytics() {
  const analytics = (data as unknown as { analytics?: { all_play?: AnalyticsSeason[] } }).analytics?.all_play ?? [];
  const schedules = (data as unknown as { analytics?: { schedule_luck?: ScheduleSeason[] } }).analytics?.schedule_luck ?? [];
  const [view, setView] = useState<"all_play" | "schedule">("all_play");
  const [scheduleSort, setScheduleSort] = useState<"points_against_per_week" | "schedule_luck" | "average_schedule_wins">("points_against_per_week");
  const [expandedTeam, setExpandedTeam] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [sort, setSort] = useState<"expected_wins" | "luck_differential" | "all_play_wins">("expected_wins");
  const years = [...analytics].sort((a, b) => b.season - a.season);
  const season = years.find((entry) => entry.season === selectedYear) ?? years[0];
  const scheduleSeason = schedules.find((entry) => entry.season === season?.season);
  const scheduleRows = [...(scheduleSeason?.teams ?? [])].sort((a, b) =>
    b[scheduleSort] - a[scheduleSort] || a.team_name.localeCompare(b.team_name));
  const rows = [...(season?.teams ?? [])].sort((a, b) => b[sort] - a[sort] || a.team_name.localeCompare(b.team_name));
  return (
    <>
      <PageHead overline="Beyond the standings" title="League Analytics"
        text="Every team's scoring performance against the whole league, not just its scheduled opponent." />
      {!season ? (
        <section className="analytics-note">
          <h3>Analytics data not generated yet</h3>
          <p>Run the updated Python history builder to populate the all-play statistics. Existing official standings remain unchanged.</p>
        </section>
      ) : (
        <>
          <div className="analytics-controls">
            <label>Analysis
              <select value={view} onChange={(event) => setView(event.target.value as typeof view)}>
                <option value="all_play">All-play &amp; expected wins</option>
                <option value="schedule">Schedule difficulty &amp; luck</option>
              </select>
            </label>
            <label>Season
              <select value={season.season} onChange={(event) => setSelectedYear(Number(event.target.value))}>
                {years.map((entry) => <option key={entry.season} value={entry.season}>{entry.season}</option>)}
              </select>
            </label>
            {view === "all_play" ? (
              <label>Rank by
                <select value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}>
                  <option value="expected_wins">Expected wins</option>
                  <option value="luck_differential">Luck differential</option>
                  <option value="all_play_wins">All-play wins</option>
                </select>
              </label>
            ) : (
              <label>Rank by
                <select value={scheduleSort} onChange={(event) => setScheduleSort(event.target.value as typeof scheduleSort)}>
                  <option value="points_against_per_week">Toughest opponent scoring</option>
                  <option value="schedule_luck">Most favorable schedule</option>
                  <option value="average_schedule_wins">Highest average schedule wins</option>
                </select>
              </label>
            )}
          </div>
          <p className="analytics-note">Calculated from {season.completed_weeks.length} fully completed regular-season weeks. Unfinished or incomplete weeks are excluded.</p>
          {view === "all_play" ? (
          <div className="table-shell analytics-table-wrap">
            <table className="analytics-table">
              <thead><tr><th>Rank</th><th>Team</th><th>All-play W–L–T</th><th>Expected wins</th><th>Actual wins*</th><th>Luck ±</th></tr></thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.team_id}>
                    <td>{index + 1}</td>
                    <td><strong>{row.team_name}</strong></td>
                    <td>{row.all_play_wins}–{row.all_play_losses}–{row.all_play_ties}</td>
                    <td>{fmt.format(row.expected_wins)}</td>
                    <td>{fmt.format(row.actual_win_equivalents)}</td>
                    <td className={row.luck_differential > 0 ? "analytics-positive" : row.luck_differential < 0 ? "analytics-negative" : ""}>
                      {row.luck_differential > 0 ? "+" : ""}{fmt.format(row.luck_differential)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          ) : scheduleSeason ? (
            <>
              <div className="table-shell analytics-table-wrap">
                <table className="analytics-table">
                  <thead><tr><th>Rank</th><th>Team</th><th>Opp. points / week</th><th>Opp. avg rank*</th><th>Actual wins</th><th>Avg. swap wins</th><th>Schedule luck ±</th><th>Compare</th></tr></thead>
                  <tbody>
                    {scheduleRows.map((row, index) => (
                      <tr key={row.team_id}>
                        <td>{index + 1}</td><td><strong>{row.team_name}</strong></td>
                        <td>{fmt.format(row.points_against_per_week)}</td>
                        <td>{row.average_opponent_weekly_rank === null ? "—" : fmt.format(row.average_opponent_weekly_rank)}</td>
                        <td>{fmt.format(row.actual_wins)}</td>
                        <td>{fmt.format(row.average_schedule_wins)}</td>
                        <td className={row.schedule_luck > 0 ? "analytics-positive" : row.schedule_luck < 0 ? "analytics-negative" : ""}>
                          {row.schedule_luck > 0 ? "+" : ""}{fmt.format(row.schedule_luck)}
                        </td>
                        <td><button type="button" onClick={() => setExpandedTeam(expandedTeam === row.team_id ? null : row.team_id)}>
                          {expandedTeam === row.team_id ? "Hide" : "Schedules"}
                        </button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {scheduleRows.filter(row => row.team_id === expandedTeam).map(row => (
                <section className="analytics-note" key={row.team_id}>
                  <h3>{row.team_name}: wins with every team's schedule</h3>
                  <div className="table-shell analytics-table-wrap">
                    <table className="analytics-table">
                      <thead><tr><th>Schedule owner</th><th>Wins with that schedule</th></tr></thead>
                      <tbody>{row.schedule_swap.map(s => (
                        <tr key={s.schedule_team_id}><td>{s.schedule_team_name}</td><td>{fmt.format(s.wins)}</td></tr>
                      ))}</tbody>
                    </table>
                  </div>
                </section>
              ))}
              <p className="analytics-note">*Opponent rank within that week's league scores (1 = highest scoring). Higher opponent points means a tougher schedule. Schedule luck = actual wins minus average wins if the same weekly scores were played against each other team's schedule. Positive means a more favorable schedule. Ties count as half. When a swap would face a team against itself, the original schedule owner takes the opposing slot. Only complete weeks count.</p>
            </>
          ) : <p className="analytics-note">Schedule data has not been generated yet. Run the ESPN refresh workflow.</p>}
          {view === "all_play" && <p className="analytics-note">*Wins plus half of ties. Expected wins = sum of weekly all-play winning percentages (ties count as half). Luck ± = actual minus expected wins. These are descriptive statistics, not future-win predictions.</p>}
        </>
      )}
    </>
  );
}
