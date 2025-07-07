"""Unit tests for game logic and state management."""

import unittest
import pygame
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import Game
from config import *
from entities import Player, Enemy, Bullet, Bonus


class TestGame(unittest.TestCase):
    """Test cases for Game class."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()

    def tearDown(self):
        """Clean up after tests."""
        # Remove any test highscore files
        if os.path.exists("highscore.json"):
            os.remove("highscore.json")

    def test_game_initialization(self):
        """Test game is initialized correctly."""
        self.assertEqual(self.game.state, GameState.MENU)
        self.assertTrue(self.game.running)
        self.assertEqual(self.game.wave, 1)
        self.assertIsNone(self.game.player)

    def test_load_high_score_no_file(self):
        """Test loading high score when no file exists."""
        score = self.game.load_high_score()
        self.assertEqual(score, 0)

    def test_save_and_load_high_score(self):
        """Test saving and loading high score."""
        # Create a player with a score
        self.game.player = Player(400, 500)
        self.game.player.score = 1000
        self.game.high_score = 500

        # Save high score
        self.game.save_high_score()

        # Load it back
        loaded_score = self.game.load_high_score()
        self.assertEqual(loaded_score, 1000)

    def test_reset_game(self):
        """Test game reset functionality."""
        # Add some sprites to groups
        self.game.player_bullets.add(Bullet(100, 100, -5, "player"))
        self.game.bonuses.add(Bonus(200, 200))

        # Reset game
        self.game.reset_game()

        # Check everything is cleared and reset
        self.assertIsNotNone(self.game.player)
        self.assertEqual(len(self.game.player_bullets), 0)
        self.assertEqual(len(self.game.bonuses), 0)
        self.assertEqual(self.game.wave, 1)
        self.assertEqual(len(self.game.enemy_group.enemies), ENEMY_ROWS * ENEMY_COLS)

    def test_state_transitions_menu_to_playing(self):
        """Test transition from menu to playing."""
        self.game.state = GameState.MENU

        # Simulate space key press
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.PLAYING)
        self.assertIsNotNone(self.game.player)

    def test_state_transitions_playing_to_paused(self):
        """Test transition from playing to paused."""
        self.game.state = GameState.PLAYING
        self.game.reset_game()

        # Simulate escape key press
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.PAUSED)

    def test_player_shoot(self):
        """Test player shooting mechanism."""
        self.game.reset_game()
        initial_bullets = len(self.game.player_bullets)

        # Mock time
        with patch("pygame.time.get_ticks", return_value=1000):
            self.game.player_shoot()

        self.assertEqual(len(self.game.player_bullets), initial_bullets + 1)

    def test_enemy_shoot(self):
        """Test enemy shooting mechanism."""
        self.game.reset_game()
        initial_bullets = len(self.game.enemy_bullets)

        # Mock random to ensure at least one enemy shoots
        with patch("random.random", return_value=0.0001):
            self.game.enemy_shoot()

        # At least one enemy should have shot
        self.assertGreater(len(self.game.enemy_bullets), initial_bullets)

    def test_check_collisions_player_bullet_hits_enemy(self):
        """Test collision detection for player bullets hitting enemies."""
        self.game.reset_game()

        # Get an enemy position
        enemy = list(self.game.enemy_group.enemies)[0]
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_score = self.game.player.score
        initial_enemies = len(self.game.enemy_group.enemies)

        # Check collisions
        self.game.check_collisions()

        # Enemy should be destroyed and score increased
        self.assertEqual(len(self.game.enemy_group.enemies), initial_enemies - 1)
        self.assertEqual(self.game.player.score, initial_score + ENEMY_SCORE)
        self.assertEqual(len(self.game.player_bullets), 0)  # Bullet removed

    def test_check_collisions_enemy_bullet_hits_player(self):
        """Test collision detection for enemy bullets hitting player."""
        self.game.reset_game()

        # Create enemy bullet at player position
        bullet = Bullet(
            self.game.player.rect.centerx, self.game.player.rect.centery, 0, "enemy"
        )
        self.game.enemy_bullets.add(bullet)

        initial_lives = self.game.player.lives

        # Check collisions
        self.game.check_collisions()

        # Player should lose a life
        self.assertEqual(self.game.player.lives, initial_lives - 1)
        self.assertEqual(len(self.game.enemy_bullets), 0)  # Bullet removed

    def test_check_collisions_player_collects_bonus(self):
        """Test collision detection for player collecting bonuses."""
        self.game.reset_game()

        # Create bonus at player position
        bonus = Bonus(self.game.player.rect.centerx, self.game.player.rect.centery)
        self.game.bonuses.add(bonus)

        initial_score = self.game.player.score

        # Check collisions
        self.game.check_collisions()

        # Player should get bonus score
        self.assertEqual(self.game.player.score, initial_score + BONUS_SCORE)
        self.assertEqual(len(self.game.bonuses), 0)  # Bonus removed

    def test_game_over_no_lives(self):
        """Test game over when player has no lives."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state
        self.game.player.lives = 0

        self.game.update()

        self.assertEqual(self.game.state, GameState.GAME_OVER)

    def test_game_over_enemies_reach_player(self):
        """Test game over when enemies reach player."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state

        # Move an enemy close to player
        enemy = list(self.game.enemy_group.enemies)[0]
        enemy.rect.bottom = self.game.player.rect.top - 30

        self.game.update()

        self.assertEqual(self.game.state, GameState.GAME_OVER)
        self.assertEqual(self.game.player.lives, 0)

    def test_wave_clear(self):
        """Test wave clear when all enemies defeated."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state
        initial_score = self.game.player.score

        # Clear all enemies
        self.game.enemy_group.enemies.empty()

        self.game.update()

        self.assertEqual(self.game.state, GameState.WAVE_CLEAR)
        self.assertEqual(self.game.player.score, initial_score + WAVE_CLEAR_BONUS)

    def test_next_wave(self):
        """Test progression to next wave."""
        self.game.reset_game()
        self.game.wave = 1

        self.game.next_wave()

        self.assertEqual(self.game.wave, 2)
        self.assertEqual(len(self.game.enemy_group.enemies), ENEMY_ROWS * ENEMY_COLS)
        self.assertEqual(self.game.state, GameState.PLAYING)

    @patch("random.random")
    def test_bonus_spawn_on_enemy_kill(self, mock_random):
        """Test bonus spawning when enemy is killed."""
        self.game.reset_game()

        # Ensure bonus will spawn
        mock_random.return_value = 0.1  # Less than BONUS_SPAWN_CHANCE

        # Get an enemy position
        enemy = list(self.game.enemy_group.enemies)[0]
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_bonuses = len(self.game.bonuses)

        # Check collisions
        self.game.check_collisions()

        # Bonus should be spawned
        self.assertEqual(len(self.game.bonuses), initial_bonuses + 1)


