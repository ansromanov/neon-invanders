# Contributing to Neon Invaders

Thank you for your interest in contributing to Neon Invaders! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- uv package manager
- Git

### Initial Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/neon-invanders.git
cd neon-invanders

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync --all-extras

# Install pre-commit hooks
make pre-commit
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow the project structure:

- `src/` - Main game code
- `tests/` - Unit tests
- `assets/` - Game assets

### 3. Code Quality

Before committing, ensure your code passes all checks:

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all tests
make test

# Check coverage (aim for >80%)
make test-cov
```

### 4. Commit Your Changes

We use conventional commits:

```bash
git add .
git commit -m "feat: add new power-up system"
```

Commit types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions/classes
- Keep functions focused and small

### Testing

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Mock external dependencies

Example test:

```python
def test_player_movement_within_bounds(self):
    """Test player stays within screen boundaries."""
    player = Player(x=50, y=550)
    player.move_left()
    assert player.rect.left >= 0
```

### Performance

- Cache expensive operations
- Use sprite groups efficiently
- Profile performance-critical code
- Keep frame rate stable at 60 FPS

## Project Architecture

### Key Modules

- `entities.py` - Game objects (Player, Enemy, Bullet)
- `game.py` - Main game loop and state management
- `sprites.py` - Sprite creation and caching
- `config.py` - Game configuration constants
- `sounds.py` - Audio management
- `hud.py` - UI elements

### Design Patterns

- **Entity-Component**: Game objects inherit from pygame.sprite.Sprite
- **State Pattern**: Game states (MENU, PLAYING, PAUSED, etc.)
- **Object Pooling**: Reuse bullet and particle objects
- **Observer Pattern**: Event handling for collisions

## Making Changes

### Adding a New Feature

1. Discuss the feature in an issue first
2. Write tests for the new functionality
3. Implement the feature
4. Update documentation if needed
5. Ensure all tests pass

### Fixing Bugs

1. Create an issue describing the bug
2. Write a test that reproduces the bug
3. Fix the bug
4. Ensure the test now passes

## Common Tasks

### Adding a New Power-Up

1. Define the power-up type in `config.py`
2. Create the bonus sprite in `sprites.py`
3. Implement effect in `entities.py` (Player class)
4. Add collision handling in `game.py`
5. Write tests for the new power-up

### Adding a New Enemy Type

1. Create new enemy class in `entities.py`
2. Define enemy properties (health, speed, score)
3. Implement unique behavior (movement, attacks)
4. Add to enemy formation in `EnemyGroup`
5. Test enemy behavior and collisions

## Debugging Tips

### Visual Debugging

```python
# Draw collision rectangles
pygame.draw.rect(screen, (255, 0, 0), sprite.rect, 2)

# Show FPS
fps_text = font.render(f"FPS: {clock.get_fps():.0f}", True, (255, 255, 255))
```

### Performance Profiling

```bash
# Run with profiling
python -m cProfile -s cumulative src/main.py
```

## CI/CD

All PRs must pass:

- GitHub Actions tests
- Code coverage requirements
- Linting and type checking
- Pre-commit hooks

## Getting Help

- Check existing issues and PRs
- Ask questions in discussions
- Join our community chat
- Read the AWS challenge guidelines

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Happy coding! 🎮
