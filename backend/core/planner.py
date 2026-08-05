from typing import Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    step: int
    action: Literal["query", "analyze", "chart"] = "query"
    description: str
    status: Literal["pending", "running", "done", "failed"] = "pending"


class Plan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)


def planner_system_prompt() -> str:
    return """You are a query planner. Decompose the user's question into a plan of steps.

Output ONLY a JSON object with this structure:
{
  "steps": [
    {"step": 1, "action": "query", "description": "Find top 5 Medicaid patients by SDOH score"},
    {"step": 2, "action": "analyze", "description": "Compute average and median SDOH scores"}
  ]
}

Rules:
- Every plan needs at least one "query" step to retrieve data.
- "analyze" steps run statistics (mean, median, stddev) on query results.
- "chart" steps generate matplotlib visualizations.
- Keep steps minimal. Default to one "query" step unless the question explicitly asks for analysis or charts.
- Use the table schemas provided in the context to plan your queries."""


def re_plan_prompt(error_context: str) -> str:
    return f"""The previous plan step failed with this error:

{error_context}

Generate a revised plan as a JSON object. Try a different approach:
- Use a different table or join path.
- Simplify the query (fewer joins, fewer conditions).
- If a condition name was used, verify its spelling in the database first.
- If the error is about missing data, acknowledge it and produce a simpler query.

Output JSON with the same structure as before."""
