# CaliperLens — Problem Statement

## The Problem

Healthcare organizations store millions of patient records across dozens of MySQL tables. Clinical analysts and care managers need to answer ad-hoc questions like "show me top 5 Medicaid patients with highest SDOH scores" or "what percentage of diabetic patients received an intervention last quarter?" Without a technical intermediary, these questions require:

1. Knowledge of the database schema (which tables hold what data)
2. Understanding of complex join paths across 10+ tables
3. Domain-specific SQL (BINARY(16) UUID handling, organization-based access scoping)
4. Manual context switching between querying, analysis, and visualization tools

This creates a bottleneck where domain experts (care managers, clinicians) cannot access data without developer intervention.

## The Solution

CaliperLens is an agentic natural-language-to-SQL engine. A care manager asks a question in plain English, and the system autonomously:

1. **Discovers** relevant tables using semantic vector search (FAISS RAG)
2. **Finds** optimal join paths using a NetworkX schema knowledge graph
3. **Generates** validated SQL with security scoping (org_id filtering, LIMIT enforcement)
4. **Executes** queries inside a sandboxed Docker container
5. **Returns** a natural language answer to the user

## Constraints

- Must run entirely locally (real patient data cannot leave the machine — HIPAA)
- Database is a MySQL dump of `fhs_coredb_local` with BINARY(16) UUIDs requiring special handling
- LLM costs must be zero (free-tier API keys)
- The frontend is deployed standalone (Vercel), displaying that the backend is not connected
