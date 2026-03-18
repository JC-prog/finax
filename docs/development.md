# Development

## Setup

```bash
git clone https://github.com/JC-Prog/finax.git
cd finax
uv sync --group dev
cp .env.example .env   # fill in credentials
```

---

## Linting & formatting

Finax uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

```bash
# Check
uv run ruff check src/

# Auto-fix
uv run ruff check src/ --fix

# Format
uv run ruff format src/
```

Ruff is configured in `pyproject.toml`:

```toml
[tool.ruff]
src = ["src"]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```

---

## Testing

```bash
uv run pytest
```

Tests live in `tests/` and use `pytest-asyncio` with `asyncio_mode = "auto"`.

---

## Serving the docs

```bash
uv run mkdocs serve
```

Opens a live-reload server at `http://127.0.0.1:8000`.

To build static HTML:

```bash
uv run mkdocs build
```

Output goes to `site/`.

---

## Project structure

```
finax/
├── src/
│   └── finax/
│       ├── main.py          # entry point
│       ├── config.py        # settings
│       ├── state.py         # data models
│       ├── graph.py         # LangGraph pipeline
│       ├── scheduler.py     # APScheduler daemon
│       └── agents/
│           ├── scout.py     # news fetching
│           ├── analyst.py   # sentiment analysis
│           └── alert.py     # notifications
├── tests/
├── docs/
├── .env.example
├── pyproject.toml
├── mkdocs.yml
└── CHANGELOG.md
```

---

## Adding a new agent

1. Create `src/finax/agents/your_agent.py` with an async node function:
   ```python
   async def your_agent_node(state: FinaxState) -> dict:
       ...
       return {"your_key": result}
   ```
2. Add the new field to `FinaxState` in `state.py`
3. Register the node and edge in `graph.py`
4. Document it under `docs/architecture/agents/`
