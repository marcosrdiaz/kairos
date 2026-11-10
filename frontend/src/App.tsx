import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router";
import { AppShell } from "./app/AppShell";
import { CarteraPage } from "./app/CarteraPage";
import { InicioPage } from "./app/InicioPage";
import { AssetPage } from "./app/market/asset-chart/AssetPage";
import { NewsPage } from "./app/news-feed/NewsPage";
import { TraceProvider } from "./components/trace/TraceProvider";
import { PanelPage } from "./panel/PanelPage";
import { PhoneHomePage } from "./widget/PhoneHomePage";
import { OpenChatRoute } from "./voice/ChatDock";

// Laboratorio de componentes (T5-01): solo en desarrollo, fuera del build y del bundle principal.
const LabPage = import.meta.env.DEV ? lazy(() => import("./lab/LabPage")) : null;

export function App() {
  return (
    <TraceProvider>
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/inicio" replace />} />
        <Route path="inicio" element={<InicioPage />} />
        <Route path="cartera" element={<CarteraPage />} />
        <Route path="noticias" element={<NewsPage />} />
        <Route path="pregunta" element={<OpenChatRoute />} />
        <Route path="activo/:assetId" element={<AssetPage />} />
      </Route>
      <Route path="panel" element={<PanelPage />} />
      <Route path="widget" element={<PhoneHomePage />} />
      {LabPage && (
        <Route
          path="lab"
          element={
            <Suspense fallback={null}>
              <LabPage />
            </Suspense>
          }
        />
      )}
      <Route path="*" element={<Navigate to="/inicio" replace />} />
    </Routes>
    </TraceProvider>
  );
}
