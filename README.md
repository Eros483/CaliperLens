<div align="center">

# CaliperLens
</center>

<center>
<p>
    <img src="https://img.shields.io/badge/license-BUSL--1.1-blue" alt="License"/>
    <img src="https://img.shields.io/badge/version-2.0.0-green" alt="Version"/>
    <img src="https://img.shields.io/badge/python-3.12+-blue" alt="Python"/>
    <img src="https://img.shields.io/badge/typescript-5.4+-3178c6" alt="TypeScript"/>
    <img src="https://img.shields.io/badge/react-18.3-61dafb" alt="React"/>
    <img src="https://img.shields.io/badge/llm-gemini_3.5_flash-4285f4" alt="Gemini"/>
    <img src="https://img.shields.io/badge/CI-passing-brightgreen" alt="CI"/>
</p>
</center>

An agentic natural-language-to-SQL engine for querying complex healthcare datasets autonomously. Uses a multi-agent sandboxed workflow to reason through database schemas and generate complex queries.

<div align="left">

## Directory Overview

```
backend/
├── api/v1/                # Versioned route handlers
│   └── router.py
├── src/
│   ├── agent.py           # Main LangGraph Agent definition
│   ├── custom_tools.py    # Tools exposed to the LLM
│   ├── graph_manager.py   # NetworkX Logic for join path discovery
│   ├── prompt_module.py   # System Prompts for different agent states
│   └── rag_manager.py     # FAISS Vector Store for schema search
├── schemas/
│   └── chat.py            # API Request/Response models
├── utils/
│   ├── config.py          # Pydantic settings
│   ├── logger.py          # Custom logging configuration
│   └── custom_exception.py
├── tests/
│   ├── test_api/          # API endpoint tests
│   └── test_core/         # Core logic tests
└── main.py                # FastAPI Entry point

frontend/
├── src/
│   ├── components/        # React components
│   ├── store/             # Zustand state management
│   ├── services/          # API call functions
│   └── __tests__/         # Vitest component tests
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json

docs/
├── problem.md             # Original problem statement
├── design.md              # Architecture & design document
└── features.json          # Feature tracker
```

## Getting Started

```bash
git clone https://github.com/Eros483/CaliperLens.git
cd CaliperLens
cp .env.example .env
```

Set your `.env` with the required keys (see `.env.example`).

```bash
make setup    # Install all dependencies
make dev      # Start frontend + backend
make test     # Run all tests
make style    # Format + lint
```

## Tools

| Tool | Type | Responsibility |
|---|---|---|
| sql_db_query | Execution | Execute SQL against the database |
| sql_db_find_relevant_tables | Research (RAG) | Semantic vector search for table discovery |
| sql_db_find_table_connections | Reasoning (Graph) | Dijkstra-based join pathfinding |
| sql_db_schema | Research | Return CREATE TABLE DDL and column metadata |
| sql_db_query_distinct_values | Research | Inspect unique values in a column |
| sql_db_sample_rows | Research | Preview 3 rows from a table |
| sql_db_get_foreign_keys | Reasoning | List explicitly defined foreign keys |
| sql_db_get_column_info | Research | Detailed column type/comment inspection |

## Guardrails

| Guardrail | Description |
|---|---|
| Binary UUID Protection | Wraps BINARY(16) columns with HEX() / BIN_TO_UUID() |
| Hallucination Check | Graph validates join paths before SQL generation |
| Syntax Correction | Auto-adds LIMIT clauses, converts raw SQL to tool calls |
| Data Verification | Detects binary garbage / empty results, triggers retry |
| Org Scoping | Enforces organization-based row-level security |

## License

BUSL-1.1 — free for personal, educational, and portfolio use. Production or commercial deployment requires a separate license. See [LICENSE](LICENSE).
