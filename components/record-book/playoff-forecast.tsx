"use client";

import { useState } from "react";
import forecast from "@/app/data/playoff_forecast.json";
import { PageHead } from "@/components/record-book/page-head";

type TeamOdds = {
  team_id: number; team_name: string; playoff_probability: number;
  bye_probability: number; championship_probability: number;
  final_probability: number; expected_seed: number; expected_wins: number;
  seed_probabilities: Record<string, number>;
};
type Model = { status: string; reason?: string; simulations?: number; teams?: TeamOdds[] };
const models = forecast.models as unknown as Record<string, Model>;
const labels: Record<string, string> = {
  historical: "Historical", roster_aware: "Roster-Aware", blended: "Blended"
};
const percent = (value: number) => (value * 100).toFixed(1) + "%";

export function PlayoffForecast() {
  const [model, setModel] = useState("historical");
  const [sort, setSort] = useState<"playoff_probability" | "bye_probability" | "championship_probability">("playoff_probability");
  const selected = models[model];
  const rows = [...(selected?.teams ?? [])].sort((a, b) => b[sort] - a[sort] || a.team_name.localeCompare(b.team_name));
  return (
    <>
      <PageHead overline="The road to the CGL championship" title="Playoff Forecast"
        text="Monte Carlo probabilities, refreshed with ESPN standings and projections each Tuesday. Forecasts are estimates, not guarantees." />
      <section className="analytics-note">
        <p>Through Week {forecast.completed_through_week} · {forecast.generated_at ? new Date(forecast.generated_at).toLocaleString() : "Awaiting first refresh"}</p>
        <p>Six playoff teams · Top two seeds earn byes · Championship uses combined Weeks 17 and 18.</p>
        <div className="analytics-controls">
          <label>Forecast model
            <select value={model} onChange={e => setModel(e.target.value)}>
              {Object.keys(labels).map(key => <option key={key} value={key}>{labels[key]}</option>)}
            </select>
          </label>
          <label>Rank by
            <select value={sort} onChange={e => setSort(e.target.value as typeof sort)}>
              <option value="playoff_probability">Playoff chance</option>
              <option value="bye_probability">Bye chance</option>
              <option value="championship_probability">Championship chance</option>
            </select>
          </label>
        </div>
        {selected?.status !== "available" ? (
          <p>Model unavailable: {selected?.reason ?? "Forecast data is not ready."}</p>
        ) : (
          <>
            <p>{selected.simulations?.toLocaleString()} simulations · Probabilities update with each successful refresh.</p>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                <thead><tr><th>Team</th><th>Playoffs</th><th>Bye</th><th>Final</th><th>Champion</th><th>Expected seed</th></tr></thead>
                <tbody>{rows.map(team => (
                  <tr key={team.team_id} style={{ borderTop: "1px solid currentColor" }}>
                    <td>{team.team_name}</td>
                    <td>{percent(team.playoff_probability)}</td>
                    <td>{percent(team.bye_probability)}</td>
                    <td>{percent(team.final_probability)}</td>
                    <td>{percent(team.championship_probability)}</td>
                    <td>{team.expected_seed.toFixed(2)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </>
        )}
      </section>
      <p className="legend">Historical uses completed 2026 scoring averages. Roster-Aware optimizes ESPN-projected regular-season lineups, filling missing starters with the top-three average of current-week free agents. Playoff weeks 15–18 use a modeled carry-forward of the final projected regular-season lineup, not ESPN playoff-week projections. Blended weights historical 40% and roster projections 60%. Models requiring missing projections remain unavailable.</p>
    </>
  );
}
