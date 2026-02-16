"""
M1PI: run a customer-support query and return structured JSON + metrics.

Usage:
  python -m src.run_query "Your question here"
  echo "Your question" | python -m src.run_query
"""
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.safety import get_fallback_response, is_safe

# Load .env from project root (parent of src/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

SYSTEM_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "system_prompt.txt"
METRICS_DIR = _PROJECT_ROOT / "metrics"
METRICS_FILE = METRICS_DIR / "metrics.json"

# Approximate USD per 1M tokens (gpt-4o-mini)
INPUT_COST_PER_1M_4o = 0.15
OUTPUT_COST_PER_1M_4o = 0.60


def _load_system_prompt() -> str:
    """Load system instructions (no user input). Reduces prompt injection risk."""
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def _user_message(question: str) -> str:
    """User content only: the raw question, sent as a separate message."""
    return question.strip()


def validate_response_schema(data: dict) -> None:
    """Raise ValueError if data does not match expected JSON schema."""
    if not isinstance(data, dict):
        raise ValueError("response must be a JSON object")
    for key in ("answer", "confidence", "actions"):
        if key not in data:
            raise ValueError(f"missing key: {key}")
    if not isinstance(data["answer"], str):
        raise ValueError("answer must be a string")
    c = data["confidence"]
    if not isinstance(c, (int, float)) or not (0 <= c <= 1):
        raise ValueError("confidence must be a number between 0 and 1")
    if not isinstance(data["actions"], list):
        raise ValueError("actions must be a list")
    if not all(isinstance(a, str) for a in data["actions"]):
        raise ValueError("actions must be a list of strings")


def _estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens / 1_000_000 * INPUT_COST_PER_1M_4o) + (
        completion_tokens / 1_000_000 * OUTPUT_COST_PER_1M_4o
    )


def _request_id() -> str:
    """ID único por ejecución (rastreable en logs sin exponer la pregunta)."""
    return uuid.uuid4().hex


def _question_hash(question: str) -> str:
    """Hash corto de la pregunta: agrupar métricas por misma pregunta sin guardar el texto."""
    return hashlib.sha256(question.strip().encode("utf-8")).hexdigest()[:16]


def run_query(question: str) -> tuple[dict, dict]:
    """
    Call OpenAI with the main prompt and return (response_json, metrics_dict).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Use .env or export.")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key)
    system_content = _load_system_prompt()
    user_content = _user_message(question)
    request_id = _request_id()
    question_hash = _question_hash(question)

    # Filtro de malas palabras: no llamar al LLM si la entrada no es segura
    if not is_safe(user_content):
        from datetime import datetime, timezone
        data = get_fallback_response()
        metrics = {
            "request_id": request_id,
            "question_hash": question_hash,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "total_tokens": 0,
            "latency_ms": 0,
            "estimated_cost_usd": 0.0,
            "blocked": True,
        }
        return data, metrics

    import time
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
    )
    latency_ms = round((time.perf_counter() - start) * 1000)

    choice = resp.choices[0]
    content = (choice.message.content or "").strip()
    # Strip markdown code block if present
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    data = json.loads(content)
    validate_response_schema(data)

    usage = resp.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens
    estimated_cost_usd = round(
        _estimate_cost_usd(prompt_tokens, completion_tokens), 6
    )

    from datetime import datetime, timezone
    metrics = {
        "request_id": request_id,
        "question_hash": question_hash,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tokens_prompt": prompt_tokens,
        "tokens_completion": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost_usd,
    }
    return data, metrics


def append_metrics(metrics: dict) -> None:
    """Append one metrics record to metrics/metrics.json."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    if METRICS_FILE.exists():
        records = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        records = [records]
    records.append(metrics)
    METRICS_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = sys.stdin.read().strip()
    if not question:
        print("Usage: python -m src.run_query 'Your question'", file=sys.stderr)
        sys.exit(1)

    data, metrics = run_query(question)
    append_metrics(metrics)

    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("\n# metrics:", json.dumps(metrics), file=sys.stderr)


if __name__ == "__main__":
    main()
