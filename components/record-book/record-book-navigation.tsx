import { Menu, X } from "lucide-react";
import { type ReactNode, useEffect, useRef, useState } from "react";

const groups = [
  { label: "Season", pages: [
    ["overview", "Overview"], ["current", "2026 Live"],
    ["standings", "Standings"], ["forecast", "Playoff Odds"],
  ] },
  { label: "History", pages: [
    ["champions", "Champions"], ["seasons", "Seasons"], ["records", "Records"],
    ["managers", "Managers"], ["head-to-head", "Head-to-Head"], ["drafts", "Drafts"],
  ] },
  { label: "Analytics", pages: [
    ["analytics", "League Analytics"], ["moves", "Moves That Mattered"],
  ] },
] as const;

const pages = groups.flatMap(({ pages }) => [...pages]);
export const sectionIds = pages.map(([id]) => id);

type NavigationProps = { section: string; hrefFor: (id: string) => string };

function PageLinks({ section, hrefFor, onNavigate }: NavigationProps & { onNavigate?: () => void }) {
  return (
    <nav aria-label="Record Book pages" className="record-book-links">
      {groups.map(({ label, pages }) => (
        <div key={label}>
          <h2>{label}</h2>
          <ul>
            {pages.map(([id, title]) => (
              <li key={id}>
                <a href={hrefFor(id)} aria-current={section === id ? "page" : undefined} onClick={onNavigate}>
                  {title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function RecordBookLayout({ children, ...props }: NavigationProps & { children: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  const close = () => dialog.current?.close();
  const title = pages.find(([id]) => id === props.section)?.[1];

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1100px)");
    const closeOnDesktop = () => {
      if (desktop.matches) dialog.current?.close();
    };
    desktop.addEventListener("change", closeOnDesktop);
    return () => desktop.removeEventListener("change", closeOnDesktop);
  }, []);

  return (
    <div className="record-book-layout">
      <aside className="record-book-sidebar"><PageLinks {...props} /></aside>
      <div className="record-book-mobile-bar">
        <button type="button" aria-haspopup="dialog" aria-controls="record-book-menu" aria-expanded={open}
          onClick={() => { dialog.current?.showModal(); setOpen(true); }}>
          <Menu aria-hidden="true" size={20} /> Menu
        </button>
        <span>{title}</span>
      </div>
      <dialog ref={dialog} id="record-book-menu" className="record-book-drawer"
        aria-labelledby="record-book-menu-title" onClose={() => setOpen(false)}
        onClick={(event) => { if (event.target === event.currentTarget) close(); }}>
        <div className="record-book-drawer-inner">
          <div className="record-book-drawer-header">
            <h2 id="record-book-menu-title">Record Book</h2>
            <button type="button" aria-label="Close navigation" onClick={close}><X aria-hidden="true" size={22} /></button>
          </div>
          <PageLinks {...props} onNavigate={close} />
        </div>
      </dialog>
      <main id="record-book-content" tabIndex={-1}>{children}</main>
    </div>
  );
}
