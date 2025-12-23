# Contributing to HAFO

Thank you for your interest in contributing to HAFO!
This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Node.js (for Prettier formatting)

### Getting Started

1. Clone the repository:

    ```bash
    git clone https://github.com/hass-energy/hafo.git
    cd hafo
    ```

2. Install dependencies:

    ```bash
    uv sync --dev
    npm install
    ```

3. Run tests:

    ```bash
    uv run pytest
    ```

4. Run linting:

    ```bash
    uv run ruff check
    uv run ruff format --check
    uv run pyright
    ```

## Code Standards

### Python

- Python 3.13+ with modern features
- Type hints required on all functions and methods
- Ruff for linting and formatting
- Pyright for type checking

### Formatting

- **Python**: Ruff formatter (120 character line length)
- **JSON**: Prettier
- **Markdown**: mdformat

### Testing

- pytest for all tests
- Coverage enforced on changed lines
- Tests should be clear and well-documented

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, atomic commits
3. Ensure all tests pass and linting is clean
4. Update documentation if needed
5. Submit a pull request with a clear description

## Code of Conduct

Please be respectful and constructive in all interactions.
We're all here to build something useful for the Home Assistant community.
