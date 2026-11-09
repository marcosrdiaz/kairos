import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "../../api/client";
import type { TransactionOut } from "../../api/generated/schema";
import { buttonPrimary } from "../../components/button";
import { formatUnits } from "../../lib/format";
import { AssetCombobox } from "../onboarding/AssetCombobox";
import { ASSET_TYPE_LABEL } from "../onboarding/labels";
import { ChoiceGroup, SelectField, TextField } from "./fields";
import { OperationResult } from "./OperationResult";
import { buildOperation, emptyDraft, type DraftErrors, type OperationDraft, type OperationKind } from "./operationDraft";
import { operationErrorText, transferNotAllowed } from "./operationError";
import { TransferNotAllowedNotice } from "./TransferNotAllowedNotice";
import { usePortfolio } from "./usePortfolio";

const KINDS: { value: OperationKind; label: string }[] = [
  { value: "buy", label: "Compra" },
  { value: "sell", label: "Venta" },
  { value: "transfer", label: "Traspaso" },
];
const SUBMIT: Record<OperationKind, string> = {
  buy: "Registrar compra",
  sell: "Registrar venta",
  transfer: "Registrar traspaso",
};

interface Submitted {
  built: Extract<ReturnType<typeof buildOperation>, { ok: true }>;
  kind: OperationKind;
  /** Nombres conocidos al enviar: respaldo si la posición desaparece (venta o traspaso total). */
  label: string | null;
  toLabel: string | null;
}

/** "300.5" (cuerpo enviado) -> "300,5" (como se escribe en el campo). */
const toInput = (value: string) => value.replace(".", ",");

/**
 * Registro de operaciones (RF-04, RF-05, RF-06) en la cartera elegida, solo en KAIROS: compra
 * o venta por importe o por participaciones y traspaso fondo → fondo. El backend usa el precio
 * del momento y devuelve el efecto; si el traspaso no es entre fondos, se explica por qué.
 */
