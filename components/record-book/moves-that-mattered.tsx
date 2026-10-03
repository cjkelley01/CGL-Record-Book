"use client";

import { useState } from "react";
import { ArrowLeftRight, ChevronDown, Search, Sparkles } from "lucide-react";
import { PageHead } from "@/components/record-book/page-head";
import { fmt } from "@/lib/record-book/history";
import { useViewValue } from "@/lib/record-book/navigation";

type Contribution = {
  regular_points: number; regular_starts: number; playoff_points: number;
  playoff_starts: number; total_points: number; total_starts: number;
  weekly?: { week: number; stage: string; points: number }[];
};
type MovePlayer = { player_id: number; player_name: string; position?: string | number | null; contribution: Contribution };
type MoveSide = {
  team_id: number; team_name: string; manager_names: string[];
  acquired: MovePlayer[]; outgoing: { player_name: string; subsequent_team?: string; subsequent_contribution?: Contribution }[];
  contribution: Contribution;
};
type Move = {
  id: string; season: number; kind: string; date?: string | null; week: number;
  sides: MoveSide[]; badges: string[];
  counterfactual: { potential_swings: number; robust_swings: number; method: string; comparisons: {
    week: number; acquired_player: string; alternative: string; alternative_projected_points: number;
    alternative_actual_points: number; matchup_margin: number; potentially_swung: boolean; robust_across_top_three: boolean;
  }[] };
};
type MovesData = {
  coverage: { season: number; completed_transactions: number; activity_feed_topics: number; limitations: string }[];
  transactions: Move[];
  front_office: { manager_id: string; manager_name: string; badges: string[]; transaction_volume: number;
    waiver_hits: string[]; trade_hits: string[]; playoff_hits: string[]; seasons: number[] }[];
  counterfactual_limitations: string;
};

const categoryCopy: Record<string, { title: string; text: string }> = {
  waiver_gold: { title: "Waiver Wire Gold", text: "Undrafted additions who became substantial regular-season starters." },
  got_away: { title: "The Ones That Got Away", text: "Drops who later delivered meaningful starts for another team." },
  deal_maker: { title: "Deal Makers", text: "Trades that produced substantial starting-lineup value for at least one side." },
  buyer_remorse: { title: "Buyer’s Remorse", text: "Deals where one side received little lineup value while the other received much more." },
  championship_reinforcement: { title: "Championship Reinforcements", text: "Acquisitions used as starters in championship-bracket games." },
};
const categoryOrder = ["buyer_remorse", "got_away", "waiver_gold", "deal_maker", "championship_reinforcement"];
const badgeLabel: Record<string, string> = {
  waiver_gold: "Waiver Wire Gold", got_away: "Got Away", deal_maker: "Deal Maker",
  buyer_remorse: "Buyer’s Remorse", championship_reinforcement: "Playoff Reinforcement", turning_point: "Turning Point",
  waiver_whisperer: "Waiver Whisperer", deal_architect: "Deal Architect", playoff_acquirer: "Playoff Acquirer",
};

const movePoints = (move: Move) => move.sides.reduce((sum, side) => sum + side.contribution.total_points, 0);
const moveStarts = (move: Move) => move.sides.reduce((sum, side) => sum + side.contribution.total_starts, 0);
const playerList = (players: { player_name: string }[]) => players.map((player) => player.player_name).join(", ") || "None";

