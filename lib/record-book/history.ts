import data from "@/app/data/core_history.json";

export { data };

export type Standing = (typeof data.manager_history.standings)[number];
export type Season = (typeof data.seasons)[number];
export type DraftPick = {
  season: number;
  overall_pick: number;
  round: number;
  round_pick: number;
  team_id: number;
  team_name: string;
  manager_ids: string[];
  manager_names: string[];
  player_id: number;
  player_name?: string | null;
  position?: string | null;
  keeper: boolean;
  player_resolved?: boolean;
};
export type RecordEntry = {
  season: number;
  matchup_period?: number;
  scoring_period?: number;
  team_name?: string;
  manager_names?: string[];
  points?: number;
  result?: string;
  home_team_name?: string | null;
  home_manager_names?: string[];
  home_score?: number | null;
  away_team_name?: string | null;
  away_manager_names?: string[];
  away_score?: number | null;
  margin?: number | null;
  combined_score?: number | null;
};
export type SeasonAward = {
  key: string;
  title: string;
  team_name?: string | null;
  manager_names: string[];
  value: string;
  detail: string;
};
export type Storyline = { label: string; title: string; text: string };
export type EnrichedSeason = Season & {
  awards?: SeasonAward[];
  storylines?: Storyline[];
};
export type LeaderRow = {
  rank: number;
  team_name: string;
  manager_name?: string;
  manager_names?: string[];
  value: number;
  games: number;
  season?: number;
  record?: string;
};
export type RecordLeaderboards = {
  minimum_games_for_percentage: number;
  career: Record<string, LeaderRow[]>;
  single_season: Record<string, LeaderRow[]>;
  streaks: Record<string, LeaderRow[]>;
};
export const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
export const names = (x?: string[]) => x?.join(" & ") ?? "—";
