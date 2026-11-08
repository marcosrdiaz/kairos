import type { ReactNode } from "react";

export function PageTitle({ children }: { children: ReactNode }) {
  return <h1 className="m-0 mb-4 text-2xl font-semibold leading-tight text-ink">{children}</h1>;
}

export function EmptyNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-card border border-line bg-surface p-4 text-ink-muted">{children}</p>
  );
}
