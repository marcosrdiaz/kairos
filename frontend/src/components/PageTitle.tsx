import type { ReactNode } from "react";

interface PageTitleProps {
  children: ReactNode;
  /** Solo para lectores de pantalla (la página ya tiene un titular visual propio). */
  visuallyHidden?: boolean;
}

export function PageTitle({ children, visuallyHidden = false }: PageTitleProps) {
  return (
    <h1
      className={
        visuallyHidden ? "sr-only" : "m-0 mb-6 text-2xl font-semibold leading-tight text-ink"
      }
    >
      {children}
    </h1>
  );
}

export function EmptyNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-card border border-line bg-surface p-5 text-ink-muted">{children}</p>
  );
}
