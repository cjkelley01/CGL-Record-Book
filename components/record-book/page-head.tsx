"use client";

export function PageHead({
  overline,
  title,
  text,
}: {
  overline: string;
  title: string;
  text?: string;
}) {
  return (
    <header className="page-head">
      <p className="eyebrow gold">{overline}</p>
      <h2>{title}</h2>
      {text && <p>{text}</p>}
    </header>
  );
}
