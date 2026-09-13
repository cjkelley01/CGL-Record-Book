"use client";

export function RecordGroup({
  number,
  name,
  children,
}: {
  number: string;
  name: string;
  children: React.ReactNode;
}) {
  return (
    <section className="record-group">
      <div>
        <strong>{number}</strong>
        <p className="eyebrow">Record class</p>
        <h3>{name}</h3>
      </div>
      <div className="record-grid">{children}</div>
    </section>
  );
}
