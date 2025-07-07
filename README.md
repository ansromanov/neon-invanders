# Neon Invaders

A modern, neon-themed implementation of the classic Space Invaders game with improved mechanics, Tetris-inspired power-ups, and enhanced ship graphics.

## Features

### Game Mechanics

- **Classic Space Invaders Movement**: Enemies move side-to-side and drop down when reaching screen edges
- **Progressive Difficulty**: Each wave increases enemy movement speed
- **Lives System**: Player has 3 lives
- **Enemy Shooting**: Bottom row enemies can shoot back at the player
- **Bonus System**: Tetris-themed bonuses with unique power-ups:
  - **O-block (Cyan)**: Extra life
  - **T-block (Yellow)**: Freeze enemies for 5 seconds
  - **I-block (Purple)**: Triple shot in triangular pattern
  - **S-block (Pink)**: Temporary shield
  - **Z-block (Green)**: Rapid fire for 5 seconds
- **Wave System**: Complete waves to progress with increasing difficulty
- **High Score Tracking**: Persistent high score storage

### Visual Features

- **Neon Color Scheme**: Vibrant neon colors for all game elements
- **Enhanced Ship Graphics**: Sleek fighter design with engine glow effects
- **Explosion Effects**: Animated explosions when enemies or player are hit
- **Clean UI**: Score, lives, and wave information clearly displayed

### Game States

- **Main Menu**: Start game or quit
- **Playing**: Active gameplay
- **Paused**: Pause during gameplay (ESC key)
- **Game Over**: Display final score and high score
- **Wave Clear**: Celebration screen between waves

## Installation

### Requirements

- Python 3.11 or higher
- pygame 2.6.1 or higher
- uv (recommended for package management)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd aws-retro-game-challenge

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the game
uv sync

# For development (includes testing, linting, and tooling)
uv sync --all-extras
make pre-commit  # Install pre-commit hooks
```

### Alternative Setup (pip)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the game
pip install -e .

# For development
pip install -e ".[dev]"
```

## How to Play

### Running the Game

```bash
python main.py
```

### Controls

- **Arrow Keys**: Move left/right
- **Space**: Shoot
- **ESC**: Pause/Resume game
- **Q**: Quit to menu (while paused)

### Gameplay

1. Destroy all enemies in each wave
2. Avoid enemy bullets
3. Collect bonus items for extra points
4. Progress through waves with increasing difficulty
5. Try to achieve the highest score!

## Running Tests

The game includes comprehensive unit tests for all major components.

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
aws-retro-game-challenge/
├── main.py              # Entry point
├── game.py              # Main game logic and state management
├── entities.py          # Game entities (Player, Enemy, Bullet, etc.)
├── sprites.py           # Sprite creation and caching
├── config.py            # Game configuration and constants
├── run_tests.py         # Test runner
└── tests/               # Unit tests
    ├── test_entities.py # Tests for game entities
    └── test_game.py     # Tests for game logic
```

## Issues Fixed from Original Implementation

1. **Proper Space Invaders Movement**: Enemies now move horizontally and drop when reaching edges
2. **Game Over Conditions**: Game ends when player loses all lives or enemies reach player
3. **Collision Detection**: Using pygame's built-in sprite collision system
4. **Performance**: Sprite caching prevents recreating sprites every frame
5. **Code Structure**: Properly organized into modules with clear separation of concerns
6. **Game States**: Proper state management with menu, pause, and game over screens
7. **Enemy Shooting**: Only bottom row enemies can shoot
8. **Wave System**: Clear progression through waves with increasing difficulty
9. **High Score Persistence**: Scores are saved between game sessions

## Development

### Quick Development Commands

```bash
# Run the game
make run

# Run tests with coverage
make test-cov

# Format code
make format

# Run linting
make lint

# Run all quality checks
make lint format type-check security

# Clean build artifacts
make clean
```

### Code Style

- Type hints for better code clarity
- Comprehensive docstrings
- Following PEP 8 guidelines
- Proper error handling
- Ruff for linting and formatting
- Black-compatible formatting (88 char line length)

### Testing Strategy

- Unit tests for all entity classes
- Integration tests for game flow
- Collision detection tests
- State transition tests
- Mock objects for random and time-based functionality
- Coverage target: >80%

### Development Tools

- **Package Management**: uv
- **Linting/Formatting**: Ruff
- **Type Checking**: mypy
- **Testing**: pytest with coverage
- **Security**: bandit
- **Pre-commit**: Automated code quality checks
- **CI/CD**: GitHub Actions
- **Containerization**: Docker & Docker Compose

### Docker Development

```bash
# Run the game in Docker
docker-compose up game

# Run tests in Docker
docker-compose run test

# Development shell
docker-compose run dev
```

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

This project is a reimplementation of the classic Space Invaders game for educational purposes.
