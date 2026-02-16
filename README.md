# M1 Project - Mauro Moyano (M1PI)

Asistente para agentes de soporte al cliente: recibe una pregunta y devuelve JSON con respuesta, confianza y acciones recomendadas, más métricas (tokens, latencia, costo estimado).

## Requisitos

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (gestor de dependencias y entornos)

## Setup

```bash
# Instalar uv (si no lo tienes)
# Windows (PowerShell): irm https://astral.sh/uv/install.ps1 | iex

# Clonar / entrar al repo y instalar dependencias
make install

# Configurar API key (obligatorio para ejecutar consultas)
cp .env.example .env
# Editar .env y setear OPENAI_API_KEY=sk-...
```

## Variables de entorno

| Variable         | Descripción                          |
|------------------|--------------------------------------|
| `OPENAI_API_KEY` | API key de OpenAI (requerida)        |
| `OPENAI_MODEL`   | Modelo a usar (default: gpt-4o-mini) |

## Cómo ejecutar

```bash
# Ejecutar con pregunta de ejemplo
make run

# Ejecutar con tu pregunta
make run-query QUESTION="How do I cancel my subscription?"
# En Windows (bash): make run-query QUESTION="How do I cancel?"
```

O directamente:

```bash
uv run python -m src.run_query "Your question here"
echo "Your question" | uv run python -m src.run_query
```

La salida es JSON en stdout (answer, confidence, actions). Las métricas se imprimen en stderr y se **append** en `metrics/metrics.json`.

## Cómo reproducir métricas

1. Ejecutar al menos una consulta: `make run` o `make run-query QUESTION="..."`.
2. Abrir `metrics/metrics.json`. Cada ejecución añade un objeto con:
   - **`request_id`**: UUID en hex (32 caracteres), único por ejecución. Sirve para identificar esta fila en logs sin guardar la pregunta.
   - **`question_hash`**: Primeros 16 caracteres del SHA256 de la pregunta. Misma pregunta → mismo hash (agrupar métricas por pregunta). No permite recuperar el texto (más seguro que guardar la pregunta).
   - `timestamp`, `tokens_prompt`, `tokens_completion`, `total_tokens`, `latency_ms`, `estimated_cost_usd` (y `blocked` si fue filtrada).

Para varias ejecuciones, el archivo es un JSON array; la primera vez que corras el script se creará el archivo.

## Tests

```bash
make test
# o
uv run pytest tests/ -v
```

Incluye `tests/test_core.py`: validación del esquema JSON de respuesta, estimación de costo por tokens y sustitución del prompt. No se llama a la API en los tests.

## Estructura del repositorio

```
.
├── pyproject.toml
├── Makefile
├── README.md
├── .env.example
├── prompts/
│   └── main_prompt.txt    # Prompt con few-shot y esquema JSON
├── src/
│   └── run_query.py       # Script ejecutable: pregunta → JSON + métricas
├── metrics/
│   └── metrics.json       # Generado al ejecutar (timestamp, tokens, latency, cost)
├── reports/
│   └── PI_report_en.md    # Informe breve (arquitectura, prompting, métricas)
└── tests/
    ├── test_core.py       # Tests de esquema y helpers
    └── test_example.py
```

## Limitaciones conocidas

- El costo estimado usa precios aproximados para gpt-4o-mini; puede variar según modelo y precios actuales de OpenAI.
- Una sola llamada por ejecución; no hay cola ni reintentos automáticos.
- El prompt está en inglés; las preguntas en español pueden funcionar pero los ejemplos few-shot están en inglés.
- No hay moderación ni fallback para prompts adversariales (opcional/bonus).

## Informe

Ver `reports/PI_report_en.md` para arquitectura, técnica de prompting elegida, métricas de ejemplo y trade-offs.
