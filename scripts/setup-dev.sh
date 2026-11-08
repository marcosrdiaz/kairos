#!/usr/bin/env bash
# Prepara las herramientas de desarrollo para Claude Code (una vez tras clonar).
# Idempotente: se puede ejecutar cuantas veces haga falta.
#
# Instala fuera del repo (no se commitea): el binario `playwright-cli`
# (@playwright/cli, para que el agente abra y pruebe la app) y su navegador.
# No es @playwright/test, que es el de los E2E de T3-02.
set -euo pipefail

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: hace falta Node.js (con npm). Instálalo y vuelve a ejecutar." >&2
  exit 1
fi

if command -v playwright-cli >/dev/null 2>&1; then
  echo "[ok] playwright-cli ya instalado ($(playwright-cli --version 2>/dev/null || echo 'versión desconocida'))"
else
  echo "[instalando] @playwright/cli (npm install -g @playwright/cli@latest)"
  npm install -g @playwright/cli@latest
  echo "[hecho] playwright-cli instalado"
fi

echo "[instalando] navegador de playwright-cli (si ya está, no hace nada)"
# `install` inicializa un workspace (crea .gitignore y .playwright/) en el
# directorio actual: se ejecuta desde uno temporal para no ensuciar el repo.
tmp="$(mktemp -d)"
(cd "$tmp" && playwright-cli install)
rm -rf "$tmp"
echo "[hecho] navegador listo"

echo
echo "Resumen: playwright-cli + navegador listos."
echo "Ahora abre Claude Code en el repo y acepta los plugins que te proponga (superpowers)."
