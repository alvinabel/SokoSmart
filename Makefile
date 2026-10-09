# AgroBasket — developer shortcuts
# Also see scripts/*.ps1 for Windows PowerShell equivalents.

.PHONY: dev seed logs down test frontend deploy-check icons clean

dev:
	docker compose up --build

seed:
	@echo "> running idempotent seeders (roles, admin, categories, demo data)"
	docker compose --profile tools run --rm seed

logs:
	docker compose logs -f

down:
	docker compose down

test:
	@echo "> backend tests"
	cd backend && python -m pytest -q
	@echo "> api tests"
	cd api && python -m pytest -q

frontend:
	cd frontend && npm install && npm run generate:icons && npm run dev

icons:
	cd frontend && npm run generate:icons

deploy-check:
	@echo "> python syntax check"
	python -m compileall -q shared backend api infra
	@echo "> frontend production build (PWA)"
	cd frontend && npm ci && npm run build

clean:
	docker compose down -v