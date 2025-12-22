# Development Setup

How to set up your development environment for HAFO.

## Prerequisites

- **Python 3.13+**
- **[uv](https://github.com/astral-sh/uv)** - Python package manager
- **Node.js** - For Prettier formatting
- **Git** - Version control

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/hass-energy/hafo.git
cd hafo
```

### 2. Install Python Dependencies

```bash
uv sync --dev
```

This installs all development dependencies including:

- pytest and coverage tools
- Ruff for linting/formatting
- Pyright for type checking
- MkDocs for documentation

### 3. Install Node Dependencies

```bash
npm install
```

This installs Prettier for JSON formatting.

### 4. Verify Setup

Run the test suite to verify everything is working:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check
uv run ruff format --check
uv run pyright
```

## IDE Setup

### VS Code (Recommended)

Install these extensions:

- **Python** - Python language support
- **Pylance** - Python language server
- **Ruff** - Python linting

The repository includes VS Code settings in `.vscode/` for consistent configuration.

### PyCharm

1. Set Python interpreter to the uv virtual environment
2. Enable Ruff for formatting
3. Configure Pyright for type checking

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `uv run pytest`
4. Run linting: `uv run ruff check && uv run pyright`
5. Commit changes
6. Push and create a pull request
