# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI backend (`app/routers`, `app/models`, `app/services`, `app/database`). Tests live in `backend/tests/` and `backend/test_*.py`.
- `frontend/`: React (CRA) app (`src/` components, pages, `__tests__/`).
- `infrastructure/`: Docker, Kubernetes, Terraform, scripts (`infrastructure/scripts/*.sh`).
- `docs/`: Setup, deployment, and product documentation.
- Root helpers: `run_tests.py` (runs backend + frontend tests), `package.json` (workspace scripts).

## Build, Test, and Development Commands
- Backend setup:
  - `cd backend && python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - Run API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend dev:
  - `cd frontend && npm install && npm start` (served on port 3000)
- Workspace build: from repo root `npm run build` (installs and builds `frontend/`).
- Tests:
  - All: `python run_tests.py`
  - Backend: `cd backend && pytest`
  - Frontend: `cd frontend && npm test` or `npm run test:coverage`

## Coding Style & Naming Conventions
- Python (backend): 4-space indent, type hints. Tools: Black (88 cols), isort (black profile), Flake8, MyPy (strict). Package names `snake_case`, classes `CamelCase`, modules `snake_case.py`.
- JavaScript/React (frontend): 2-space indent, components `PascalCase` (e.g., `ProjectBoard.js`), hooks `camelCase`. ESLint via `react-scripts` defaults.

## Testing Guidelines
- Backend: `pytest` with coverage (configured in `pyproject.toml`). Place tests under `backend/tests/` or as `backend/test_*.py`.
- Frontend: Jest + React Testing Library. Tests under `src/**/__tests__` and `*.test.js(x)`.
- Coverage: frontend enforces ~75% global thresholds (`package.json`). Aim similar for backend.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits — examples: `feat(api): add chat history`, `fix(frontend): resolve sidebar overflow`, `chore(ci): tweak coverage report`.
- PRs: include clear description, linked issues, test plan, and screenshots for UI changes. Ensure CI passes (`run_tests.py`), add/adjust tests, and update docs when behavior changes.

## Security & Configuration Tips
- Do not commit secrets. Use env vars: `OPENAI_API_KEY`, `JWT_SECRET`, `DATABASE_URL`, `CORS_ORIGINS` (see `backend/app/config/settings.py`).
- Use `infrastructure/scripts/setup-secrets.sh` and deployment guides under `infrastructure/` for safe config.
