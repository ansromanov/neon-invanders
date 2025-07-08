# Neon Invaders

[![Tests](https://github.com/ansromanov/neon-invanders/actions/workflows/test.yml/badge.svg)](https://github.com/ansromanov/neon-invanders/actions/workflows/test.yml)
[![Build](https://github.com/ansromanov/neon-invanders/actions/workflows/build.yml/badge.svg)](https://github.com/ansromanov/neon-invanders/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ansromanov/neon-invanders/branch/main/graph/badge.svg)](https://codecov.io/gh/ansromanov/neon-invanders)

A modern, neon-themed Space Invaders game built for the **AWS Build Classic Games with Amazon Q Developer CLI** challenge.

## Features

- Classic Space Invaders mechanics with modern twists
- Tetris-inspired power-ups (O, T, I, S, Z blocks)
- Progressive difficulty with elite enemies
- Neon visual effects and enhanced graphics
- High score persistence

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ansromanov/neon-invanders.git
cd neon-invanders

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install and run
uv sync
uv run python src/main.py
```

## Controls

- **←/→**: Move
- **Space**: Shoot
- **ESC**: Pause
- **Q**: Quit (while paused)

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
make test

# Code quality checks
make format lint type-check

# Run with coverage
make test-cov
```

## Project Structure

```
src/
├── main.py         # Entry point
├── game.py         # Game logic
├── entities.py     # Game objects
├── sprites.py      # Graphics
└── config.py       # Settings
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## AWS Challenge

This project was created as part of the AWS Build Classic Games with Amazon Q Developer CLI challenge, demonstrating modern Python game development with clean architecture and comprehensive testing.

## License

Educational project based on the classic Space Invaders game.
