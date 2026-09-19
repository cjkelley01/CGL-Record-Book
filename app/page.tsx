"use client";

import { CurrentSeason } from "@/components/record-book/current-season";
import { DraftHistory } from "@/components/record-book/draft-history";
import { HeadToHead } from "@/components/record-book/head-to-head";
import { ManagerProfile } from "@/components/record-book/manager-profile";
import { PageHead } from "@/components/record-book/page-head";
import { RecordCard } from "@/components/record-book/record-card";
import { RecordGroup } from "@/components/record-book/record-group";
import { RecordsLeaderboards } from "@/components/record-book/records-leaderboards";
import { SeasonArchive } from "@/components/record-book/season-archive";
import { Standings } from "@/components/record-book/standings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RecordLeaderboards } from "@/lib/record-book/history";
import { data, fmt, names } from "@/lib/record-book/history";
import { Crown, History, Shield, Swords, Trophy } from "lucide-react";
import { updateView, useViewValue } from "@/lib/record-book/navigation";
import { TeamLink } from "@/components/record-book/team-link";

const sections = [
  ["overview", "Overview"],
  ["current", "2026 Live"],
  ["champions", "Champions"],
  ["standings", "Standings"],
  ["managers", "Managers"],
  ["head-to-head", "Head-to-Head"],
  ["drafts", "Drafts"],
  ["records", "Records"],
  ["seasons", "Seasons"],
] as const;