function MoveCard({ move, featured = false }: { move: Move; featured?: boolean }) {
  const explanation = move.badges.includes("got_away")
    ? move.sides.flatMap((side) => side.outgoing).find((player) => player.subsequent_contribution)?.player_name + " later became a meaningful starter elsewhere."
    : move.kind === "trade"
      ? "Both sides are shown together; value is measured only from actual starts after the deal."
      : `${fmt.format(movePoints(move))} points reached a starting lineup across ${moveStarts(move)} starts.`;
  return (
    <article className={`move-card${featured ? " featured" : ""}`}>
      <header>
        <div>
          <p className="eyebrow">{move.season} · Week {move.week} · {move.kind === "freeagent" ? "Free agent" : move.kind}</p>
          <h3>{move.kind === "trade" ? "Trade" : playerList(move.sides[0]?.acquired ?? [])}</h3>
        </div>
        <span className="move-date">{move.date ?? "Date unavailable"}</span>
      </header>
      <div className="move-sides">
        {move.sides.map((side) => (
          <section key={side.team_id}>
            <h4>{side.team_name}</h4>
            <p>{side.manager_names.join(" & ")}</p>
            <dl>
              <div><dt>Acquired</dt><dd>{playerList(side.acquired)}</dd></div>
              <div><dt>Sent / dropped</dt><dd>{playerList(side.outgoing)}</dd></div>
              <div><dt>Lineup value</dt><dd>{fmt.format(side.contribution.total_points)} pts · {side.contribution.total_starts} starts</dd></div>
              {side.contribution.playoff_starts > 0 && <div><dt>Playoffs</dt><dd>{fmt.format(side.contribution.playoff_points)} pts · {side.contribution.playoff_starts} starts</dd></div>}
            </dl>
          </section>
        ))}
      </div>
      <p className="move-explanation">{explanation}</p>
      <div className="move-badges">{move.badges.map((badge) => <span key={badge}>{badgeLabel[badge] ?? badge}</span>)}</div>
      <details className="move-numbers">
        <summary>Show the numbers <ChevronDown /></summary>
        <div>
          {move.sides.flatMap((side) => side.acquired.map((player) => ({ side, player }))).map(({ side, player }) => (
            <section key={`${side.team_id}:${player.player_id}`}>
              <h5>{player.player_name} · {side.team_name}</h5>
              <p>{fmt.format(player.contribution.regular_points)} regular-season points in {player.contribution.regular_starts} starts · {fmt.format(player.contribution.playoff_points)} playoff points in {player.contribution.playoff_starts} starts</p>
              {(player.contribution.weekly?.length ?? 0) > 0 && <ol>{player.contribution.weekly?.map((week) => <li key={week.week}><b>W{week.week}</b><span>{week.stage === "championship_playoffs" ? "Playoffs" : "Regular"}</span><strong>{fmt.format(week.points)}</strong></li>)}</ol>}
            </section>
          ))}
          {move.counterfactual.comparisons.length > 0 && <section className="comparison-evidence">
            <h5>Projection-based comparison</h5>
            {move.counterfactual.comparisons.map((row, index) => <p key={`${row.week}:${index}`}>Week {row.week}: {row.acquired_player} versus {row.alternative}, the highest-projected eligible bench option ({fmt.format(row.alternative_projected_points)} projected; {fmt.format(row.alternative_actual_points)} actual). The recorded margin was {fmt.format(row.matchup_margin)}. {row.potentially_swung ? "This comparison changes the matchup result." : "This comparison does not change the result."}</p>)}
            <small>{move.counterfactual.method}</small>
          </section>}
        </div>
      </details>
    </article>
  );
}

