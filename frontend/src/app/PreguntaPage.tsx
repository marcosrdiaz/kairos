import { VoiceAsk } from "../voice/VoiceAsk";
import { usePortfolioId } from "./portfolio-picker/usePortfolioId";

export function PreguntaPage() {
  const [portfolioId] = usePortfolioId();
  // key: al cambiar de cartera se empieza una conversación limpia. El <h1> lo pone VoiceAsk
  // (comparte fila con el interruptor «Leer en voz alta»).
  return <VoiceAsk key={portfolioId} portfolioId={portfolioId} />;
}
