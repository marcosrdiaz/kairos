import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ApiError } from "../../api/client";
import type { PortfolioSummaryOut } from "../../api/generated/schema";
import { useUpdatePortfolio } from "../../api/hooks/usePortfolioManage";
import { buttonPrimary, buttonSecondary } from "../../components/button";
import { NAME_MAX } from "../onboarding/portfolioDetails";
import { kindLabel } from "./kindLabel";

interface PortfolioRowProps {
  portfolio: PortfolioSummaryOut;
  selected: boolean;
  onRenamed: (oldName: string, newName: string) => void;
  onDelete: () => void;
}

function renameErrorText(error: unknown): string {
  if (error instanceof ApiError && error.status === 422) return "Ese nombre no es válido.";
  if (error instanceof ApiError && error.status === 404) return "Esta cartera ya no existe.";
  return "No hemos podido cambiar el nombre. Vuelve a intentarlo en unos segundos.";
}

/**
 * Una cartera en «Tus carteras»: nombre, tipo y acciones. «Renombrar» cambia la fila por un
 * campo con el nombre (foco en él); Esc o «Cancelar» lo deja como estaba y el foco vuelve.
 */
export function PortfolioRow({ portfolio, selected, onRenamed, onDelete }: PortfolioRowProps) {
  const update = useUpdatePortfolio();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(portfolio.name);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const renameRef = useRef<HTMLButtonElement>(null);
  const restoreFocus = useRef(false);
  const id = useId();
  const kind = kindLabel(portfolio);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
    else if (restoreFocus.current) {
      restoreFocus.current = false;
      renameRef.current?.focus();
    }
  }, [editing]);

  function stopEditing() {
    restoreFocus.current = true;
    setEditing(false);
    setError("");
    update.reset();
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return setError("Ponle un nombre a la cartera.");
    if (trimmed.length > NAME_MAX) return setError(`El nombre no puede pasar de ${NAME_MAX} caracteres.`);
    if (trimmed === portfolio.name) return stopEditing();
    setError("");
    update.mutate(
      { id: portfolio.id, body: { name: trimmed } },
      {
        onSuccess: (p) => {
          stopEditing();
          onRenamed(portfolio.name, p.name);
        },
        onError: (err) => setError(renameErrorText(err)),
      },
    );
  }

  if (editing) {
    return (
      <li className="rounded-card border border-line bg-surface p-4">
        <form noValidate onSubmit={submit} className="flex flex-col gap-2">
          <label htmlFor={`${id}-name`} className="text-base font-semibold text-ink">
            Nuevo nombre de «{portfolio.name}»
          </label>
          <input
            id={`${id}-name`}
            ref={inputRef}
            value={name}
            maxLength={NAME_MAX}
            autoComplete="off"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") stopEditing();
            }}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? `${id}-error` : undefined}
            className="min-h-touch w-full rounded-control border border-line-strong bg-surface px-3 text-base text-ink aria-invalid:border-error"
          />
          {error && (
            <span id={`${id}-error`} role="alert" className="text-sm font-medium text-error">
              {error}
            </span>
          )}
          <div className="flex flex-wrap gap-2 pt-1">
            <button type="submit" className={buttonPrimary} disabled={update.isPending} aria-disabled={update.isPending}>
              {update.isPending ? "Guardando…" : "Guardar"}
            </button>
            <button type="button" className={buttonSecondary} disabled={update.isPending} onClick={stopEditing}>
              Cancelar
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-card border border-line bg-surface p-4">
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-base font-semibold text-ink">{portfolio.name}</span>
        <span className="text-sm text-ink-muted">
          {[kind, selected ? "Elegida" : ""].filter(Boolean).join(" · ") || "Sin tipo"}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          ref={renameRef}
          type="button"
          className={buttonSecondary}
          aria-label={`Renombrar «${portfolio.name}»`}
          onClick={() => {
            setName(portfolio.name);
            setEditing(true);
          }}
        >
          Renombrar
        </button>
        <button
          type="button"
          className={buttonSecondary}
          aria-label={`Borrar «${portfolio.name}»`}
          onClick={onDelete}
        >
          Borrar
        </button>
      </div>
    </li>
  );
}
