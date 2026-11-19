"use client";

export function RecordGroup({
  name,
  children,
}: {
  name: string;
  children: React.ReactNode;
}) {
  return (
    <section className="record-group">
      <h3>{name}</h3>
      <div className="record-grid">{children}</div>
    </section>
  );
}
