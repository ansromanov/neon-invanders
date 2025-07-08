"""Main entry point for Neon Space Invaders game."""

from .game_optimized import OptimizedGame


def main():
    """Run the game."""
    game = OptimizedGame()
    game.run()


if __name__ == "__main__":
    main()
