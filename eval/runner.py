"""NL-to-SQL eval harness. Validates question schema and runs questions against the agent.

Usage:
    python eval/runner.py --check      # validate questions.json only (CI-safe, no DB)
    python eval/runner.py --run        # run all questions against live agent (needs DB + key)
    python eval/runner.py --run -q eval_001   # run a single question
"""

import argparse
import json
import re
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).parent
QUESTIONS_FILE = EVAL_DIR / "questions.json"

VALID_CATEGORIES = {
    "simple_select",
    "filtered_select",
    "aggregation",
    "join",
    "multi_step",
    "edge_case",
}

VALID_RESULT_TYPES = {"scalar", "rows"}


class EvalError(Exception):
    pass


def load_questions(path: Path = QUESTIONS_FILE) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def validate_question_schema(q: dict) -> list[str]:
    errors = []
    required = ["id", "category", "question", "expected_sql_contains", "expected_result_shape"]
    for field in required:
        if field not in q:
            errors.append(f"{q.get('id', '?')}: missing '{field}'")

    if "category" in q and q["category"] not in VALID_CATEGORIES:
        errors.append(f"{q.get('id')}: invalid category '{q['category']}'")

    if "expected_sql_contains" in q and not isinstance(q["expected_sql_contains"], list):
        errors.append(f"{q.get('id')}: expected_sql_contains must be a list")

    shape = q.get("expected_result_shape", {})
    if isinstance(shape, dict):
        rtype = shape.get("type")
        if rtype not in VALID_RESULT_TYPES:
            errors.append(f"{q.get('id')}: invalid result shape type '{rtype}'")
        if rtype == "scalar" and "min" not in shape and "max" not in shape:
            errors.append(f"{q.get('id')}: scalar shape should specify min/max")
    else:
        errors.append(f"{q.get('id')}: expected_result_shape must be a dict")

    return errors


def check_all_questions(questions: list[dict]) -> tuple[int, list[str]]:
    all_errors = []
    seen_ids = set()
    for q in questions:
        qid = q.get("id")
        if qid in seen_ids:
            all_errors.append(f"duplicate id: {qid}")
        seen_ids.add(qid)
        all_errors.extend(validate_question_schema(q))
    return len(questions), all_errors


# ---- SQL validation ----

def check_sql(sql: str, q: dict) -> list[str]:
    errors = []
    upper = sql.upper()
    for fragment in q.get("expected_sql_contains", []):
        if fragment.upper() not in upper:
            errors.append(f"missing fragment '{fragment}'")

    for pattern in q.get("sql_patterns", []):
        if pattern.lower() not in sql.lower():
            errors.append(f"missing pattern '{pattern}'")

    for table in q.get("tables_required", []):
        if table not in sql.lower():
            errors.append(f"does not reference '{table}'")

    return errors


def check_result_shape(result: str, q: dict) -> list[str]:
    shape = q.get("expected_result_shape", {})
    errors = []
    rtype = shape.get("type")

    if rtype == "scalar":
        match = re.search(r"-?\d+", result)
        if not match:
            return [f"no numeric value in result: {result[:80]!r}"]
        value = int(match.group())
        if "min" in shape and value < shape["min"]:
            errors.append(f"value {value} < min {shape['min']}")
        if "max" in shape and value > shape["max"]:
            errors.append(f"value {value} > max {shape['max']}")
    elif rtype == "rows":
        count = result.count("\n") - 1
        if "min_rows" in shape and count < shape["min_rows"]:
            errors.append(f"row count {count} < min_rows {shape['min_rows']}")
        if "max_rows" in shape and count > shape["max_rows"]:
            errors.append(f"row count {count} > max_rows {shape['max_rows']}")

    return errors


# ---- Agent integration ----

def import_agent():
    sys.path.insert(0, str(EVAL_DIR.parent))
    from backend.src.agent import SQLAgentGenerator

    return SQLAgentGenerator


def run_question(agent, q: dict) -> dict:
    trace = agent.run_with_trace(q["question"], session_id=f"eval_{q['id']}", org_id=16)
    return {
        "response": trace["response"],
        "sql_queries": trace["sql_queries"],
        "sql_results": trace["sql_results"],
        "retries": trace["retries"],
    }


def evaluate_question(q: dict, trace: dict) -> dict:
    sql = trace["sql_queries"][-1] if trace["sql_queries"] else ""
    result = trace["sql_results"][-1] if trace["sql_results"] else trace["response"]

    issues = []

    if not sql:
        issues.append("no SQL was generated")
    else:
        issues.extend(check_sql(sql, q))

    if result:
        issues.extend(check_result_shape(str(result), q))

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "sql": sql, "result": result}


# ---- Runner ----

def cmd_check(questions) -> int:
    count, errors = check_all_questions(questions)
    print(f"Validated {count} questions.")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    print("All questions pass schema validation.")
    return 0


def cmd_run(questions, only_id: str | None) -> int:
    AgentClass = import_agent()
    agent = AgentClass()

    results = []
    for q in questions:
        if only_id and q["id"] != only_id:
            continue
        trace = run_question(agent, q)
        eval_result = evaluate_question(q, trace)
        results.append({"question": q, **eval_result, **trace})

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    repaired = sum(1 for r in results if r["retries"] > 0 and r["passed"])
    retried = sum(1 for r in results if r["retries"] > 0)

    print(f"\n=== EVAL RESULTS ({total} questions) ===")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        marker = f" (repaired: {r['retries']} retries)" if r["retries"] > 0 else ""
        print(f"  [{status}]{marker} {r['question']['id']}: {r['question']['question']}")
        if not r["passed"]:
            for issue in r["issues"]:
                print(f"      - {issue}")

    print(f"\nPass rate: {passed}/{total} ({passed / total * 100:.1f}%)")
    print(f"Auto-repair rate: {repaired}/{retried if retried else 1} "
          f"({repaired / retried * 100:.1f}% of retried questions)")

    return 0 if passed == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="CaliperLens eval harness")
    parser.add_argument("--check", action="store_true", help="validate questions.json only")
    parser.add_argument("--run", action="store_true", help="run questions against live agent")
    parser.add_argument("-q", "--question", help="run only one question by id")
    args = parser.parse_args()

    questions = load_questions()

    if args.check or not args.run:
        return cmd_check(questions)
    if args.run:
        return cmd_run(questions, args.question)
    return 0


if __name__ == "__main__":
    sys.exit(main())