class TestGameStates(unittest.TestCase):
    """Test cases for game state management."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()

    def test_menu_state_escape_quits(self):
        """Test escape key quits from menu."""
        self.game.state = GameState.MENU
        self.game.running = True

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertFalse(self.game.running)

    def test_paused_state_resume(self):
        """Test resuming from paused state."""
        self.game.state = GameState.PAUSED

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.PLAYING)

    def test_paused_state_quit_to_menu(self):
        """Test quitting to menu from paused state."""
        self.game.state = GameState.PAUSED

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.MENU)

    def test_game_over_continue(self):
        """Test continuing from game over state."""
        self.game.state = GameState.GAME_OVER

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.MENU)

    def test_wave_clear_continue(self):
        """Test continuing from wave clear state."""
        self.game.state = GameState.WAVE_CLEAR
        self.game.wave = 1

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        self.game.handle_events()
        self.assertEqual(self.game.wave, 2)
        self.assertEqual(self.game.state, GameState.PLAYING)


class TestGameIntegration(unittest.TestCase):
    """Integration tests for game flow."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()

    def test_full_game_flow(self):
        """Test complete game flow from menu to game over."""
        # Start at menu
        self.assertEqual(self.game.state, GameState.MENU)

        # Start game
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)
        self.game.handle_events()

        self.assertEqual(self.game.state, GameState.PLAYING)
        self.assertIsNotNone(self.game.player)

        # Simulate player losing all lives
        self.game.player.lives = 1
        self.game.player.hit()

        # Update should detect game over
        self.game.update()
        self.assertEqual(self.game.state, GameState.GAME_OVER)

        # Return to menu
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)
        self.game.handle_events()

        self.assertEqual(self.game.state, GameState.MENU)

    def test_wave_progression(self):
        """Test progressing through multiple waves."""
        # Start game
        self.game.state = GameState.PLAYING
        self.game.reset_game()

        # Clear first wave
        self.game.enemy_group.enemies.empty()
        self.game.update()
        self.assertEqual(self.game.state, GameState.WAVE_CLEAR)

        # Continue to wave 2
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)
        self.game.handle_events()

        self.assertEqual(self.game.wave, 2)
        self.assertEqual(self.game.state, GameState.PLAYING)
        self.assertEqual(len(self.game.enemy_group.enemies), ENEMY_ROWS * ENEMY_COLS)


if __name__ == "__main__":
    unittest.main()
