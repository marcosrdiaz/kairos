import { PanelNotice } from "../components/notices/Notices";

/**
 * Avisos del panel (T2-12): aviso de IA (AI Act art. 50) y "no es asesoramiento".
 * Va justo debajo de la cabecera, antes del contenido, para que sea lo primero que se lea.
 */
export function PanelNoticeSlot() {
  return (
    <div data-slot="panel-notices">
      <PanelNotice />
    </div>
  );
}
