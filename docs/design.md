# CaliperLens — Design Document

## 1. Overview

CaliperLens is a local-first, agentic natural-language-to-SQL engine for querying complex healthcare datasets. Users type plain-English questions ("top 5 Medicaid patients with highest SDOH score, chart their intervention costs") and the system autonomously plans multi-step workflows, generates and executes SQL, performs statistical analysis, and produces charts — all inside sandboxed Docker containers.

The system runs entirely locally. Only the frontend is deployed (Vercel), displaying a notice that the backend is not publicly connected. Real patient data stays on the developer's machine.

## 2. Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────────────┐
│   Frontend   │     │               Local Docker Host                    │
│  (Vercel)    │     │                                                  │
│  React+TS    │     │  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  Tailwind v4 │     │  │ FastAPI   │  │ Airflow  │  │  Prometheus   │  │
│  Zustand     │     │  │ Backend   │  │ (dbt)    │  │  + Grafana    │  │
│              │     │  │           │  │          │  │               │  │
│  "not public │     │  │ /api/v1/  │  │ DAG ->   │  │  metrics +    │  │
│   yet" banner│     │  │  chat     │  │ dbt run  │  │  dashboards   │  │
└──────────────┘     │  │  health   │  └────┬─────┘  └───────────────┘  │
                     │  └─────┬─────┘       │                            │
                     │        │             │                            │
                     │  ┌─────▼─────┐  ┌───▼────────┐  ┌─────────────┐  │
                     │  │ LangGraph │  │    dbt     │  │  Sandbox    │  │
                     │  │  Agent    │  │  MySQL ->  │  │  Docker     │  │
                     │  │           │  │  DuckDB    │◄─┤  --network  │  │
                     │  │ Gemini    │  │  models    │  │   none      │  │
                     │  │ 3.5 Flash │  └────────────┘  │  ro mounts  │  │
                     │  └─────┬─────┘                  └─────────────┘  │
                     │        │                                         │
                     │  ┌─────▼─────┐  ┌────────────┐                  │
                     │  │  FAISS    │  │  DuckDB    │                  │
                     │  │  Vector   │  │  Analytics │                  │
                     │  │  Store    │  │  (read)    │                  │
                     │  └───────────┘  └────────────┘                  │
                     └──────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: Raw MySQL dump -> dbt staging models -> intermediate joins -> analytics marts (DuckDB)
2. **Query**: User question -> FastAPI -> LangGraph agent -> Gemini 3.5 Flash generates SQL -> executes against DuckDB
3. **Analysis**: Agent optionally spawns Python analysis code -> sandbox Docker container -> results returned
4. **Charts**: Agent optionally spawns matplotlib/plotly code -> sandbox -> chart artifact saved -> returned to frontend

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| DuckDB over raw MySQL | OLAP-optimized, in-process, no server. dbt transforms create analytics-ready models. Agent queries denormalized marts, not raw transactional tables. |
| dbt-duckdb over Snowflake | Runs locally, free, no cloud account. Same dbt experience (models, tests, docs, Jinja). |
| Airflow (local) | Learning value for data engineering. Single-node, docker-compose. Schedules dbt runs. |
| Sandbox (Docker) | Agent generates Python/SQL code. Must run isolated: --network none, CPU/mem caps, read-only DB mount, strict timeout. |
| Gemini 3.5 Flash | Free tier, strong reasoning, same provider for embeddings (text-embedding-004). Single key. AWS removed. |
| Zustand over useState | Chat state is simple but multi-step workflows (planner, multi-turn) add complexity. Zustand is 1KB gzipped, minimal overhead. |
| Tailwind v4 (raw) | No component library. The existing UI has a specific pill-button gradient aesthetic that raw Tailwind preserves without fighting shadcn/shadcn defaults. |
| JWT auth | API-key insufficient for session-scoped access. JWT with refresh tokens, rate-limited per user. |
| Local-only backend | HIPAA constraints. Real patient data never leaves the machine. Frontend on Vercel is a static shell. |

## 3. Phase Breakdown

### Phase 0: Foundation (Structural Overhaul)

Bring the repository into AGENTS.md compliance without changing any feature behavior. This phase creates the scaffolding that all subsequent work depends on.

**Makefile**: All 6 required targets (setup, dev, test, style, build, clean). Plus project-specific: infra-up, infra-down, dbt-run, eval.

**TypeScript migration**: Convert all .jsx to .tsx with strict tsconfig.json. Define typed props interfaces for all components. Convert api.js to api.ts with typed request/response shapes.

**TailwindCSS v4**: Replace plain CSS files with Tailwind utility classes. Delete *.css files. Preserve the existing pill-button gradient aesthetic.

