# AGENT.md

Refer to `docs/design.md` for architecture and `docs/features.json` for task tracking. Follow the conventions below.

## Project Overview
CaliperLens is an agentic natural-language-to-SQL engine for querying complex healthcare datasets. Users ask questions in plain English and receive answers backed by generated SQL, statistical analysis, and charts — all executed inside a sandboxed runtime. It is a portfolio/resume project targeting local-only deployment (frontend deployed standalone, backend + database run locally due to HIPAA constraints on real patient data).

## Development Philosophy
- TDD first: write the test, then the implementation. Never skip.
- Tests mirror the structure of the module they test
- No function ships without a test
- API routes are thin — logic lives in core/
- Explicit over clever — readable code beats smart code
- If it isn't runnable via `make`, it isn't done

## Tech Stack
- Frontend: React + Vite + TypeScript
- Backend: FastAPI (Python)
- Database: DuckDB (analytics) via dbt transforms, source data from MySQL
- Styling: TailwindCSS v4 (raw, no component library)
- State Management: Zustand
- Package Manager: uv (Python), npm (frontend)
- Build/Task Runner: **Make** — a root `Makefile` is mandatory and is the single entry point for setup, running, testing, linting, and building.
- Orchestration: Apache Airflow (local, docker-compose) for dbt pipeline scheduling
- LLM: Google Gemini 3.5 Flash (reasoning), `text-embedding-004` (embeddings)
- Vector Store: FAISS
- Agent Framework: LangGraph
- Sandbox: Docker containers (`--network none`, CPU/mem caps, timeout, read-only mounts)
- Observability: LangSmith (tracing), Prometheus + Grafana (metrics, local), structured logging with trace IDs
- Auth: JWT-based, rate-limited

## Key Commands

All commands MUST be runnable via `make <target>` from the project root. Calling tools directly (`uvicorn`, `npm run dev`, etc.) is for the Makefile's internal use only — humans and agents invoke `make`.

```bash
make setup                       # installs all dependencies (frontend + backend + dbt)
make dev                         # runs frontend + backend dev servers concurrently
make test                        # runs all tests (frontend + backend)
make style                       # formats + lints all code
make build                       # production build of frontend and backend
make clean                       # removes build artifacts, caches, __pycache__/node_modules etc.
make infra-up                    # starts docker-compose services (Airflow, Prometheus, Grafana, Sandbox)
make infra-down                  # stops docker-compose services
make dbt-run                     # runs dbt models (MySQL → DuckDB transforms)
make eval                        # runs the NL-to-SQL eval harness
```

## Directory Structure

```
caliperlens/
├── frontend/
│   ├── src/
│   │   ├── components/          # reusable UI components
│   │   ├── pages/               # route-level components
│   │   ├── hooks/               # custom React hooks
│   │   ├── utils/               # helper functions
│   │   ├── assets/              # images, fonts, static files
│   │   ├── store/               # Zustand state stores
│   │   ├── services/            # API call functions
│   │   └── main.tsx             # entry point
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/
│   ├── core/                    # business logic, domain layer (no HTTP knowledge)
│   ├── api/
│   │   └── v1/                  # versioned route handlers (thin layer)
│   ├── models/                  # SQLAlchemy DB models (if needed)
│   ├── schemas/                 # Pydantic schemas (request/response)
│   ├── utils/
│   │   ├── config.py            # Pydantic BaseSettings class, instantiated as `settings`
│   │   ├── logger.py            # custom logger, imported as `logger`
│   │   └── [other helpers]
│   ├── tests/
│   │   ├── test_api/            # mirrors api/v1/ structure
│   │   └── test_core/           # mirrors core/ structure
│   ├── main.py                  # FastAPI app entry point
│   └── pyproject.toml
│
├── dbt/                         # dbt project for data transforms
│   ├── models/
│   │   ├── staging/             # raw source models
│   │   ├── intermediate/        # joined/cleaned models
│   │   └── marts/               # analytics-ready models
│   ├── macros/
│   ├── tests/
│   └── dbt_project.yml
│
├── airflow/                     # Airflow DAGs and config
│   ├── dags/
│   │   └── caliperlens_pipeline.py
│   └── docker-compose.airflow.yaml
│
├── sandbox/                     # Sandbox infra
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── eval/                        # Eval harness
│   ├── questions.json           # 20-25 NL questions with expected SQL/result shape
│   └── runner.py
│
├── docker-compose.yaml          # full stack: backend + Airflow + Prometheus + Grafana
├── Makefile                     # single entry point
├── docs/
│   ├── problem.md               # original problem statement
│   ├── design.md                # design document
│   ├── features.json            # canonical feature tracker
│   └── [other design docs]
├── .env.example                 # committed, no secrets
├── .gitignore
├── README.md
└── AGENT.md
```

