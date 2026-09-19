"use client";

import { TeamLink } from "@/components/record-book/team-link";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Standing } from "@/lib/record-book/history";
import { data, fmt, names } from "@/lib/record-book/history";
import { Swords } from "lucide-react";

export function HeadToHead({
  managerAId,
  managerBId,
  setManagerAId,
  setManagerBId,
}: {
  managerAId: string;
  managerBId: string;
  setManagerAId: (id: string) => void;
  setManagerBId: (id: string) => void;
}) {
  const managers = data.manager_history.standings;
  const managerA = managers.find((m) => m.manager_id === managerAId)!;
  const managerB = managers.find((m) => m.manager_id === managerBId)!;
  const currentTeam = (manager: Standing) =>
    [...manager.team_names].sort((a, b) => b.season - a.season)[0]?.team_name ??
    "—";
  const hasManager = (ids: readonly string[], id: string) => ids.includes(id);
  const meetings = data.seasons
    .flatMap((season) =>
      season.matchups
        .filter(
          (m) =>
            m.decided &&
            ["regular_season", "championship_playoffs"].includes(m.stage) &&
            ((hasManager(m.home_manager_ids, managerAId) &&
              hasManager(m.away_manager_ids, managerBId)) ||
              (hasManager(m.home_manager_ids, managerBId) &&
                hasManager(m.away_manager_ids, managerAId))),
        )
        .map((m) => {
          const aHome = hasManager(m.home_manager_ids, managerAId);
          const aScore = (aHome ? m.home_score : m.away_score) ?? 0;
          const bScore = (aHome ? m.away_score : m.home_score) ?? 0;
          return {
            ...m,
            aScore,
            bScore,
            aTeam: aHome ? m.home_team_name : m.away_team_name,
            bTeam: aHome ? m.away_team_name : m.home_team_name,
            aManagers: aHome ? m.home_manager_names : m.away_manager_names,
            bManagers: aHome ? m.away_manager_names : m.home_manager_names,
            aResult: aScore === bScore ? "T" : aScore > bScore ? "W" : "L",
            bResult: aScore === bScore ? "T" : bScore > aScore ? "W" : "L",
          };
        }),
    )
    .sort((a, b) => b.season - a.season || b.matchup_period - a.matchup_period);
  const regular = meetings.filter((m) => m.stage === "regular_season");
  const playoffs = meetings.filter((m) => m.stage === "championship_playoffs");
  const aWins = regular.filter((m) => m.aResult === "W").length;
  const bWins = regular.filter((m) => m.bResult === "W").length;
  const ties = regular.filter((m) => m.aResult === "T").length;
  const aPoints = regular.reduce((sum, m) => sum + m.aScore, 0);
  const bPoints = regular.reduce((sum, m) => sum + m.bScore, 0);
  const decided = regular.filter((m) => m.aResult !== "T");
  const largest = decided.length
    ? [...decided].sort((a, b) => b.margin! - a.margin!)[0]
    : undefined;
  const closest = decided.length
    ? [...decided].sort((a, b) => a.margin! - b.margin!)[0]
    : undefined;
  const selector = (
    value: string,
    other: string,
    onChange: (id: string) => void,
    label: string,
  ) => (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {managers
          .filter((m) => m.manager_id !== other)
          .map((m) => (
            <SelectItem key={m.manager_id} value={m.manager_id}>
              {currentTeam(m)} · {m.manager_name}
            </SelectItem>
          ))}
      </SelectContent>
    </Select>
  );
  const meetingRows = (rows: typeof meetings) => (
    <div className="h2h-games">
      {rows.map((m) => (
        <article key={m.matchup_key}>
          <div>
            <span>
              {m.season} ·{" "}
              {m.stage === "regular_season"
                ? `Week ${m.matchup_period}`
                : `Playoff round ${m.playoff_round}`}
            </span>
            {m.is_multiweek_series && <small>Two-week series</small>}
          </div>
          <section>
            <div>
              <b><TeamLink managerId={managerAId}>{m.aTeam}</TeamLink></b>
              <small>{names(m.aManagers)}</small>
            </div>
            <i className={`result-${m.aResult.toLowerCase()}`}>{m.aResult}</i>
            <strong>{fmt.format(m.aScore)}</strong>
            <em>–</em>
            <strong>{fmt.format(m.bScore)}</strong>
            <i className={`result-${m.bResult.toLowerCase()}`}>{m.bResult}</i>
            <div>
              <b><TeamLink managerId={managerBId}>{m.bTeam}</TeamLink></b>
              <small>{names(m.bManagers)}</small>
            </div>
          </section>
        </article>
      ))}
    </div>
  );
  return (
    <>
      <section className="h2h-picker">
        <div>
          <p className="eyebrow">Head-to-head</p>
          <h2>Rivalry comparison</h2>
        </div>
        <section>
          <label>
            Team one
            {selector(
              managerAId,
              managerBId,
              setManagerAId,
              "Select first manager",
            )}
          </label>
          <Swords />
          <label>
            Team two
            {selector(
              managerBId,
              managerAId,
              setManagerBId,
              "Select second manager",
            )}
          </label>
        </section>
      </section>
      <section className="versus-board">
        <article>
          <h3><TeamLink managerId={managerAId}>{currentTeam(managerA)}</TeamLink></h3>
          <p>{managerA.manager_name}</p>
          <strong>{aWins}</strong>
          <span>Regular-season wins</span>
        </article>
        <div>
          <span>{regular.length} meetings</span>
          <b>
            {aWins}–{bWins}
            {ties ? `–${ties}` : ""}
          </b>
          <small>Official regular-season series</small>
        </div>
        <article>
          <h3><TeamLink managerId={managerBId}>{currentTeam(managerB)}</TeamLink></h3>
          <p>{managerB.manager_name}</p>
          <strong>{bWins}</strong>
          <span>Regular-season wins</span>
        </article>
      </section>
      <section className="h2h-stats">
        <article>
          <span>Total points</span>
          <strong>
            {fmt.format(aPoints)} – {fmt.format(bPoints)}
          </strong>
          <small>Regular season</small>
        </article>
        <article>
          <span>Largest victory</span>
          <strong>
            {largest ? `${fmt.format(largest.margin!)} pts` : "—"}
          </strong>
          <small>
            {largest
              ? `${largest.aResult === "W" ? largest.aTeam : largest.bTeam} · ${largest.season} Week ${largest.matchup_period}`
              : "No decided meetings"}
          </small>
        </article>
        <article>
          <span>Closest game</span>
          <strong>
            {closest ? `${fmt.format(closest.margin!)} pts` : "—"}
          </strong>
          <small>
            {closest
              ? `${closest.season} Week ${closest.matchup_period}`
              : "No decided meetings"}
          </small>
        </article>
      </section>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Regular season</p>
          <h2>Complete matchup history</h2>
        </div>
      </div>
      {regular.length ? (
        meetingRows(regular)
      ) : (
        <p className="empty-series">
          These teams have not met in a completed regular-season game.
        </p>
      )}
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Postseason</p>
          <h2>Playoff meetings</h2>
        </div>
        <p>Tracked separately from the official regular-season series.</p>
      </div>
      {playoffs.length ? (
        meetingRows(playoffs)
      ) : (
        <p className="empty-series">No playoff meetings yet.</p>
      )}
    </>
  );
}
