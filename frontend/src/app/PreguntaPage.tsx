import { PageTitle } from "../components/PageTitle";
import { VoiceAsk } from "../voice/VoiceAsk";
import { usePortfolioId } from "./portfolio-picker/usePortfolioId";

export function PreguntaPage() {
  const [portfolioId] = usePortfolioId();
  return (
    <>
      <PageTitle>Pregunta</PageTitle>
      {/* key: al cambiar de cartera se empieza una conversación limpia */}
      <VoiceAsk key={portfolioId} portfolioId={portfolioId} />
    </>
  );
}
