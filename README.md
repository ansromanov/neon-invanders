# Neon Space Invaders

A modern, neon-themed implementation of the classic Space Invaders game with improved mechanics and proper code structure.

## Features

### Game Mechanics

- **Classic Space Invaders Movement**: Enemies move side-to-side and drop down when reaching screen edges
- **Progressive Difficulty**: Each wave increases enemy movement speed
- **Lives System**: Player has 3 lives
- **Enemy Shooting**: Bottom row enemies can shoot back at the player
- **Bonus System**: Tetris-themed bonuses drop randomly when enemies are destroyed
- **Wave System**: Complete waves to progress with increasing difficulty
- **High Score Tracking**: Persistent high score storage

### Visual Features

- **Neon Color Scheme**: Vibrant neon colors for all game elements
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

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd aws-retro-game-challenge

# Install dependencies using uv (recommended)
uv pip install -e .

# Or install with pip
pip install -e .

# For development (includes testing dependencies)
uv pip install -e ".[dev]"
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

### Code Style

- Type hints for better code clarity
- Comprehensive docstrings
- Following PEP 8 guidelines
- Proper error handling

### Testing Strategy

- Unit tests for all entity classes
- Integration tests for game flow
- Collision detection tests
- State transition tests
- Mock objects for random and time-based functionality

## License

This project is a reimplementation of the classic Space Invaders game for educational purposes.
