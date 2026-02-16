# M1 Project Mauro Moyano - Makefile
# Requiere: uv (https://docs.astral.sh/uv/)

UV ?= uv
PYTHON ?= python3

.PHONY: check-uv install run test lint format clean

check-uv:
	@command -v $(UV) >/dev/null 2>&1 || (echo "uv no está instalado. Instala uv y vuelve a ejecutar: https://docs.astral.sh/uv/"; exit 1)

install: check-uv
	$(UV) sync

run: check-uv
	$(UV) run python -m src.run_query "How do I reset my password?"

run-query: check-uv
	@if [ -z "$(QUESTION)" ]; then echo "Usage: make run-query QUESTION=\"Your question\""; exit 1; fi
	$(UV) run python -m src.run_query "$(QUESTION)"

test: check-uv
	$(UV) run pytest -v

lint: check-uv
	$(UV) run ruff check .

format: check-uv
	$(UV) run ruff format .

check:
	$(PYTHON) -m compileall .

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