## Conventions

### Makefile (required)
- A root-level `Makefile` is **mandatory** and is the canonical control surface for the project. No setup, run, test, style, or build step should exist only as a "remember to run this manually" instruction — it belongs in the Makefile.
- Required targets: `setup`, `dev`, `test`, `style`, `build`, `clean`. `style` covers both formatting and linting in one command. Add more (`infra-up`, `infra-down`, `dbt-run`, `eval`) as the project needs them, but never remove the required set.
- Each target should be a thin wrapper that shells into `frontend/` or `backend/` and calls the underlying tool (`npm`, `pytest`, etc.) — the Makefile is an orchestration layer, not a place for business logic.
- `make setup` must be idempotent and safe to re-run — it should install/sync dependencies for both frontend and backend + dbt in one command.
- `make dev` should run frontend and backend concurrently (e.g. via backgrounded processes with a trap to kill both, or a tool like `overmind`/`concurrently`) so a single command boots the full stack.
- Every target should have a `## short description` comment on the same line so `make help` (if implemented) or a quick `grep` of the Makefile documents itself.

### Python (Backend)
- **Package manager: `uv`** — use `uv` for all dependency management (`uv add`, `uv run`, `uv sync`). Never use `pip` directly.
- Formatter: `black`, Linter: `ruff` (includes import sorting)
- Naming: snake_case for everything — files, variables, functions, DB columns
- API routes are thin: validate input → call core → return output
- core/ has zero knowledge of HTTP or FastAPI
- Env vars are accessed exclusively via the settings object (`from utils.config import settings`) — never use `os.environ` directly.

Config is a Pydantic `BaseSettings` class instantiated once in `backend/utils/config.py`:

```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Central management for settings and configurations."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    port: int = 8000
    database_url: str = "sqlite:///app.db"
    environment: str = "development"
    secret_key: str
    # Add project-specific fields here

settings = Settings()
```

pydantic-settings automatically reads `.env` and maps `UPPER_CASE` env vars to the corresponding lowercase fields. Each field acts as a typed accessor — `settings.port` returns an `int`, `settings.database_url` returns a `str`. Fields without defaults (like `secret_key`) raise a validation error at startup if the env var is missing. No `load_dotenv()` or `os.environ` needed.

All logging uses the custom logger (`from utils.logger import logger`) — never use `print` or the stdlib `logging` module directly.

### TypeScript (Frontend)
- **Strict mode enabled** in `tsconfig.json` — no implicit `any`, strict null checks
- Type component props with interfaces or type aliases — never leave props untyped
- camelCase for variables and functions
- PascalCase for components, types, and interfaces
- kebab-case for file names (`user-profile.tsx`, `use-auth.ts`)
- All backend API calls go through `services/`, never directly in components
- Formatter: Prettier, Linter: ESLint