export default function Home() {
  const [section] = useViewValue("section", "overview", sections.map(([value]) => value));
  const [yearValue, setYear] = useViewValue("season", String([...data.seasons].reverse().find((s) => s.is_complete)!.season), data.seasons.filter((s) => s.is_complete).map((s) => String(s.season)));
  const year = Number(yearValue);
  const managerIds = data.manager_history.standings.map((m) => m.manager_id);
  const season = data.seasons.find((s) => s.season === year) ?? data.seasons[0];
  const regular = data.records.regular_season,
    playoffs = data.records.championship_playoffs,
    series = data.records.multiweek_playoff_series;
  const leaderboards = (
    data.records as unknown as { leaderboards?: RecordLeaderboards }
  ).leaderboards;
  const latestSeason = [...data.seasons].reverse().find((s) => s.is_complete)!;
  const latestChampion = latestSeason.teams.find((t) => t.final_rank === 1)!;
  const [managerId, setManagerId] = useViewValue("manager", latestChampion.manager_ids[0], managerIds);
  const previousChampion = data.records.champions
    .slice()
    .sort((a, b) => b.season - a.season)
    .find((c) => !c.manager_ids.includes(latestChampion.manager_ids[0]));
  const [managerAId, setManagerAId] = useViewValue("team1", latestChampion.manager_ids[0], managerIds);
  const [managerBId, setManagerBId] = useViewValue("team2",
    (previousChampion?.manager_ids[0] !== managerAId ? previousChampion?.manager_ids[0] : undefined) ??
      data.manager_history.standings.find(
        (m) => m.manager_id !== managerAId,
      )!.manager_id,
    managerIds.filter((id) => id !== managerAId),
  );
  const currentSeason = data.seasons.find((s) => !s.is_complete);
  const setSection = (next: string) => updateView({
    section: next,
    season: yearValue,
    manager: managerId,
    team1: managerAId,
    team2: managerBId,
  });
  return (
    <main>
      <header className="site-header">
        <div className="crest">
          <b>CGL</b>
          <small>EST. 2024</small>
        </div>
        <div>
          <p>Charley&apos;s Gonna Lose</p>
          <h1>Official Record Book</h1>
        </div>
        <div className="seal">
          <Shield />
          <span>
            League
            <br />
            History
          </span>
        </div>
      </header>
      <Tabs value={section} onValueChange={setSection} className="tabs">
        <nav aria-label="Record book sections">
          <label className="mobile-navigation">
            Browse
            <select value={section} onChange={(event) => setSection(event.target.value)}>
              {sections.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <TabsList variant="line">
            {sections.map(([value, label]) => (
              <TabsTrigger key={value} value={value}>{label}</TabsTrigger>
            ))}
          </TabsList>
        </nav>
        <TabsContent value="overview" className="page">
          <section className="lede">
            <div>
              <p className="eyebrow gold">The books are open</p>
              <h2>
                {data.records.counts.seasons} seasons.
                <br />
                <em>One official history.</em>
              </h2>
              <p className="intro">
                Every matchup, title and heartbreak since CGL&apos;s official
                record era began in 2024.
              </p>
              <p className="legend">
                <History /> Pre-2024 championships live on as league legend.
              </p>
            </div>
            <article className="reigning">
              <Crown />
              <p className="eyebrow">
                Reigning champion · {latestSeason.season}
              </p>
              <h3><TeamLink>{latestChampion.team_name}</TeamLink></h3>
              <p>{names(latestChampion.manager_names)}</p>
              <div>
                <span>
                  <b>
                    {latestChampion.regular_season.wins}–
                    {latestChampion.regular_season.losses}
                  </b>
                  Regular season
                </span>
                <span>
                  <b>#{latestChampion.playoff_seed}</b>Playoff seed
                </span>
              </div>
            </article>
          </section>
          <section className="totals">
            <div>
              <b>{data.records.counts.seasons}</b>
              <span>Seasons</span>
            </div>
            <div>
              <b>{data.records.counts.regular_season_matchups}</b>
              <span>Regular-season games</span>
            </div>
            <div>
              <b>{data.managers.length}</b>
              <span>Managers</span>
            </div>
            <div>
              <b>{data.records.champions.length}</b>
              <span>Champions</span>
            </div>
          </section>
          <div className="section-title">
            <div>
              <p className="eyebrow">All-time pace setters</p>
              <h2>Winning percentage</h2>
            </div>
            <p>Minimum 14 completed regular-season games to qualify.</p>
          </div>
          <Standings
            rows={data.manager_history.standings}
            qualificationGames={14}
          />
          <section className="record-grid spaced">
            <RecordCard
              label="Single-week high"
              title={regular.highest_weekly_score.team_name}
              record={regular.highest_weekly_score}
              value={fmt.format(regular.highest_weekly_score.points)}
            />
            <RecordCard
              label="Closest finish"
              title={`${regular.closest_game.home_team_name} / ${regular.closest_game.away_team_name}`}
              record={regular.closest_game}
              value={`${fmt.format(regular.closest_game.margin)} pts`}
            />
            <RecordCard
              label="Largest rout"
              title={`${regular.largest_margin.home_team_name} / ${regular.largest_margin.away_team_name}`}
              record={regular.largest_margin}
              value={`${fmt.format(regular.largest_margin.margin)} pts`}
            />
          </section>
        </TabsContent>

        <TabsContent value="current" className="page">
          <CurrentSeason season={currentSeason} />
        </TabsContent>

        <TabsContent value="champions" className="page">
          <PageHead
            overline="The highest honor"
            title="Championship ledger"
            text="Official CGL champions beginning with the 2024 season."
          />
          <div className="ledger">
            {data.records.champions.map((c) => {
              const s = data.seasons.find((x) => x.season === c.season)!;
              const t = s.teams.find((x) => x.team_id === c.team_id)!;
              const ru = s.teams.find((x) => x.final_rank === 2)!;
              const f = s.matchups.find(
                (x) =>
                  x.stage === "championship_playoffs" &&
                  x.is_multiweek_series &&
                  (x.home_team_id === c.team_id ||
                    x.away_team_id === c.team_id),
              );
              return (
                <article key={c.season}>
                  <strong className="year">{c.season}</strong>
                  <span className="medal">
                    <Trophy />
                  </span>
                  <div>
                    <p className="eyebrow">CGL champion</p>
                    <h3><TeamLink season={c.season}>{c.team_name}</TeamLink></h3>
                    <p>{names(c.manager_names)}</p>
                  </div>
                  <dl>
                    <div>
                      <dt>Regular season</dt>
                      <dd>
                        {t.regular_season.wins}–{t.regular_season.losses} · #
                        {t.playoff_seed} seed
                      </dd>
                    </div>
                    <div>
                      <dt>Championship</dt>
                      <dd>
                        {f
                          ? `${fmt.format(Math.max(f.home_score ?? 0, f.away_score ?? 0))}–${fmt.format(Math.min(f.home_score ?? 0, f.away_score ?? 0))}`
                          : "—"}{" "}
                        vs. <b><TeamLink season={c.season}>{ru.team_name}</TeamLink></b>
                        <small>{names(ru.manager_names)}</small>
                      </dd>
                    </div>
                  </dl>
                </article>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="standings" className="page">
          <PageHead
            overline="Every season counts"
            title="All-time standings"
            text="Ranked by regular-season winning percentage, then wins and points scored."
          />
          <Standings rows={data.manager_history.standings} />
        </TabsContent>

        <TabsContent value="managers" className="page">
          <ManagerProfile managerId={managerId} setManagerId={setManagerId} />
        </TabsContent>

        <TabsContent value="head-to-head" className="page">
          <HeadToHead
            managerAId={managerAId}
            managerBId={managerBId}
            setManagerAId={setManagerAId}
            setManagerBId={setManagerBId}
          />
        </TabsContent>

        <TabsContent value="drafts" className="page">
          <DraftHistory managerId={managerId} />
        </TabsContent>

        <TabsContent value="records" className="page">
          <PageHead
            overline="Best, worst & wildest"
            title="The record board"
            text="Consolation games are preserved in season history but excluded here."
          />
          <RecordsLeaderboards boards={leaderboards} />
          <div className="section-title compact game-records">
            <div>
              <p className="eyebrow">Single-game history</p>
              <h2>Game records</h2>
            </div>
            <p>
              League-wide extremes from official regular-season and
              championship-playoff games.
            </p>
          </div>
          <RecordGroup number="01" name="Regular season">
            <RecordCard
              label="Highest score"
              title={regular.highest_weekly_score.team_name}
              record={regular.highest_weekly_score}
              value={fmt.format(regular.highest_weekly_score.points)}
            />
            <RecordCard
              label="Lowest score"
              title={regular.lowest_weekly_score.team_name}
              record={regular.lowest_weekly_score}
              value={fmt.format(regular.lowest_weekly_score.points)}
            />
            <RecordCard
              label="Highest score in a loss"
              title={regular.highest_score_in_loss.team_name}
              record={regular.highest_score_in_loss}
              value={fmt.format(regular.highest_score_in_loss.points)}
            />
            <RecordCard
              label="Lowest score in a win"
              title={regular.lowest_score_in_win.team_name}
              record={regular.lowest_score_in_win}
              value={fmt.format(regular.lowest_score_in_win.points)}
            />
            <RecordCard
              label="Largest margin"
              title={`${regular.largest_margin.home_team_name} / ${regular.largest_margin.away_team_name}`}
              record={regular.largest_margin}
              value={fmt.format(regular.largest_margin.margin)}
            />
            <RecordCard
              label="Closest game"
              title={`${regular.closest_game.home_team_name} / ${regular.closest_game.away_team_name}`}
              record={regular.closest_game}
              value={fmt.format(regular.closest_game.margin)}
            />
          </RecordGroup>
          <RecordGroup number="02" name="Championship playoffs">
            <RecordCard
              label="Highest playoff week"
              title={playoffs.highest_weekly_score.team_name}
              record={playoffs.highest_weekly_score}
              value={fmt.format(playoffs.highest_weekly_score.points)}
            />
            <RecordCard
              label="Lowest playoff week"
              title={playoffs.lowest_weekly_score.team_name}
              record={playoffs.lowest_weekly_score}
              value={fmt.format(playoffs.lowest_weekly_score.points)}
            />
            <RecordCard
              label="Largest playoff margin"
              title={`${playoffs.largest_single_week_or_round_margin.home_team_name} / ${playoffs.largest_single_week_or_round_margin.away_team_name}`}
              record={playoffs.largest_single_week_or_round_margin}
              value={fmt.format(
                playoffs.largest_single_week_or_round_margin.margin,
              )}
            />
          </RecordGroup>
          <RecordGroup number="03" name="Two-week championship series">
            <RecordCard
              label="Largest series margin"
              title={`${series.largest_margin.home_team_name} / ${series.largest_margin.away_team_name}`}
              record={series.largest_margin}
              value={fmt.format(series.largest_margin.margin)}
            />
            <RecordCard
              label="Closest series"
              title={`${series.closest_series.home_team_name} / ${series.closest_series.away_team_name}`}
              record={series.closest_series}
              value={fmt.format(series.closest_series.margin)}
            />
            <RecordCard
              label="Highest combined"
              title={`${series.highest_combined_score.home_team_name} / ${series.highest_combined_score.away_team_name}`}
              record={series.highest_combined_score}
              value={fmt.format(series.highest_combined_score.combined_score)}
            />
          </RecordGroup>
        </TabsContent>

        <TabsContent value="seasons" className="page">
          <div className="season-head">
            <PageHead overline="Year by year" title="Season archive" />
            <div className="year-pick">
              {data.seasons
                .filter((s) => s.is_complete)
                .map((s) => (
                  <button
                    key={s.season}
                    className={s.season === year ? "active" : ""}
                    onClick={() => setYear(String(s.season))}
                  >
                    {s.season}
                  </button>
                ))}
            </div>
          </div>
          <SeasonArchive key={season.season} season={season} />
        </TabsContent>
      </Tabs>
      <footer>
        <div className="crest mini">
          <b>CGL</b>
        </div>
        <p>Official statistical history begins in 2024.</p>
        <Swords />
      </footer>
    </main>
  );
}