export function OperationsForm({ portfolioId }: { portfolioId: string }) {
  const queryClient = useQueryClient();
  const portfolio = usePortfolio(portfolioId);
  const [draft, setDraft] = useState<OperationDraft>(() => emptyDraft());
  const [errors, setErrors] = useState<DraftErrors>({});
  const resultRef = useRef<HTMLElement>(null);
  const noticeRef = useRef<HTMLDivElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);
  const base = `/portfolios/${encodeURIComponent(portfolioId)}`;

  const save = useMutation({
    mutationFn: ({ built }: Submitted) =>
      built.kind === "transfer"
        ? apiPost<TransactionOut>(`${base}/transfers`, built.body, { mock: "TransactionOut.transfer" })
        : apiPost<TransactionOut>(`${base}/transactions`, built.body, { mock: "TransactionOut" }),
    onSuccess: () => {
      setDraft((d) => ({ ...emptyDraft(d.kind), mode: d.mode }));
      // La cartera, el estado, la exposición y las noticias dependen de las posiciones.
      void queryClient.invalidateQueries();
    },
  });
  const notAllowed = transferNotAllowed(save.error);
  const showNotice = notAllowed !== null;

  useEffect(() => {
    if (save.isSuccess) resultRef.current?.focus();
  }, [save.isSuccess]);
  useEffect(() => {
    if (showNotice) noticeRef.current?.focus();
  }, [showNotice]);

  const positions = portfolio.data?.positions ?? [];
  const held = positions.find((p) => p.asset_id === draft.heldAssetId);

  function update(patch: Partial<OperationDraft>) {
    setDraft((d) => ({ ...d, ...patch }));
    setErrors((e) => {
      const next = { ...e };
      for (const k of Object.keys(patch)) delete next[k as keyof DraftErrors];
      return next;
    });
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const built = buildOperation(draft);
    if (!built.ok) {
      setErrors(built.errors);
      return;
    }
    setErrors({});
    const label = draft.kind === "buy" ? (draft.asset?.name ?? null) : (held?.name ?? null);
    const toLabel = draft.kind === "transfer" ? (draft.asset?.name ?? null) : null;
    save.mutate({ built, kind: draft.kind, label, toLabel });
  }

  function sellInstead() {
    const from = save.variables?.built;
    if (from?.kind !== "transfer") return;
    save.reset();
    // Cantidad y unidad salen del cuerpo enviado, no del borrador (que puede haber cambiado).
    const { amount_eur, units } = from.body;
    setDraft({
      ...emptyDraft("sell"),
      heldAssetId: from.body.from_asset_id,
      mode: amount_eur ? "amount" : "units",
      quantity: toInput(amount_eur ?? units ?? ""),
    });
    requestAnimationFrame(() => submitRef.current?.focus());
  }

  const positionOptions = positions.map((p) => ({
    value: p.asset_id,
    label: `${p.name} (${ASSET_TYPE_LABEL[p.asset_type]}) · ${formatUnits(p.units)} participaciones`,
  }));
  let positionsHint: string | undefined;
  if (portfolio.isPending) positionsHint = "Cargando las posiciones…";
  else if (portfolio.isError) positionsHint = "No podemos cargar las posiciones ahora mismo.";
  else if (positions.length === 0) positionsHint = "Esta cartera aún no tiene posiciones.";

  return (
    <div className="flex flex-col gap-5">
      {save.isSuccess && (
        <OperationResult
          ref={resultRef}
          tx={save.data}
          fallbackName={save.variables.label}
          fallbackToName={save.variables.toLabel}
        />
      )}
      <form noValidate onSubmit={onSubmit} className="flex flex-col gap-5 rounded-card border border-line bg-surface p-5">
        <ChoiceGroup
          legend="Tipo de operación"
          value={draft.kind}
          options={KINDS}
          onValue={(kind) => {
            // Cantidad vacía: cada tipo tiene su unidad por defecto (importe o participaciones)
            // y conservar la cifra la cambiaría de unidad sin que se note.
            setDraft(emptyDraft(kind));
            setErrors({});
            save.reset();
          }}
        />
        {draft.kind === "buy" ? (
          <AssetCombobox label="Activo" value={draft.asset} onChange={(asset) => update({ asset })} error={errors.asset} />
        ) : (
          <SelectField
            label={draft.kind === "sell" ? "Posición" : "Fondo de origen"}
            hint={positionsHint ?? (draft.kind === "transfer" ? "Solo hay traspaso entre fondos de inversión." : undefined)}
            placeholder="Elige una posición"
            value={draft.heldAssetId}
            options={positionOptions}
            onValue={(heldAssetId) => update({ heldAssetId })}
            error={errors.heldAssetId}
          />
        )}
        {draft.kind === "transfer" && (
          <AssetCombobox
            label="Fondo de destino"
            value={draft.asset}
            onChange={(asset) => update({ asset })}
            error={errors.asset}
          />
        )}
        <ChoiceGroup
          legend="Cantidad"
          value={draft.mode}
          options={[
            { value: "amount", label: "Por importe (€)" },
            { value: "units", label: "Por participaciones" },
          ]}
          onValue={(mode) => update({ mode, quantity: "" })}
        />
        <TextField
          label={draft.mode === "amount" ? "Importe (€)" : "Participaciones"}
          hint={
            draft.mode === "amount"
              ? "Con coma para los céntimos. Se usa el precio del momento."
              : "Con coma para los decimales. Se usa el precio del momento."
          }
          inputMode="decimal"
          autoComplete="off"
          value={draft.quantity}
          onValue={(quantity) => update({ quantity })}
          error={errors.quantity}
        />
        <button
          ref={submitRef}
          type="submit"
          className={`${buttonPrimary} self-start`}
          disabled={save.isPending}
          aria-disabled={save.isPending}
        >
          {save.isPending ? "Registrando…" : SUBMIT[draft.kind]}
        </button>
        {notAllowed && <TransferNotAllowedNotice ref={noticeRef} info={notAllowed} onSellInstead={sellInstead} />}
        <p role="status" className="m-0 text-base font-medium text-error empty:hidden">
          {save.isError && !notAllowed && save.variables
            ? operationErrorText(save.error, save.variables.kind, save.variables.label)
            : ""}
        </p>
      </form>
    </div>
  );
}
