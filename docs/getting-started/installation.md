# Installation

## Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) package manager

## Steps

### 1. Clone the repository

```bash
git clone https://github.com/JC-Prog/finax.git
cd finax
```

### 2. Install dependencies

```bash
uv sync
```

This installs all runtime dependencies defined in `pyproject.toml` into an isolated virtual environment managed by uv.

### 3. Install dev dependencies (optional)

```bash
uv sync --group dev
```

Includes `pytest`, `pytest-asyncio`, and `ruff`.

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys and credentials. See [Configuration](configuration.md) for details.

### 5. Run

```bash
uv run finax
```

The daemon starts, logs to stdout and `finax.log`, and will execute the pipeline at the configured schedule time.

## Running in the background

```bash
nohup uv run finax > finax.log 2>&1 &
```

Or wrap it in a systemd service for production deployments.
