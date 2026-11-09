import { useSearchParams } from "react-router";
import { useStatus } from "../api/hooks/useStatus";
import { LogoTile } from "../components/icons";
import { AlertNotice } from "./AlertNotice";
import { HomeWidget } from "./HomeWidget";

const DEFAULT_PORTFOLIO = "laura";

const timeFmt = new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit" });
const dayFmt = new Intl.DateTimeFormat("es-ES", { weekday: "long", day: "numeric", month: "long" });

/** "lunes, 9 de noviembre" -> "Lunes, 9 de noviembre" (en español solo la primera). */
function capitalizeFirst(text: string): string {
  return text.charAt(0).toLocaleUpperCase("es-ES") + text.slice(1);
}

/** Iconos de app genéricos del dock (decorativos, sin marcas de terceros). */
function DockIcon({ tone }: { tone: string }) {
  return <span aria-hidden="true" className={`block size-12 rounded-[28%] ${tone}`} />;
}

/**
 * `/widget`: pantalla de inicio de un móvil simulada con el widget de Kairos (RF-13, D-004).
 * En escritorio se ve un móvil centrado; en un móvil real ocupa la pantalla.
 * El estado y los avisos se actualizan solos cada 5 s; si falla una consulta, sigue lo último.
 */
export function PhoneHomePage() {
  const [params] = useSearchParams();
  const portfolioId = params.get("p") || DEFAULT_PORTFOLIO;
  const query = params.toString() ? `?${params.toString()}` : "";
  const { data, isPending, isError } = useStatus(portfolioId);
  const now = new Date();

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-paper p-0 sm:p-8">
      <h1 className="sr-only">Widget de Kairos en la pantalla de inicio del móvil (simulación)</h1>

      <div className="relative flex min-h-dvh w-full flex-col overflow-hidden bg-linear-to-b from-accent-tint via-surface-muted to-paper sm:min-h-0 sm:h-[46rem] sm:w-[23rem] sm:rounded-[3rem] sm:border-[10px] sm:border-ink">
        {/* Barra de estado y reloj (decorativos) */}
        <div
          aria-hidden="true"
          className="flex items-center justify-between px-7 pt-4 text-sm font-semibold text-ink"
        >
          <span>{timeFmt.format(now)}</span>
          <span className="flex items-center gap-1">
            <span className="block h-2.5 w-4 rounded-sm bg-ink" />
          </span>
        </div>
        <div aria-hidden="true" className="mt-8 text-center text-ink">
          <p className="m-0 text-[4rem] font-semibold leading-none tracking-tight">
            {timeFmt.format(now)}
          </p>
          <p className="m-0 mt-2 text-base text-ink-muted">{capitalizeFirst(dayFmt.format(now))}</p>
        </div>

        <div className="mt-6 px-5">
          <AlertNotice portfolioId={portfolioId} href={`/inicio${query}`} />
        </div>

        <div aria-live="polite" className="mt-4 px-5">
          {isPending && (
            <div
              role="status"
              aria-label="Cargando el widget"
              className="h-44 rounded-[1.75rem] bg-surface/70 motion-safe:animate-pulse"
            />
          )}
          {isError && !data && (
            <p className="m-0 rounded-[1.75rem] bg-surface/90 p-4 text-ink-muted">
              Ahora mismo no podemos mostrar el estado de tu cartera.
            </p>
          )}
          {data && <HomeWidget status={data} href={`/inicio${query}`} />}
        </div>

        <div
          aria-hidden="true"
          className="mx-4 mb-4 mt-auto flex justify-around rounded-[2rem] bg-surface/60 p-3"
        >
          <LogoTile className="size-12" />
          <DockIcon tone="bg-icon-blue-bg" />
          <DockIcon tone="bg-icon-green-bg" />
          <DockIcon tone="bg-icon-purple-bg" />
        </div>
      </div>

      <p className="m-0 hidden text-sm text-ink-muted sm:block">
        Simulación del widget en la pantalla de inicio del móvil. Tócalo para abrir la app.
      </p>
    </main>
  );
}
