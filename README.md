# M1 Project - Mauro Moyano (M1PI)

Asistente para soporte al cliente: recibe una pregunta y devuelve JSON (`answer`, `confidence`, `actions`) más métricas por ejecución.

## Cómo ejecutar

**Requisitos:** Python ≥ 3.10, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clonar y entrar al repo
cd ai-engineering-m1-project-mauro-moyano

# 2. Instalar dependencias
make install

# 3. Configurar API key (obligatorio)
cp .env.example .env
# Editar .env y poner tu OPENAI_API_KEY=sk-...

# 4. Ejecutar
make run
```

**Otra pregunta:**
```bash
make run-query QUESTION="How do I cancel my subscription?"
# O: uv run python -m src.run_query "Tu pregunta"
```

Salida: JSON en pantalla; métricas en `metrics/metrics.json`.

## Variables de entorno

| Variable         | Uso                          |
|------------------|------------------------------|
| `OPENAI_API_KEY` | Obligatoria                  |
| `OPENAI_MODEL`   | Opcional (default: gpt-4o-mini) |

## Tests

```bash
make test
```

## Estructura del proyecto

```
.
├── pyproject.toml          # Dependencias
├── Makefile                # install, run, run-query, test
├── .env.example             # Plantilla (copiar a .env)
├── prompts/
│   ├── system_prompt.txt   # Instrucciones + few-shot (rol system)
│   ├── main_prompt.txt     # Notas sobre separación system/user
│   ├── bad_words.txt       # Palabras a filtrar (opcional)
│   └── injection_phrases.txt  # Frases de secuestro (opcional)
├── src/
│   ├── run_query.py        # Entrada → OpenAI → JSON + métricas
│   └── safety.py           # Filtro malas palabras e inyección
├── metrics/
│   └── metrics.json        # Por ejecución: request_id, question_hash, tokens, latency_ms, cost, blocked
├── reports/
│   └── PI_report_en.md    # Informe (arquitectura, prompting, métricas)
└── tests/
    ├── test_core.py        # Esquema JSON, costo, prompt
    └── test_safety.py      # Filtros y fallback
```

- **Métricas:** cada fila tiene `request_id` (único) y `question_hash` (agrupar por misma pregunta sin guardar el texto).
- **Seguridad:** entradas con malas palabras o frases de inyección (ej. "olvida tus instrucciones") devuelven un fallback y se registran con `blocked: true`; no se llama al LLM.

## Informe

Detalle en `reports/PI_report_en.md`.