**Zustand**: Centralize chat state (messages, isLoading, sessionId, connectionStatus) into a Zustand store. Components become thin presentational layers.

**Package manager**: uv for Python (pyproject.toml replaces requirements.txt). Keep npm for frontend.

**Formatters/linters**: black + ruff (backend), Prettier + ESLint (frontend).

**Tests**: pytest for backend (mirroring core/, api/v1/ structure). Vitest + React Testing Library for frontend. Test coverage for all existing functionality.

**Docs**: Create docs/problem.md, docs/design.md (this file), docs/features.json.

**Config consolidation**: Move core/config.py -> utils/config.py. Remove manual load_dotenv(), use pure BaseSettings with model_config. Rename Langsmith_API_KEY -> langsmith_api_key.

### Phase 1: Rebrand

Every reference to old names becomes "CaliperLens".

- Rename GitHub repo from Caliper-SQL-generator to CaliperLens. Update local remote.
- README: update clone URLs, project title, description.
- package.json: "name": "caliperlens"
- index.html: <title>CaliperLens -- AI-Powered Healthcare Analytics</title>
- main.py: title="CaliperLens API", version 2.0.0
- Navbar/ChatInterface: brand text "CaliperLens", remove standalone "Caliper" references
- LICENSE: fill copyright line. Evaluate whether Apache 2.0 is the right license for desired usage restrictions.
- Remove foresighthealth_logo.jpeg, foresighthealth_logo-removebg-preview.png
- Remove root package-lock.json (empty placeholder)

### Phase 2: LLM Migration (AWS -> Gemini 3.5 Flash)

- Delete AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN from settings. Delete boto3.
- Use langchain-google-genai for both ChatGoogleGenerativeAI and GoogleGenerativeAIEmbeddings. Single GEMINI_API_KEY.
- Clean config: utils/config.py, pure BaseSettings (no os.getenv() in defaults, no manual load_dotenv()). All credentials via settings object.
- Remove os.environ blocks in agent.py. Inject settings via dependency.
- Model: gemini-3.5-flash for reasoning, text-embedding-004 for embeddings.
- Keep fallback provider logic (generic pattern, not AWS-specific).
- Update .env.example: remove AWS keys, keep GEMINI_API_KEY.

### Phase 3: Data Pipeline (dbt + DuckDB + Airflow)

The data pipeline transforms raw MySQL tables into analytics-ready DuckDB marts.

**dbt project structure:**
```
dbt/
  models/
    staging/
      stg_patient.sql           -- raw MySQL views cast to DuckDB types
      stg_lob.sql
      stg_patient_score.sql
      ...
    intermediate/
      int_patient_scores.sql    -- joined patient + scores + insurance
      int_patient_conditions.sql -- patient + diagnoses
      ...
    marts/
      dim_patients.sql          -- patient dimension (SCD type 1)
      dim_conditions.sql        -- condition/diagnosis dimension
      fct_patient_metrics.sql   -- fact table: one row per patient-metric
      fct_interventions.sql     -- intervention transactions
```

**Airflow DAG:** A single DAG (caliperlens_pipeline) that runs dbt run on a schedule (daily or on-demand via make dbt-run). Uses the dbt-duckdb adapter. Airflow runs locally via docker-compose.airflow.yaml.

**Agent impact:** The agent adopts a tiered query strategy that maximizes simplicity while retaining the graph-based pathfinder as a safety net for edge cases:

**Tier 1 — Single mart (80% of queries):** The agent queries a single analytics mart directly. `fct_patient_metrics` already contains patient demographics, insurance, organization, and all risk scores in one row. Queries like "top 5 Medicaid patients by SDOH score" require zero joins — just WHERE, ORDER BY, LIMIT.

**Tier 2 — Two-mart join on shared key (15%):** All marts share `patient_id`. A query like "intervention costs for high-SDOH patients" joins `fct_patient_metrics` and `fct_interventions` on `patient_id`. No pathfinding needed — the same column name exists on both sides. A simple foreign key dictionary replaces Dijkstra for this tier.

**Tier 3 — Edge queries via staging fallback (5%):** A genuinely novel query that crosses tables not covered by the marts (e.g., filtering by a column that was deliberately excluded from the mart). The agent falls back to querying dbt staging models (1:1 mirrors of raw MySQL tables, materialized in DuckDB). The SchemaGraph (NetworkX) pathfinder still operates against these staging tables to discover join paths. The graph is preserved, not deleted — it is downgraded from the default path to a safety net.

The SchemaRAG context library is rebuilt against dbt model documentation (auto-generated via `dbt docs generate` + manual medical terminology annotations). Both the mart descriptions and staging table descriptions are indexed, so the agent can discover whether a question is Tier 1/2 or needs Tier 3.

