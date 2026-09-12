SHELL := /bin/zsh

.PHONY: setup check models backend frontend dev test clean-cache

setup:
	./scripts/setup_mac.sh

check:
	./scripts/check_system.sh

models:
	./scripts/check_models.sh --pull

backend:
	./scripts/start_backend.sh

frontend:
	./scripts/start_frontend.sh

dev:
	./scripts/run_all.sh

test:
	.venv/bin/python -m pytest backend/tests
	cd frontend && npm run lint && npm run build

clean-cache:
	find backend frontend -type d \( -name __pycache__ -o -name .pytest_cache -o -name .vite \) -prune -exec rm -r {} +

