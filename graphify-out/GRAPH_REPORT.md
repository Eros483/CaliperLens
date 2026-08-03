# Graph Report - .  (2026-08-03)

## Corpus Check
- 52 files · ~153,643 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 293 nodes · 398 edges · 30 communities (28 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Frontend Linting
- Backend Agent Core
- Agent SQL Generation
- Frontend UI Components
- Frontend TypeScript Config
- Architecture Design Docs
- Backend API Routes
- Frontend Dependencies
- DevOps & CI/CD
- Backend Config Tests
- Backend Exception Tests
- Brand & Visual Identity
- API Integration Tests
- Multi-Agent Workflow
- OpenCode Configuration
- Graphify Plugin
- Package Config

## God Nodes (most connected - your core abstractions)
1. `SQLAgentGenerator` - 21 edges
2. `compilerOptions` - 19 edges
3. `CustomException` - 14 edges
4. `SchemaRAG` - 11 edges
5. `LangGraph Agent` - 11 edges
6. `SchemaGraph` - 10 edges
7. `Settings` - 10 edges
8. `CaliperLens` - 10 edges
9. `scripts` - 9 edges
10. `ChatRequest` - 8 edges

## Surprising Connections (you probably didn't know these)
- `SQL Guardrails` --semantically_similar_to--> `Sandbox Security Properties`  [INFERRED] [semantically similar]
  README.md → docs/design.md
- `LangSmith Tracing` --conceptually_related_to--> `LangGraph Agent`  [EXTRACTED]
  docs/design.md → README.md
- `Root Makefile` --rationale_for--> `CaliperLens`  [EXTRACTED]
  AGENTS.md → README.md
- `TDD Development Philosophy` --rationale_for--> `CaliperLens`  [EXTRACTED]
  AGENTS.md → README.md
- `NL-to-SQL Eval Harness` --conceptually_related_to--> `CaliperLens`  [EXTRACTED]
  docs/design.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Agent Runtime Stack** — readme_langgraph_agent, readme_gemini_35_flash, readme_faiss_vector_store, readme_networkx_schemagraph, readme_duckdb_analytics, docs_design_sandbox [INFERRED 0.85]
- **Data Pipeline: MySQL to Analytics Marts** — docs_design_dbt_pipeline, docs_design_dbt_duckdb_adapter, docs_design_airflow, readme_duckdb_analytics, docs_design_tiered_query_strategy [INFERRED 0.95]
- **Multi-Agent Build Subagents** — agents_md_multi_agent_workflow, agents_md_builder_subagent, agents_md_playwright_tester, agents_md_ponytail_reviewer [EXTRACTED 1.00]

## Communities (30 total, 2 thin omitted)

### Community 0 - "Frontend Linting"
Cohesion: 0.05
Nodes (37): eslint, eslint-plugin-react-hooks, eslint-plugin-react-refresh, devDependencies, eslint, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+29 more)

### Community 1 - "Backend Agent Core"
Cohesion: 0.10
Nodes (19): lifespan(), get_db_tools(), SQLDatabase, Returns a list of custom tools bound to the specific database instance.…, SQLDatabase, Manages a graph representation of the database schema to facilitate pathfinding…, Initialize the SchemaGraph with a database connection and build the graph.…, Constructs the internal NetworkX graph. This method performs two main actions:… (+11 more)

### Community 2 - "Agent SQL Generation"
Cohesion: 0.11
Nodes (12): SQLDatabase, LangGraph-based SQL Agent using Google Gemini 3.5 Flash., SQLAgentGenerator, answer_validation_prompt_module(), generate_query_prompt_module(), query_verification_prompt_module(), Generates the system prompt for the query verification phase (Code Reviewer).…, Generates the system prompt for the table selection/discovery phase. Focuses on… (+4 more)

### Community 3 - "Frontend UI Components"
Cohesion: 0.15
Nodes (16): App(), ChatInput(), ChatInputProps, ChatInterface(), ChatMessage(), ChatMessageProps, checkHealth(), sendMessage() (+8 more)

### Community 4 - "Frontend TypeScript Config"
Cohesion: 0.08
Nodes (24): compilerOptions, allowImportingTsExtensions, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib, module (+16 more)

### Community 5 - "Architecture Design Docs"
Cohesion: 0.11
Nodes (23): Apache Airflow Orchestration, dbt-duckdb Adapter, dbt Data Pipeline, DuckDB over MySQL Decision, Multi-turn Memory with LangGraph MemorySaver, Phase 2: AWS to Gemini Migration, LangGraph Planner Node, RAG as Deterministic Preprocessing (+15 more)

### Community 6 - "Backend API Routes"
Cohesion: 0.19
Nodes (14): chat_endpoint(), get_agent(), health_check(), ChatRequest, ChatResponse, HealthResponse, Schema for the AI response., Schema for health check response. (+6 more)

### Community 7 - "Frontend Dependencies"
Cohesion: 0.10
Nodes (20): dependencies, react, react-dom, zustand, name, private, scripts, build (+12 more)

### Community 8 - "DevOps & CI/CD"
Cohesion: 0.13
Nodes (18): Root Makefile, TDD Development Philosophy, NL-to-SQL Eval Harness, GitHub Actions CI Pipeline, HIPAA-Compliant Local-Only Backend, JWT Authentication, LangSmith Tracing, Prometheus + Grafana Observability (+10 more)

### Community 9 - "Backend Config Tests"
Cohesion: 0.29
Nodes (4): TestSettings, Central management for settings and configurations., Settings, BaseSettings

### Community 10 - "Backend Exception Tests"
Cohesion: 0.33
Nodes (3): TestCustomException, CustomException, Exception

### Community 11 - "Brand & Visual Identity"
Cohesion: 0.39
Nodes (9): Blue Color Scheme, Healthcare Database Icon, Gear/Processing Icon, Heart Plus Icon, CaliperLens Logo, Magnifying Glass Icon, Natural Language Query Text, To SQL Text (+1 more)

### Community 12 - "API Integration Tests"
Cohesion: 0.40
Nodes (3): TestChatEndpoint, TestHealthEndpoint, skipif

### Community 13 - "Multi-Agent Workflow"
Cohesion: 0.50
Nodes (4): Builder Subagent, Multi-Agent Build Workflow, Playwright Tester Subagent, Ponytail Reviewer Subagent

### Community 14 - "OpenCode Configuration"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

## Knowledge Gaps
- **74 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `caliperlens`, `name`, `version` (+69 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLAgentGenerator` connect `Agent SQL Generation` to `Backend Agent Core`, `Backend Exception Tests`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `devDependencies` connect `Frontend Linting` to `Frontend Dependencies`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `SchemaRAG` connect `Backend Agent Core` to `Agent SQL Generation`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `SQLAgentGenerator` (e.g. with `SchemaGraph` and `SchemaRAG`) actually correct?**
  _`SQLAgentGenerator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `CustomException` (e.g. with `SQLAgentGenerator` and `TestCustomException`) actually correct?**
  _`CustomException` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `caliperlens` to the rest of the system?**
  _74 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Linting` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._