export function MovesThatMattered({ moves }: { moves: MovesData }) {
  const seasons = [...new Set(moves.transactions.map((move) => move.season))].sort();
  const [season, setSeason] = useViewValue("movesSeason", "all", ["all", ...seasons.map(String)]);
  const [query, setQuery] = useState("");
  const selected = moves.transactions.filter((move) => season === "all" || move.season === Number(season));
  const featured = selected.filter((move) => move.badges.includes("turning_point"))
    .sort((a, b) => b.counterfactual.robust_swings - a.counterfactual.robust_swings || movePoints(b) - movePoints(a)).slice(0, 3);
  const featuredIds = new Set(featured.map((move) => move.id));
  const assignedIds = new Set(featuredIds);
  const categories = categoryOrder.map((badge) => {
    const rows = selected.filter((move) => move.badges.includes(badge) && !assignedIds.has(move.id));
    rows.forEach((move) => assignedIds.add(move.id));
    return { badge, rows };
  }).filter((category) => category.rows.length > 0);
  const needle = query.trim().toLowerCase();
  const visibleHistory = needle ? selected.filter((move) => JSON.stringify(move.sides).toLowerCase().includes(needle) || move.kind.includes(needle) || String(move.week).includes(needle)) : selected;
  const coverage = moves.coverage.filter((row) => season === "all" || row.season === Number(season));
  const office = moves.front_office.filter((row) => season === "all" || row.seasons.includes(Number(season)));

  return <>
    <div className="moves-head">
      <PageHead overline="Transactions with consequences" title="Moves That Mattered" text="Trades, waiver claims and free-agent additions measured by the points managers actually put into CGL starting lineups." />
      <label>Season<select value={season} onChange={(event) => setSeason(event.target.value)}><option value="all">All-Time</option>{seasons.map((year) => <option key={year}>{year}</option>)}</select></label>
    </div>
    <aside className="coverage-note"><Sparkles /><div><b>What the archive supports</b><p>{coverage.map((row) => `${row.season}: ${row.completed_transactions} completed transactions`).join(" · ")}. Completed moves are recovered from player-card history and checked against weekly rosters. Historical rejected or failed moves are not available, and empty activity feeds are treated as coverage gaps—not proof that no moves happened.</p></div></aside>

    {featured.length > 0 && <section className="moves-section turning-points"><div className="section-title"><div><p className="eyebrow">Season-shaping evidence</p><h2>Turning Points</h2></div><p>Moves with substantial lineup value and at least one matchup that may change under a projection-based bench comparison.</p></div><div className="moves-grid">{featured.map((move) => <MoveCard key={move.id} move={move} featured />)}</div><p className="method-note">“Potentially swung” is a comparison, not proof of causation. {moves.counterfactual_limitations}</p></section>}

    {categories.map(({ badge, rows }) => <section className="moves-section" key={badge}><div className="section-title compact"><div><p className="eyebrow">Qualified highlights</p><h2>{categoryCopy[badge].title}</h2></div><p>{categoryCopy[badge].text}</p></div><div className="moves-grid">{rows.slice(0, 3).map((move) => <MoveCard key={move.id} move={move} />)}</div>{rows.length > 3 && <details className="more-moves"><summary>Show {rows.length - 3} more</summary><div className="moves-grid">{rows.slice(3).map((move) => <MoveCard key={move.id} move={move} />)}</div></details>}</section>)}

    {office.length > 0 && <section className="moves-section"><div className="section-title"><div><p className="eyebrow">Repeated success</p><h2>The Front Office</h2></div><p>Distinct qualifying moves, with total activity shown as context rather than a hit-rate ranking.</p></div><div className="front-office-grid">{office.map((row) => <article key={row.manager_id}><ArrowLeftRight /><h3>{row.manager_name}</h3><div>{row.badges.map((badge) => <span key={badge}>{badgeLabel[badge]}</span>)}</div><p>{new Set([...row.waiver_hits, ...row.trade_hits, ...row.playoff_hits]).size} distinct qualifying moves · {row.transaction_volume} completed acquisitions · {row.seasons.join(", ")}</p><small>{row.seasons.length > 1 ? "Success across multiple seasons" : "Repeated success within one season"}</small></article>)}</div></section>}

    <section className="moves-section transaction-history"><div className="section-title"><div><p className="eyebrow">The recovered ledger</p><h2>Transaction History</h2></div><label><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search team or player" /></label></div><p className="history-count">{visibleHistory.length} completed acquisitions. Lineup-only changes and draft selections are excluded.</p><div className="history-list">{visibleHistory.map((move) => <details key={move.id}><summary><span><b>{move.season} · W{move.week}</b>{move.kind === "trade" ? "Trade" : playerList(move.sides[0]?.acquired ?? [])}</span><span>{move.sides.map((side) => side.team_name).join(" ↔ ")} · {fmt.format(movePoints(move))} starter pts</span></summary><MoveCard move={move} /></details>)}</div></section>
  </>;
}
