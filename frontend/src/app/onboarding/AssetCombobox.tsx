import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import type { AssetOut } from "../../api/generated/schema";
import { buttonSecondary } from "../../components/button";
import { assetDetails } from "./labels";
import { MIN_QUERY_LENGTH, useAssetLookup } from "./useAssetLookup";

interface AssetComboboxProps {
  label: string;
  value: AssetOut | null;
  onChange: (asset: AssetOut | null) => void;
  error?: string | undefined;
  /**
   * Error que se pinta con un activo ya elegido (p. ej. "destino igual al origen" del
   * traspaso). Opcional: sin ella, con activo elegido no se muestra ningún error.
   */
  selectedError?: string | undefined;
  /** Para la fila recién añadida: el foco va a su buscador. */
  autoFocus?: boolean;
}

/**
 * Buscador de activo con el patrón combobox de ARIA 1.2 (lista con aria-activedescendant):
 * flechas para recorrer, Intro para elegir, Escape para cerrar. El número de resultados se
 * anuncia en una región `status`. Una vez elegido, se muestra el activo con "Cambiar".
 */
export function AssetCombobox({
  label,
  value,
  onChange,
  error,
  selectedError,
  autoFocus,
}: AssetComboboxProps) {
  const uid = useId();
  const inputId = `${uid}-input`;
  const listId = `${uid}-list`;
  const hintId = `${uid}-hint`;
  const errorId = `${uid}-error`;
  const inputRef = useRef<HTMLInputElement>(null);
  const changeRef = useRef(false);
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const lookup = useAssetLookup(text);
  const results = lookup.enabled ? (lookup.data ?? []) : [];
  const showList = open && results.length > 0;

  useEffect(() => {
    if (value === null && changeRef.current) {
      changeRef.current = false;
      inputRef.current?.focus();
    }
  }, [value]);

  function choose(asset: AssetOut) {
    onChange(asset);
    setText("");
    setOpen(false);
    setActive(-1);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && showList) {
      e.preventDefault(); // no envía el formulario
      const pick = results[active >= 0 ? active : 0];
      if (pick) choose(pick);
    } else if (e.key === "Escape") {
      if (showList) setOpen(false);
      else setText("");
    }
  }

  if (value) {
    return (
      <div
        role="group"
        aria-labelledby={`${uid}-label`}
        aria-describedby={selectedError ? errorId : undefined}
        className="flex flex-col gap-2"
      >
        <span id={`${uid}-label`} className="text-base font-semibold text-ink">
          {label}
        </span>
        <div className="flex flex-wrap items-center gap-3 rounded-control border border-line bg-surface-muted p-3">
          <span className="flex min-w-0 flex-1 flex-col">
            <span className="font-semibold text-ink">{value.name}</span>
            <span className="text-sm text-ink-muted">{assetDetails(value)}</span>
          </span>
          <button
            type="button"
            className={buttonSecondary}
            aria-label={`Cambiar ${value.name}`}
            onClick={() => {
              changeRef.current = true;
              onChange(null);
            }}
          >
            Cambiar
          </button>
        </div>
        {/* Solo si quien lo usa lo pide: errores del activo elegido (destino = origen). */}
        {selectedError && (
          <span id={errorId} className="text-sm font-medium text-error">
            {selectedError}
          </span>
        )}
      </div>
    );
  }

  let statusText = "";
  if (open && lookup.enabled && lookup.settled && !lookup.isFetching) {
    if (lookup.isError) statusText = "No hemos podido buscar ahora mismo. Vuelve a intentarlo.";
    else if (results.length === 0) statusText = `No hay activos que coincidan con «${text.trim()}».`;
    else statusText = results.length === 1 ? "1 activo encontrado." : `${results.length} activos encontrados.`;
  }

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={inputId} className="text-base font-semibold text-ink">
        {label}
      </label>
      <div className="relative flex flex-col">
        <input
          ref={inputRef}
          id={inputId}
          autoFocus={autoFocus}
          type="text"
          role="combobox"
          autoComplete="off"
          spellCheck={false}
          aria-autocomplete="list"
          aria-expanded={showList}
          aria-controls={listId}
          aria-activedescendant={showList && active >= 0 ? `${listId}-${active}` : undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${hintId} ${errorId}` : hintId}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setOpen(true);
            setActive(-1);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
          className="min-h-touch rounded-control border border-line-strong bg-surface px-3 text-base text-ink placeholder:text-ink-muted aria-invalid:border-error"
          placeholder="ISIN, ticker o nombre"
        />
        <ul
          id={listId}
          role="listbox"
          aria-label="Activos encontrados"
          hidden={!showList}
          className="absolute inset-x-0 top-full z-10 m-0 mt-1 max-h-80 list-none overflow-y-auto rounded-control border border-line-strong bg-surface p-1"
        >
          {results.map((a, i) => (
            <li
              key={a.id}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              // mousedown sin perder el foco del input (si no, el blur cierra la lista antes del click)
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => choose(a)}
              className={`flex cursor-pointer flex-col rounded-control px-3 py-2 ${i === active ? "bg-accent-tint" : "hover:bg-surface-muted"}`}
            >
              <span className="font-medium text-ink">{a.name}</span>
              <span className="text-sm text-ink-muted">{assetDetails(a)}</span>
            </li>
          ))}
        </ul>
      </div>
      <span id={hintId} className="text-sm text-ink-muted">
        Escribe al menos {MIN_QUERY_LENGTH} caracteres.
      </span>
      {error && (
        <span id={errorId} className="text-sm font-medium text-error">
          {error}
        </span>
      )}
      <span role="status" className="text-sm text-ink-muted empty:hidden">
        {statusText}
      </span>
    </div>
  );
}
