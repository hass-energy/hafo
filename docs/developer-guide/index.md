# Developer Guide

Welcome to the HAFO developer guide!

This section covers everything you need to contribute to HAFO.

## Getting Started

- **[Setup](setup.md)** - Set up your development environment
- **[Architecture](architecture.md)** - Understand how HAFO works
- **[Testing](testing.md)** - Write and run tests
- **[Contributing](contributing.md)** - Contribution guidelines

## Quick Start

```bash
# Clone the repository
git clone https://github.com/hass-energy/hafo.git
cd hafo

# Install dependencies
uv sync --dev
npm install

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run pyright
```

## Code Standards

- Python 3.13+ with modern features
- Type hints required on all functions
- Ruff for linting and formatting
- Pyright for type checking
- pytest for testing
