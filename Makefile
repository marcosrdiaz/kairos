# KAIROS: comandos del equipo (ver CLAUDE.md). Requiere docker, uv y node.
# En Windows sin `uv` en el PATH: make UV="python -m uv" test

UV ?= uv
BACKEND := backend
FRONTEND := frontend
SCRIPTS := scripts
HAS_FRONTEND := $(wildcard $(FRONTEND)/package.json)

.PHONY: up down seed test test-backend test-frontend lint lint-backend lint-frontend \
        gen-api replay betas

up:  ## db + seed + backend + frontend
	docker compose up --build

down:
	docker compose down

seed:  ## migraciones + carga de data/seed (Laura y Javier)
	docker compose run --rm --build seed

test: test-backend test-frontend

# En paralelo con pytest-xdist (un proceso por núcleo). Para un solo fichero, `uv run pytest <fichero>`
# sin -n arranca antes.
test-backend:
	cd $(BACKEND) && $(UV) run pytest -n auto

test-frontend:
ifneq ($(HAS_FRONTEND),)
	cd $(FRONTEND) && npx vitest run --passWithNoTests
else
	@echo "frontend: sin package.json todavía (T0-07), se omite"
endif

lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND) && $(UV) run ruff check . ../$(SCRIPTS) && $(UV) run ruff format --check . ../$(SCRIPTS) && $(UV) run mypy app tests

lint-frontend:
ifneq ($(HAS_FRONTEND),)
	cd $(FRONTEND) && npx eslint . && npx tsc --noEmit
else
	@echo "frontend: sin package.json todavía (T0-07), se omite"
endif

# Tipos TS desde el OpenAPI (frontend/src/api/generated/) y ejemplos a frontend/src/api/mocks/.
# Ejecútalo tras cambiar un esquema o un ejemplo y sube lo generado en el mismo PR.
# Usa el openapi-typescript instalado en frontend/ (devDependency con versión exacta; hace falta
# `npm ci` allí) y no descarga nada, así que no depende de la red.
# Sin Node: make gen-api GEN_API_ARGS=--skip-ts (solo OpenAPI y mocks).
GEN_API_ARGS ?=
gen-api:
	cd $(BACKEND) && $(UV) run python ../scripts/gen_api.py $(GEN_API_ARGS)

EVENT ?=
replay:  ## make replay EVENT=bce-2025-06
	@test -n "$(EVENT)" || (echo "Uso: make replay EVENT=<event_id>" && exit 1)
	curl -fsS -X POST http://localhost:8000/api/v1/demo/replay/$(EVENT)

betas:  ## recalcula factor_beta desde data/prices
	docker compose run --rm --build seed python /scripts/compute_betas.py
