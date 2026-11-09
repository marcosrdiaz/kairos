import { Navigate, Route, Routes } from "react-router";
import { AppShell } from "./app/AppShell";
import { CarteraPage } from "./app/CarteraPage";
import { InicioPage } from "./app/InicioPage";
import { PanelPage } from "./panel/PanelPage";
import { PhoneHomePage } from "./widget/PhoneHomePage";
import { OpenChatRoute } from "./voice/ChatDock";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/inicio" replace />} />
        <Route path="inicio" element={<InicioPage />} />
        <Route path="cartera" element={<CarteraPage />} />
        <Route path="pregunta" element={<OpenChatRoute />} />
      </Route>
      <Route path="panel" element={<PanelPage />} />
      <Route path="widget" element={<PhoneHomePage />} />
      <Route path="*" element={<Navigate to="/inicio" replace />} />
    </Routes>
  );
}
