"use client";

import { ArrowRight, CalendarRange, Quote, Sparkles } from "lucide-react";
import { PageHead } from "@/components/record-book/page-head";
import { useViewValue } from "@/lib/record-book/navigation";

type Story = {
  id: string;
  story_type: string;
  priority: number;
  transaction_ids: string[];
  manager_ids: string[];
  relevant_seasons: number[];
  span: string;
  headline: string;
  label: string;
  context: string;
  decision: string;
  aftermath: string;
  evidence: string[];
};

type MovesData = { stories: Story[]; coverage: { season: number }[] };

function StoryTimeline({ story }: { story: Story }) {
  return <div className="story-timeline">
    <section><span>01</span><div><b>Before</b><p>{story.context}</p></div></section>
    <section><span>02</span><div><b>The move</b><p>{story.decision}</p></div></section>
    <section><span>03</span><div><b>Afterward</b><p>{story.aftermath}</p></div></section>
  </div>;
}

function Evidence({ story }: { story: Story }) {
  return <ul className="story-evidence" aria-label="Selected evidence">
    {story.evidence.map((item) => <li key={item}>{item}</li>)}
  </ul>;
}

function LeadStory({ story }: { story: Story }) {
  return <article className="move-story-lead">
    <div className="lead-story-copy">
      <p className="eyebrow">{story.label}</p>
      <h2>{story.headline}</h2>
      <p className="lead-context">{story.context}</p>
      <Evidence story={story} />
    </div>
    <StoryTimeline story={story} />
  </article>;
}

function FeatureStory({ story, index }: { story: Story; index: number }) {
  return <article className="move-story-feature">
    <header><span>{String(index).padStart(2, "0")}</span><div><p className="eyebrow">{story.label}</p><h3>{story.headline}</h3></div></header>
    <div className="feature-story-body">
      <p>{story.context}</p>
      <p><b>The decision:</b> {story.decision}</p>
      <p><b>What followed:</b> {story.aftermath}</p>
    </div>
    <Evidence story={story} />
  </article>;
}

function CrossYearStory({ story }: { story: Story }) {
  return <article className="cross-year-story">
    <CalendarRange />
    <div><p className="eyebrow">{story.label}</p><h3>{story.headline}</h3><p>{story.context} {story.decision}</p><p>{story.aftermath}</p></div>
    <Evidence story={story} />
  </article>;
}

function ShortStory({ story }: { story: Story }) {
  return <article className="short-move-story">
    <Quote />
    <p className="eyebrow">{story.label}</p>
    <h3>{story.headline}</h3>
    <p>{story.context}</p><p>{story.decision}</p><p>{story.aftermath}</p>
    <Evidence story={story} />
  </article>;
}

export function MovesThatMattered({ moves }: { moves: MovesData }) {
  const seasons = moves.coverage.map((row) => row.season).sort();
  const [season, setSeason] = useViewValue("movesSeason", "all", ["all", ...seasons.map(String)]);
  const stories = moves.stories.filter((story) => season === "all" || story.relevant_seasons.includes(Number(season))).sort((a, b) => b.priority - a.priority);
  const [lead, ...remaining] = stories;
  const crossYear = remaining.filter((story) => story.story_type === "cross_year");
  const features = remaining.filter((story) => story.story_type === "feature");
  const shorter = remaining.filter((story) => ["timeline", "brief", "lead"].includes(story.story_type));

  return <>
    <div className="moves-head">
      <PageHead overline="Decisions with a legacy" title="Moves That Mattered" text="The draft picks, trades and second chances that became part of CGL history." />
      <label>Season<select value={season} onChange={(event) => setSeason(event.target.value)}><option value="all">All-Time</option>{seasons.map((year) => <option key={year}>{year}</option>)}</select></label>
    </div>

    {!lead ? <section className="moves-empty"><Sparkles /><h2>No story has earned the page yet.</h2><p>The archive contains transactions for this season, but none currently meet the editorial standard for a published feature.</p></section> : <>
      <LeadStory story={lead} />
      {features.length > 0 && <section className="move-story-section">
        <div className="story-section-heading"><p className="eyebrow">More from the archive</p><h2>Moves that shaped a season</h2><ArrowRight /></div>
        <div className="feature-story-list">{features.map((story, index) => <FeatureStory key={story.id} story={story} index={index + 1} />)}</div>
      </section>}
      {crossYear.length > 0 && <section className="move-story-section">
        <div className="story-section-heading"><p className="eyebrow">Across the seasons</p><h2>Patterns that lasted</h2></div>
        {crossYear.map((story) => <CrossYearStory key={story.id} story={story} />)}
      </section>}
      {shorter.length > 0 && <section className="move-story-section">
        <div className="story-section-heading"><p className="eyebrow">Worth remembering</p><h2>More stories from the archive</h2></div>
        <div className="short-story-grid">{shorter.map((story) => <ShortStory key={story.id} story={story} />)}</div>
      </section>}
    </>}
  </>;
}

