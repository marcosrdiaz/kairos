/** Icono de la sección Noticias (periódico). Decorativo, como los de `components/icons`. */
export function NewsIcon({ className = "size-6" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <path d="M5 4h12v15a1 1 0 0 0 1 1H6a2 2 0 0 1-2-2V5a1 1 0 0 1 1-1z" />
      <path d="M17 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2" />
      <path d="M8 8h5M8 11.5h5M8 15h3" />
    </svg>
  );
}
