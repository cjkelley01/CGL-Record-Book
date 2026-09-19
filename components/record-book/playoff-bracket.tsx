"use client";

import { TeamLink } from "@/components/record-book/team-link";

import type { Season } from "@/lib/record-book/history";
import { fmt, names } from "@/lib/record-book/history";

export function PlayoffBracket({ season }: { season: Season }) {
  const rounds = season.matchups.filter(
    (m) =>
      m.stage === "championship_playoffs" &&
      m.home_team_id !== null &&
      m.away_team_id !== null,
  );
  const labels: Record<number, string> = {
    1: "Quarterfinals",
    2: "Semifinals",
    3: "Championship",
  };
  return (
    <section className="bracket-wrap">
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Championship playoffs</p>
          <h2>Playoff bracket</h2>
        </div>
        <p>Final series totals are combined across both championship weeks.</p>
      </div>
      <div className="bracket">
        {[1, 2, 3].map((round) => (
          <div className="bracket-round" key={round}>
            <h3>{labels[round]}</h3>
            {rounds
              .filter((m) => m.playoff_round === round)
              .map((m) => (
                <article key={m.matchup_key}>
                  <div className={m.winner === "HOME" ? "winner" : ""}>
                    <span>
                      <b><TeamLink season={season.season}>{m.home_team_name}</TeamLink></b>
                      <small>{names(m.home_manager_names)}</small>
                    </span>
                    <strong>{fmt.format(m.home_score ?? 0)}</strong>
                  </div>
                  <div className={m.winner === "AWAY" ? "winner" : ""}>
                    <span>
                      <b><TeamLink season={season.season}>{m.away_team_name}</TeamLink></b>
                      <small>{names(m.away_manager_names)}</small>
                    </span>
                    <strong>{fmt.format(m.away_score ?? 0)}</strong>
                  </div>
                  {m.is_multiweek_series && <small>Two-week total</small>}
                </article>
              ))}
          </div>
        ))}
      </div>
    </section>
  );
}
