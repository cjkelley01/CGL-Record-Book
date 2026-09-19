import { data } from "@/lib/record-book/history";
import { updateView, viewLink } from "@/lib/record-book/navigation";
import type { ReactNode } from "react";

export function TeamLink({
  children,
  managerId,
  season,
}: {
  children: ReactNode;
  managerId?: string;
  season?: number;
}) {
  // Use the season's ownership, including names that have since changed.
  // A shared team opens its first listed owner's profile; owner-specific
  // standings and matchup links supply an explicit manager ID instead.
  const team = [...data.seasons]
    .sort((a, b) => b.season - a.season)
    .filter((entry) => season === undefined || entry.season === season)
    .flatMap((entry) => entry.teams)
    .find((entry) => entry.team_name === children);
  const id = managerId ?? team?.manager_ids[0];
  if (!id) return <>{children}</>;
  const manager = data.manager_history.standings.find((entry) => entry.manager_id === id);
  return (
    <a
      className="team-link"
      title={manager ? `View ${manager.manager_name}'s manager profile` : undefined}
      href={viewLink({ section: "managers", manager: id })}
      onClick={(event) => {
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        updateView({ section: "managers", manager: id });
        requestAnimationFrame(() => {
          document.querySelector<HTMLElement>('[role="tabpanel"][data-state="active"]')?.focus({ preventScroll: true });
          window.scrollTo({ top: 0, behavior: "instant" });
        });
      }}
    >
      {children}
    </a>
  );
}
