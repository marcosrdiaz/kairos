# KAIROS: comandos del equipo (ver CLAUDE.md). Requiere docker, uv y node.
# En Windows sin `uv` en el PATH: make UV="python -m uv" test

UV ?= uv
BACKEND := backend
FRONTEND := frontend
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

test-backend:
	cd $(BACKEND) && $(UV) run pytest

test-frontend:
ifneq ($(HAS_FRONTEND),)
	cd $(FRONTEND) && npx vitest run --passWithNoTests
else
	@echo "frontend: sin package.json todavía (T0-07), se omite"
endif

lint: lint-backend lint-frontend

lint-backend:
	cd $(BACKEND) && $(UV) run ruff check . && $(UV) run ruff format --check . && $(UV) run mypy app tests

lint-frontend:
ifneq ($(HAS_FRONTEND),)
	cd $(FRONTEND) && npx eslint . && npx tsc --noEmit
else
	@echo "frontend: sin package.json todavía (T0-07), se omite"
endif

# Objetivo de T0-03: genera los tipos TS desde el OpenAPI y copia los ejemplos a mocks/.
gen-api:
	@if [ -f scripts/gen_api.py ]; then cd $(BACKEND) && $(UV) run python ../scripts/gen_api.py; \
	else echo "gen-api: pendiente (T0-03)"; fi

EVENT ?=
replay:  ## make replay EVENT=bce-2025-06
	@test -n "$(EVENT)" || (echo "Uso: make replay EVENT=<event_id>" && exit 1)
	curl -fsS -X POST http://localhost:8000/api/v1/demo/replay/$(EVENT)

betas:  ## recalcula factor_beta desde data/prices
	docker compose run --rm --build seed python /scripts/compute_betas.py
