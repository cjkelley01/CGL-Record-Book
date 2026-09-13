"use client";

import { PlayoffBracket } from "@/components/record-book/playoff-bracket";
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
import type { EnrichedSeason, Season } from "@/lib/record-book/history";
import { fmt, names } from "@/lib/record-book/history";
import { Trophy } from "lucide-react";
import { useState } from "react";

export function SeasonArchive({ season }: { season: Season }) {
  const archive = season as EnrichedSeason;
  const [week, setWeek] = useState("1");
  const teams = [...season.teams].sort(
    (a, b) => (a.playoff_seed ?? 99) - (b.playoff_seed ?? 99),
  );
  const champ = season.teams.find((t) => t.final_rank === 1);
  const runner = season.teams.find((t) => t.final_rank === 2);
  const periods = [
    ...new Set(
      season.weekly_scores
        .filter((s) => s.opponent_team_id !== null)
        .map((s) => s.scoring_period),
    ),
  ].sort((a, b) => a - b);
  const selected = Number(week);
  const scoreRows = season.weekly_scores.filter(
    (s) => s.scoring_period === selected && s.opponent_team_id !== null,
  );
  const scoreMap = new Map(scoreRows.map((s) => [s.team_id, s]));
  const games = scoreRows
    .filter((s) => s.team_id < (s.opponent_team_id ?? 0))
    .map((s) => ({ a: s, b: scoreMap.get(s.opponent_team_id!) }))
    .filter((g) => g.b);
  const championship = season.matchups.find(
    (m) =>
      m.stage === "championship_playoffs" && m.is_multiweek_series && m.decided,
  );
  return (
    <>
      <div className="season-grid">
        <aside className="season-card">
          <span className="watermark">{season.season}</span>
          <Trophy />
          <p className="eyebrow">League champion</p>
          <h3>{champ?.team_name}</h3>
          <p>{names(champ?.manager_names)}</p>
          <dl>
            <div>
              <dt>Regular-season record</dt>
              <dd>
                {champ?.regular_season.wins}–{champ?.regular_season.losses}
              </dd>
            </div>
            <div>
              <dt>Regular-season seed</dt>
              <dd>#{champ?.playoff_seed}</dd>
            </div>
            <div>
              <dt>Runner-up</dt>
              <dd>
                <b>{runner?.team_name}</b>
                <small>{names(runner?.manager_names)}</small>
              </dd>
            </div>
          </dl>
        </aside>
        <div>
          <p className="eyebrow">Regular-season standings</p>
          <div className="season-standings-cards">
            {teams.map((t) => (
              <article key={t.team_season_id}>
                <header>
                  <span className="rank">#{t.playoff_seed}</span>
                  <div>
                    <h3>{t.team_name}</h3>
                    <p>{names(t.manager_names)}</p>
                  </div>
                </header>
                <dl>
                  <div><dt>Record</dt><dd>{t.regular_season.wins}–{t.regular_season.losses}</dd></div>
                  <div><dt>Final finish</dt><dd>{t.final_rank === 1 ? "Champion" : t.final_rank === 2 ? "Runner-up" : `#${t.final_rank}`}</dd></div>
                  <div><dt>Points for</dt><dd>{fmt.format(t.regular_season.points_for)}</dd></div>
                  <div><dt>Points against</dt><dd>{fmt.format(t.regular_season.points_against)}</dd></div>
                </dl>
              </article>
            ))}
          </div>
          <div className="table-shell no-top season-standings-table">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Seed</TableHead>
                  <TableHead>Team</TableHead>
                  <TableHead>Record</TableHead>
                  <TableHead>PF</TableHead>
                  <TableHead>PA</TableHead>
                  <TableHead>Final finish</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teams.map((t) => (
                  <TableRow key={t.team_season_id}>
                    <TableCell className="rank">#{t.playoff_seed}</TableCell>
                    <TableCell>
                      <strong>{t.team_name}</strong>
                      <small>{names(t.manager_names)}</small>
                    </TableCell>
                    <TableCell>
                      {t.regular_season.wins}–{t.regular_season.losses}
                    </TableCell>
                    <TableCell>
                      {fmt.format(t.regular_season.points_for)}
                    </TableCell>
                    <TableCell>
                      {fmt.format(t.regular_season.points_against)}
                    </TableCell>
                    <TableCell>
                      {t.final_rank === 1
                        ? "Champion"
                        : t.final_rank === 2
                          ? "Runner-up"
                          : `#${t.final_rank}`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
      {championship && (
        <section className="championship-recap">
          <div>
            <p className="eyebrow">Championship recap</p>
            <h2>
              {championship.home_team_name} vs. {championship.away_team_name}
            </h2>
            <p>Two-week championship series · {season.season}</p>
          </div>
          <div
            className={
              (championship.winner === "HOME" ? "winner " : "") + "score-side"
            }
          >
            <span>
              <b>{championship.home_team_name}</b>
              <small>{names(championship.home_manager_names)}</small>
            </span>
            <strong>{fmt.format(championship.home_score ?? 0)}</strong>
          </div>
          <div
            className={
              (championship.winner === "AWAY" ? "winner " : "") + "score-side"
            }
          >
            <span>
              <b>{championship.away_team_name}</b>
              <small>{names(championship.away_manager_names)}</small>
            </span>
            <strong>{fmt.format(championship.away_score ?? 0)}</strong>
          </div>
        </section>
      )}
      <div className="section-title compact">
        <div>
          <p className="eyebrow">Season honors</p>
          <h2>{season.season} awards</h2>
        </div>
        <p>Championship results plus regular-season achievements.</p>
      </div>
      <section className="award-board">
        {archive.awards?.map((award) => (
          <article
            key={award.key}
            className={award.key === "champion" ? "major-award" : ""}
          >
            <p className="eyebrow">{award.title}</p>
            <strong>{award.value}</strong>
            <h3>{award.team_name}</h3>
            <span>{names(award.manager_names)}</span>
            <small>{award.detail}</small>
          </article>
        ))}
      </section>
      {archive.storylines?.length ? (
        <>
          <div className="section-title compact">
            <div>
              <p className="eyebrow">The year in review</p>
              <h2>{season.season} storylines</h2>
            </div>
            <p>Generated only from official league results and changes.</p>
          </div>
          <section className="story-grid">
            {archive.storylines.map((story, index) => (
              <article key={`${story.label}:${index}`}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <p className="eyebrow">{story.label}</p>
                  <h3>{story.title}</h3>
                  <p>{story.text}</p>
                </div>
              </article>
            ))}
          </section>
        </>
      ) : null}
      <PlayoffBracket season={season} />
      <section className="weekly-results">
        <div className="section-title compact">
          <div>
            <p className="eyebrow">Full scoreboard</p>
            <h2>Weekly results</h2>
          </div>
          <Select value={week} onValueChange={setWeek}>
            <SelectTrigger aria-label="Select scoring week">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {periods.map((p) => (
                <SelectItem key={p} value={String(p)}>
                  Week {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="score-grid">
          {games.map(({ a, b }) => (
            <article key={`${selected}:${a.matchup_id}:${a.team_id}`}>
              <div
                className={
                  (a.points > (b?.points ?? 0) ? "winner " : "") + "score-side"
                }
              >
                <span>
                  <b>{a.team_name}</b>
                  <small>{names(a.manager_names)}</small>
                </span>
                <strong>{fmt.format(a.points)}</strong>
              </div>
              <div
                className={
                  ((b?.points ?? 0) > a.points ? "winner " : "") + "score-side"
                }
              >
                <span>
                  <b>{b?.team_name}</b>
                  <small>{names(b?.manager_names)}</small>
                </span>
                <strong>{fmt.format(b?.points ?? 0)}</strong>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
