import { createContext, useContext } from "react";

export interface ChatDockState {
  open: boolean;
  setOpen: (open: boolean) => void;
}

export const ChatDockContext = createContext<ChatDockState>({ open: false, setOpen: () => undefined });

/** Abre o cierra el asistente desde cualquier pantalla dentro de AppShell. */
export function useChatDock(): ChatDockState {
  return useContext(ChatDockContext);
}
