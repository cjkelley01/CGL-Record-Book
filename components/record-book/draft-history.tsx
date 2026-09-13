"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DraftPick } from "@/lib/record-book/history";
import { data, names } from "@/lib/record-book/history";
import { useState } from "react";

export function DraftHistory({
  managerId,
  setManagerId,
}: {
  managerId: string;
  setManagerId: (id: string) => void;
}) {
  const draftSeasons = data.seasons.filter((s) => s.draft_picks.length > 0);
  const [draftYear, setDraftYear] = useState(
    String(draftSeasons.at(-1)?.season ?? 2025),
  );
  const [round, setRound] = useState("1");
  const [managerDraftYear, setManagerDraftYear] = useState(
    String(draftSeasons.at(-1)?.season ?? 2025),
  );
  const season =
    draftSeasons.find((s) => String(s.season) === draftYear) ?? draftSeasons[0];
  const picks = season.draft_picks as unknown as DraftPick[];
  const rounds = [...new Set(picks.map((p) => p.round))].sort((a, b) => a - b);
  const roundPicks = picks.filter((p) => p.round === Number(round));
  const first = picks.find((p) => p.overall_pick === 1);
  const allPicks = draftSeasons.flatMap(
    (s) => s.draft_picks as unknown as DraftPick[],
  );
  const unresolved = allPicks.filter((p) => !p.player_name).length;
  const managers = data.manager_history.standings;
  const playerLabel = (pick?: DraftPick) =>
    pick?.player_name ?? `ESPN player #${pick?.player_id}`;
  const currentTeam = (id: string) => {
    const manager = managers.find((m) => m.manager_id === id);
    return manager
      ? ([...manager.team_names].sort((a, b) => b.season - a.season)[0]
          ?.team_name ?? "—")
      : "—";
  };
  const teamPlayerCounts = [
    ...allPicks
      .reduce((map, p) => {
        for (const id of p.manager_ids) {
          const key = `${id}:${p.player_id}`;
          const row = map.get(key) ?? {
            manager_id: id,
            player_id: p.player_id,
            player_name: p.player_name,
            position: p.position,
            count: 0,
            seasons: new Set<number>(),
          };
          row.count++;
          row.seasons.add(p.season);
          if (!row.player_name && p.player_name)
            row.player_name = p.player_name;
          if (!row.position && p.position) row.position = p.position;
          map.set(key, row);
        }
        return map;
      }, new Map<string, { manager_id: string; player_id: number; player_name?: string | null; position?: string | null; count: number; seasons: Set<number> }>())
      .values(),
  ]
    .filter((p) => p.count > 1)
    .sort(
      (a, b) =>
        b.count - a.count ||
        currentTeam(a.manager_id).localeCompare(currentTeam(b.manager_id)) ||
        String(a.player_name).localeCompare(String(b.player_name)),
    );
  const managerYears = draftSeasons
    .filter((s) =>
      (s.draft_picks as unknown as DraftPick[]).some((p) =>
        p.manager_ids.includes(managerId),
      ),
    )
    .map((s) => s.season)
    .sort((a, b) => b - a);
  const selectedManagerYear = managerYears.includes(Number(managerDraftYear))
    ? Number(managerDraftYear)
    : managerYears[0];
  const selectedManagerPicks = allPicks
    .filter(
      (p) =>
        p.season === selectedManagerYear && p.manager_ids.includes(managerId),
    )
    .sort((a, b) => a.overall_pick - b.overall_pick);
  const changeManager = (id: string) => {
    setManagerId(id);
    const latest = draftSeasons
      .filter((s) =>
        (s.draft_picks as unknown as DraftPick[]).some((p) =>
          p.manager_ids.includes(id),
        ),
      )
      .at(-1);
    if (latest) setManagerDraftYear(String(latest.season));
  };
  return (
    <>
      <section className="draft-head">
        <div>
          <p className="eyebrow">Draft history</p>
          <h2>{season.season} Draft Board</h2>
          <p>
            {picks.length} selections · {season.settings.team_count} teams
          </p>
        </div>
        <div>
          <label>
            Season
            <Select
              value={String(season.season)}
              onValueChange={(value) => {
                setDraftYear(value);
                setRound("1");
              }}
            >
              <SelectTrigger aria-label="Select draft season">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {draftSeasons.map((s) => (
                  <SelectItem key={s.season} value={String(s.season)}>
                    {s.season}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
          <label>
            Round
            <Select value={round} onValueChange={setRound}>
              <SelectTrigger aria-label="Select draft round">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {rounds.map((r) => (
                  <SelectItem key={r} value={String(r)}>
                    Round {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        </div>
      </section>
      {unresolved > 0 && (
        <p className="draft-warning">
          {unresolved} archived selections still need a player name. Rebuild
          from the complete weekly roster archive to resolve them.
        </p>
      )}
      <section className="draft-summary">
        <article>
          <p className="eyebrow">First overall</p>
          <strong>{playerLabel(first)}</strong>
          <span>
            {first?.position && `${first.position} · `}
            {first?.team_name}
            <small>{names(first?.manager_names)}</small>
          </span>
        </article>
        <article>
          <p className="eyebrow">Draft format</p>
          <strong>{rounds.length} rounds</strong>
          <span>{season.settings.team_count}-team snake draft</span>
        </article>
        <article>
          <p className="eyebrow">Keepers</p>
          <strong>{picks.filter((p) => p.keeper).length}</strong>
          <span>Keeper selections</span>
        </article>
      </section>
      <div className="draft-board">
        {roundPicks.map((p) => (
          <article key={p.overall_pick}>
            <span>#{p.overall_pick}</span>
            <div>
              <b>{playerLabel(p)}</b>
              <small>{p.position ?? "Position unavailable"}</small>
            </div>
            <div>
              <b>{p.team_name}</b>
              <small>{names(p.manager_names)}</small>
            </div>
          </article>
        ))}
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Franchise view</p>
          <h2>Team draft history</h2>
        </div>
        <div className="draft-history-filters">
          <Select value={managerId} onValueChange={changeManager}>
            <SelectTrigger aria-label="Select draft team">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {managers
                .filter((m) =>
                  draftSeasons.some((s) =>
                    (s.draft_picks as unknown as DraftPick[]).some((p) =>
                      p.manager_ids.includes(m.manager_id),
                    ),
                  ),
                )
                .map((m) => (
                  <SelectItem key={m.manager_id} value={m.manager_id}>
                    {currentTeam(m.manager_id)} · {m.manager_name}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
          <Select
            value={String(selectedManagerYear)}
            onValueChange={setManagerDraftYear}
          >
            <SelectTrigger aria-label="Select team draft season">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {managerYears.map((year) => (
                <SelectItem key={year} value={String(year)}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="team-draft-card">
        <header>
          <div>
            <p className="eyebrow">{selectedManagerYear} draft</p>
            <h3>
              {selectedManagerPicks[0]?.team_name ?? currentTeam(managerId)}
            </h3>
            <p>
              {managers.find((m) => m.manager_id === managerId)?.manager_name}
            </p>
          </div>
          <strong>
            Slot #
            {selectedManagerPicks.find((p) => p.round === 1)?.round_pick ?? "—"}
          </strong>
        </header>
        <div className="draft-board team-board">
          {selectedManagerPicks.map((p) => (
            <article key={p.overall_pick}>
              <span>R{p.round}</span>
              <div>
                <b>{playerLabel(p)}</b>
                <small>{p.position ?? "Position unavailable"}</small>
              </div>
              <div>
                <b>Pick #{p.overall_pick}</b>
                <small>
                  Round {p.round}, pick {p.round_pick}
                </small>
              </div>
            </article>
          ))}
        </div>
      </div>
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Team tendencies</p>
          <h2>Franchise Favorites</h2>
        </div>
        <p>
          Every player selected by the same franchise in multiple seasons,
          ranked by selections and then team.
        </p>
      </div>
      {teamPlayerCounts.length ? (
        <div className="repeat-picks">
          {teamPlayerCounts.map((player, index) => {
            const manager = managers.find(
              (m) => m.manager_id === player.manager_id,
            );
            const rank =
              teamPlayerCounts.findIndex((row) => row.count === player.count) +
              1;
            return (
              <article
                key={`${player.manager_id}:${player.player_id}`}
                className={
                  index > 0 &&
                  teamPlayerCounts[index - 1].count !== player.count
                    ? "new-tier"
                    : ""
                }
              >
                <span>{rank}</span>
                <div>
                  <b>
                    {player.player_name ?? `ESPN player #${player.player_id}`}
                  </b>
                  <small>
                    {player.position ?? "Position unavailable"} ·{" "}
                    {currentTeam(player.manager_id)} · {manager?.manager_name} ·{" "}
                    {[...player.seasons].sort().join(" & ")}
                  </small>
                </div>
                <strong>{player.count}×</strong>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="empty-series">
          No franchise has drafted the same player in multiple archived drafts.
        </p>
      )}
    </>
  );
}