**MySQL retention:** The MySQL source database is still loaded (raw dump). It serves as the immutable source of truth. All dbt transforms are idempotent and re-runnable.

### Phase 4: Sandbox

All agent-generated code runs inside isolated Docker containers.

**Container spec:**
- Base image: python:3.12-slim
- Network: --network none (no internet access)
- Resources: --cpus=1, --memory=256m, --pids-limit=50
- Timeout: 30 seconds per execution
- Mounts: DuckDB database file mounted read-only, writable /tmp for output artifacts

**Execution flow:**
1. Agent generates Python code string (analysis or chart generation)
2. Backend writes code to a temp file
3. Docker run with code mounted, DB mounted read-only
4. Captures stdout, stderr, exit code, and any output files (charts as PNG/SVG)
5. Returns results to the agent for final answer synthesis

**Security properties:**
- No network access prevents exfiltration
- Read-only DB mount prevents data modification
- CPU/memory caps prevent resource exhaustion
- Timeout prevents runaway processes
- pids-limit prevents fork bombs

### Phase 5: Eval Harness

Objective measurement of agent quality. Required before any agent behavior changes.

**questions.json structure:**
```json
[
  {
    "id": "eval_001",
    "category": "simple_select",
    "question": "How many patients are in the database?",
    "expected_sql_contains": ["SELECT COUNT", "FROM"],
    "expected_result_shape": {"type": "scalar", "min": 1},
    "max_joins": 1,
    "tables_required": ["dim_patients"]
  }
]
```

**Categories:** simple_select, filtered_select, join, aggregation, multi_step, edge_case (binary UUID handling, LIMIT enforcement, org_id filtering).

**Runner (runner.py):** Iterates questions, sends each to the agent endpoint, validates SQL structure (contains expected clauses), validates result shape (type, range, row count), reports pass/fail with detailed reason. Generates pass-rate and auto-repair-rate (questions that passed on retry after first failure).

**Integration:** make eval runs the harness. CI runs it on every push via GitHub Actions.

### Phase 6: Planner + Multi-turn Memory + RAG Preprocessing

Upgrades the agent from single-shot query generation to multi-step workflow execution, and moves RAG from a reactive LLM tool to a deterministic preprocessing step.

**RAG as preprocessing (graph simplification):**

Currently the RAG is a tool the LLM must decide to call mid-graph — costing LLM roundtrips for "should I search for tables?", variable quality (the LLM chooses search terms), and an 8-node graph. This changes to a preprocessing step that runs once before the graph:

```
User query
    → RAG search (deterministic, always runs): top-K relevant tables + schemas
    → enriched prompt injected into initial state
    → graph: generate_query → check_query → run_tools → validate_answer
              ↑__________________________________________↓  (retry loop)
                          → generate_final_answer → END
```

Benefits: 3 nodes eliminated (list_tables_node, call_get_schema_node, get_schema_node), zero LLM roundtrips spent on table discovery, the LLM gets schema context upfront like a human analyst, and RAG table discovery tools remain available as Tier-3 fallback tools but no longer gate the primary path.

The enriched prompt includes: the user's original question, top-K relevant tables with column schemas, and the Tier-2 FK dictionary (patient_id shared across marts). Example:

```
User Question: show top 5 medicaid patients with highest SDOH score

Relevant Tables:
  fct_patient_metrics (patient_id, first_name, last_name, insurance_name,
    sdoh_score, comprehensive_score, hcc_score, org_id, org_name)
  dim_conditions (patient_id, condition_name, condition_category)

Generate SQL to answer the question. Use LIMIT 10. Use HEX() for binary IDs.
Filter by Organization ID if provided.
```

**Planner node:** A new LangGraph node inserted at the start of the graph. Receives the enriched prompt, generates an ordered execution plan:
```
Plan: [
  { step: 1, action: "query", description: "Find top 5 Medicaid patients by SDOH score" },
  { step: 2, action: "analyze", description: "Compute mean/median/stdev of scores" },
  { step: 3, action: "chart", description: "Bar chart of scores per patient" }
]
```

**Task-state tracking:** A plan_state dict tracks per-step status (pending, running, done, failed). The planner outputs a structured JSON plan object validated against a Pydantic schema.

**Re-planning on failure:** If a step fails (invalid SQL, sandbox error, validation failure), the graph routes back to the planner with the error context. The planner generates a revised plan (different query approach, simplified analysis, etc.) rather than blind-retrying the same approach.

**Multi-turn memory:** The MemorySaver already exists in the codebase. This phase upgrades it:
- Conversation history preserved across messages in a session
- The agent can reference previous queries ("compare those results to the previous chart")
- Session state includes the plan history so follow-up questions like "now break that down by insurance type" reuse the prior plan context
- Session IDs stored in localStorage on the frontend; backend routes by session_id