### General
- Commits: conventional commits format (feat:, fix:, chore:, docs:, test:, refactor:)
- Env vars: never committed, always have a `.env.example` with keys but no values
- API versioned from day one under `/api/v1/`
- **All setup, dev, test, style, and build steps run through the root `Makefile`.**
- **README badges**: READMEs should include HTML shield badges (via [shields.io](https://shields.io)) for build status, version, license, and tech stack. Use raw HTML `<img>` tags, not Markdown image syntax, so badge layout and alignment can be controlled.

## Deployment Philosophy

CaliperLens runs entirely locally. The frontend is deployed standalone (Vercel free tier) displaying a notice that the backend is not publicly connected. The backend, DuckDB, Airflow, Prometheus, Grafana, and sandbox all run via `docker-compose` on the developer's machine. This is intentional — the database contains real patient data and must remain local per HIPAA constraints.

## Multi-Agent Workflow

When `docs/features.json` contains 3 or more independent features (different modules, no shared state), the Build agent parallelizes implementation using subagents.

### Flow

1. **Plan**: Identify independent features from `features.json`. Features touching the same files are dependent and batched sequentially.
2. **Build**: Spawn up to 3 builder subagents at a time via the Task tool. When one completes, spawn the next pending feature.
3. **E2E** (if applicable): When all builders complete, spawn the playwright-tester to run browser tests.
4. **Review**: Spawn the ponytail-reviewer to audit the combined diff for over-engineering. Ponytail only works on the full picture — review the combined diff, not per-feature.
5. **Verify**: Run `make test && make style`.

If fewer than 3 independent features exist, the Build agent implements them directly without subagents.

### Subagents

Subagents are defined in `~/.config/opencode/agents/` and available globally. All three use `model: opencode-go/deepseek-v4-flash`.

| Agent | File | Purpose | Permissions |
|-------|------|---------|-------------|
| builder | `builder.md` | TDD one feature, writes tests then implementation | edit: allow, bash: allow, task: { \*: deny, playwright-tester: allow } |
| playwright-tester | `playwright-tester.md` | E2E browser tests via playwright-cli | edit: deny, bash: allow |
| ponytail-reviewer | `ponytail-reviewer.md` | Bloat/over-engineering audit on combined diff | edit: deny, bash: allow |

### Edge cases

- **Dependent features** (same files): Sequenced within the same builder subagent.
- **Ponytail finds issues**: Main agent decides fix-now vs file-as-debt.
- **No E2E tests defined**: Playwright-tester step is skipped.
- **E2E failure during builder**: A builder can spawn playwright-tester mid-flight to validate its own feature.

## Agent Guidelines
- Always run `make style` before considering any code done
- Always use snake_case for Python files/variables/functions/DB columns; kebab-case for frontend files
- Never modify files in `/docs` unless explicitly asked
- Always run `make test` after making changes — if tests fail, fix before moving on
- Never use `os.environ` directly outside the config module — always go through the settings object
- Never use `print` or stdlib `logging` — always use the custom logger
- Never put API calls directly in React components — they belong in services/
- Always use `uv` for Python package management — never invoke `pip` directly
- Always check `/docs` for relevant design documents before starting any task — if a design doc exists for what you're building, it takes precedence
- If a design doc is missing but the task is significant enough to warrant one, flag it to the user before proceeding
- Always update `docs/features.json` after completing any task — mark features as done, update test status, add new features if they were introduced
- Any new setup/run/test/style/build step must be added as a Makefile target, not just documented in prose
- If the backend is purely HTTP plumbing with no Python-specific dependencies in `core/`, flag Go-portability during the design phase
- If something feels out of scope, flag it rather than silently doing it
- If >=3 independent features exist in docs/features.json, spawn builder subagents (max 3 concurrent) per the Multi-Agent Workflow

## Project-Specific Notes
- **LLM Provider**: Google Gemini 3.5 Flash for reasoning, `text-embedding-004` for embeddings. Single Google API key (`GEMINI_API_KEY` in `.env`). No AWS credentials.
- **Database**: Source data is MySQL (`fhs_coredb_local`) loaded from a SQL dump. Analytics layer is DuckDB populated via dbt transforms. The agent queries DuckDB, never raw MySQL directly.
- **dbt + Airflow**: `dbt-duckdb` adapter. Airflow runs locally via `docker-compose.airflow.yaml`. The main DAG triggers `dbt run` on a schedule. The dbt project lives in `dbt/`.
- **Sandbox**: All agent-generated code (Python for analysis/charts, SQL for queries) runs inside Docker containers with `--network none`, CPU/mem limits, and a strict timeout. The DuckDB database is mounted read-only into sandbox containers.
- **Deprecated assets to remove**: AWS credentials (`AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_SESSION_TOKEN`), ForesightHealth logos, `requirements.txt` (replaced by `uv`/`pyproject.toml`), `package-lock.json` in root (placeholder), bare `.jsx` files (migrated to `.tsx`).
- **Files that must not be touched**: The MySQL SQL dump data files. The `data/` directory is input-only, never modified by the pipeline.
- **Deployment**: Frontend only, deployed to Vercel (static). The frontend displays "Backend not publicly available due to HIPAA compliance." No backend-to-frontend connection in production; all backend/infra runs locally via `make infra-up`.
- **License**: Apache 2.0. The copyright line in LICENSE needs to be filled with the owner's name. If usage restrictions beyond Apache 2.0 are desired, the license should be changed to a proprietary or AGPL/CC BY-NC-ND license.
- **Legacy naming**: `Caliper-SQL-generator` in old git remote, README clone instructions, and package.json name. All references must be changed to `CaliperLens`.
