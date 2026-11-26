.PHONY: instalar pruebas lint formato dev-api dev-web
instalar:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install
pruebas:
	cd backend && SECRET_KEY=local-secret-0123456789 .venv/bin/pytest
lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/bandit -q -r app -c pyproject.toml
	cd frontend && npm run lint
formato:
	cd backend && .venv/bin/ruff format . && .venv/bin/ruff check --fix .
dev-api:
	cd backend && SECRET_KEY=local-secret-0123456789 ADMIN_PASSWORD=Admin12345x DEMO_DATA=1 DB_PATH=/tmp/dev.db .venv/bin/uvicorn app.main:app --reload
dev-web:
	cd frontend && npm run dev