### Phase 7: Auth + Security

- **JWT auth:** POST /api/v1/auth/login returns access + refresh tokens. All /api/v1/* endpoints require Authorization: Bearer header. Token validation in FastAPI middleware/dependency.
- **Rate limiting:** Per-user rate limit on /api/v1/chat (e.g., 20 requests/minute). Implemented via slowapi or a simple Redis-backed counter.
- **DB credentials:** DuckDB database mounted read-only into sandbox. MySQL connection uses a dedicated read-only user (SELECT only, no INSERT/UPDATE/DELETE/DROP).
- **Secrets audit:** No credentials in logs, traces, or error messages. LangSmith traces sanitized of API keys. .env.example reflects only GEMINI_API_KEY, DB_*, SECRET_KEY, LANGSMITH_API_KEY.
- **org_id scoping:** The hardcoded org_id=16 in main.py becomes a configurable parameter validated against the JWT claims (per-user org access).

### Phase 8: Infra + CI

- **Dockerfile:** Multi-stage build for the FastAPI backend. Production image runs uvicorn with gunicorn workers.
- **docker-compose.yaml:** Orchestrates: backend, Airflow (webserver + scheduler + postgres), Prometheus, Grafana, sandbox image pre-built. Single make infra-up boots everything.
- **GitHub Actions:** .github/workflows/ci.yaml: checkout, make setup, make style, make test, make eval. Runs on push to main and PRs.
- **Health check:** GET /api/v1/health returns status of all downstream dependencies (DuckDB connectivity, Gemini API reachability, sandbox docker availability).

### Phase 9: Observability

- **LangSmith:** Already partially configured (LANGSMITH_API_KEY in settings). Enable full tracing: node-by-node graph execution, tool calls with inputs/outputs, retry loops. Set LANGCHAIN_TRACING_V2=true.
- **Prometheus metrics:** FastAPI endpoint /metrics exposes: request count, request latency histogram, per-LangGraph-node execution time, sandbox execution time, error rate counter. Prometheus scrapes locally.
- **Grafana dashboard:** Pre-built dashboard JSON committed to repo. Panels: p95/p99 chat latency, plan success rate, sandbox execution time distribution, error rate by type (SQL syntax, timeout, validation failure), cost per query (Gemini token usage).
- **Structured logging:** python-json-logger with trace IDs. Every log line includes trace_id, session_id, and node_name. Enables grep-able reconstruction of any single query's full execution path.

### Phase 10: Analysis + Charts

Built on phase 4 (sandbox) and phase 6 (planner). The agent can now perform statistical analysis and generate visualizations.

**Analysis routines:** The planner can schedule an "analyze" step. The agent generates Python code that:
- Loads query results (passed as JSON to the sandbox)
- Computes descriptive statistics (mean, median, stddev, quartiles)
- Performs trend detection (linear regression on time-series data)
- Returns structured analysis as JSON

**Chart routines:** The planner can schedule a "chart" step. The agent generates Python code that:
- Uses matplotlib (no plotly, avoids heavy deps — matplotlib is already in the sandbox image)
- Produces PNG chart artifacts written to /tmp
- Chart files are returned to the frontend as base64-encoded images
- Supported chart types: bar, line, scatter, histogram, pie

**Output contracts:** Both analysis and chart routines have Pydantic-schema-validated return types. Analysis returns a typed dict with stats fields. Chart returns {chart_type, chart_data_base64, title}.

## 4. Dependencies & Sequencing

```
Phase 0 (Foundation)
   |
Phase 1 (Rebrand) -- parallelizable with Phase 0
   |
Phase 2 (LLM Migration)
   |
Phase 3 (Data Pipeline) -- can partially overlap with Phase 2
   |
Phase 4 (Sandbox)
   |
Phase 5 (Eval Harness)
   |
Phase 6 (Planner + Multi-turn) -- needs eval baseline first
   |
Phase 7 (Auth + Security)
   |
Phase 8 (Infra + CI)
   |
Phase 9 (Observability)
   |
Phase 10 (Analysis + Charts) -- needs sandbox + planner
```

Phases 0 and 1 can run in parallel (independent file sets). All others are sequential.

## 5. Files Never Touched

- data/ directory (MySQL dump files — input only)
- The MySQL source database itself (reads via dbt, never writes)

## 6. Deprecated Assets (to remove during Foundation/Rebrand)

- AWS credentials from .env and config
- foresighthealth_logo.jpeg and foresighthealth_logo-removebg-preview.png
- Root package-lock.json (empty placeholder)
- requirements.txt (replaced by pyproject.toml + uv)
- All *.jsx files (migrated to *.tsx)
- All *.css files (replaced by Tailwind)
- core/config.py (moved to utils/config.py)
