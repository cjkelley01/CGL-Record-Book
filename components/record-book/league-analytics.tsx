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

export function LeagueAnalytics() {
  const analytics = (data as unknown as { analytics?: { all_play?: AnalyticsSeason[] } }).analytics?.all_play ?? [];
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [sort, setSort] = useState<"expected_wins" | "luck_differential" | "all_play_wins">("expected_wins");
  const years = [...analytics].sort((a, b) => b.season - a.season);
  const season = years.find((entry) => entry.season === selectedYear) ?? years[0];
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
            <label>Season
              <select value={season.season} onChange={(event) => setSelectedYear(Number(event.target.value))}>
                {years.map((entry) => <option key={entry.season} value={entry.season}>{entry.season}</option>)}
              </select>
            </label>
            <label>Rank by
              <select value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}>
                <option value="expected_wins">Expected wins</option>
                <option value="luck_differential">Luck differential</option>
                <option value="all_play_wins">All-play wins</option>
              </select>
            </label>
          </div>
          <p className="analytics-note">Calculated from {season.completed_weeks.length} fully completed regular-season weeks. Unfinished or incomplete weeks are excluded.</p>
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
          <p className="analytics-note">*Wins plus half of ties. Expected wins = sum of weekly all-play winning percentages (ties count as half). Luck ± = actual minus expected wins. These are descriptive statistics, not future-win predictions.</p>
        </>
      )}
    </>
  );
}
