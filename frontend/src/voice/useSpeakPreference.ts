import { useCallback, useState } from "react";

const KEY = "kairos.speak_answers";

function readStored(): boolean {
  try {
    return localStorage.getItem(KEY) !== "false";
  } catch {
    return true;
  }
}

/** Si las respuestas se leen en voz alta. Activa por defecto (RF-14) y guardada en `localStorage`. */
export function useSpeakPreference(): [boolean, (on: boolean) => void] {
  const [on, setOn] = useState(readStored);
  const set = useCallback((value: boolean) => {
    setOn(value);
    try {
      localStorage.setItem(KEY, String(value));
    } catch {
      // sin almacenamiento: vale para esta visita
    }
  }, []);
  return [on, set];
}
