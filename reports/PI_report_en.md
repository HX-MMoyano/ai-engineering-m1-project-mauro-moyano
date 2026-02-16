# M1PI Report – Customer Support Assistant

**Author:** Mauro Moyano  
**Project:** Multitasking Text Utility / Support Assistant (M1PI)

---

## 1. Architecture

The application is a small CLI pipeline:

- **Input:** A single user question (command-line argument or stdin).
- **Prompt:** Loaded from `prompts/main_prompt.txt`, with a `{{QUESTION}}` placeholder replaced by the user question. The prompt defines the assistant role, the exact JSON schema, and few-shot examples.
- **LLM:** One call to OpenAI Chat Completions (default model: `gpt-4o-mini`) with the composed prompt.
- **Output:** The model is instructed to return only a JSON object. The script parses it, validates the schema (answer, confidence, actions), and prints it to stdout.
- **Metrics:** For each run we record timestamp, `tokens_prompt`, `tokens_completion`, `total_tokens`, `latency_ms`, and `estimated_cost_usd`. Metrics are appended to `metrics/metrics.json` and also printed to stderr.

No server or database: everything is file-based and stateless per run. This keeps the deliverable self-contained and easy to run with `make run` or `uv run python -m src.run_query "..."`.

---

## 2. Prompting technique and rationale

**Technique used: Few-shot prompting.**

The prompt in `prompts/main_prompt.txt` includes:

- Clear **instructions**: act as an assistant for customer support agents; respond only with a JSON object.
- **Explicit schema**: field names and types (answer, confidence, actions).
- **Three few-shot examples**: concrete user questions and the exact JSON response we want (password reset, late order, cancel subscription). This reduces format errors and aligns the model with the desired tone and structure.

**Why few-shot:** We need stable, parseable JSON and consistent fields. Zero-shot alone often produces extra text or small schema variations. Few-shot examples act as a contract and reduce the need for retries or brittle parsing. It was the most direct way to meet the “structured output + at least one explicit prompt engineering technique” requirement without adding chain-of-thought or self-consistency complexity for this scope.

---

## 3. Metrics (sample)

After running at least one query (e.g. `make run`), `metrics/metrics.json` contains one object per run. Example:

```json
{
  "timestamp": "2025-02-15T12:00:00.000000Z",
  "tokens_prompt": 420,
  "tokens_completion": 85,
  "total_tokens": 505,
  "latency_ms": 1200,
  "estimated_cost_usd": 0.000127
}
```

- **tokens_prompt / tokens_completion / total_tokens:** From the OpenAI API `usage` field.
- **latency_ms:** Wall-clock time from request start to response (ms).
- **estimated_cost_usd:** Using approximate gpt-4o-mini pricing (input ~$0.15/1M, output ~$0.60/1M tokens). For other models you’d adjust the constants in `src/run_query.py`.

Reproducing: run `make run` or `make run-query QUESTION="..."` and open `metrics/metrics.json`; each run appends one record.

---

## 4. Challenges and possible improvements

- **JSON robustness:** The model sometimes wraps the JSON in markdown code blocks. The script strips ``` before parsing. A stricter approach would be to use the API’s structured output (e.g. JSON mode / response format) where available.
- **Cost and latency:** For production, you’d add retries, timeouts, and perhaps caching for repeated or similar questions. The current cost estimate is indicative only.
- **Language:** The prompt and examples are in English; supporting other languages would require localized few-shot examples and possibly separate prompt files.
- **Safety:** A **bad-words filter** is implemented in `src/safety.py`: before calling the LLM, the user input is checked against a list (default set in code + optional `prompts/bad_words.txt`). If a word is detected, the request is not sent to the API; instead a fallback JSON is returned (generic message, confidence 0, actions “Escalate to human agent”, “Log moderation event”) and metrics are recorded with `"blocked": true` and zero tokens/cost. This reduces abuse and avoids sending clearly offensive input to the model.

---

*End of report.*
