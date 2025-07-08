"""Unit tests for game logic and state management."""

import os
import sys
from unittest.mock import patch

import pygame
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    BONUS_SCORE,
    ENEMY_COLS,
    ENEMY_ROWS,
    ENEMY_SCORE,
    MUSIC_ENABLED,
    SOUND_ENABLED,
    SOUND_VOLUME,
    WAVE_CLEAR_BONUS,
    GameState,
)
from src.entities import Bonus, Bullet, Player
from src.game import Game


class TestGame:
    """Test cases for Game class."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        pygame.init()
        self.game = Game()
        yield
        # Clean up after tests
        if os.path.exists("highscore.json"):
            os.remove("highscore.json")
        pygame.quit()

    def test_game_initialization(self):
        """Test game is initialized correctly."""
        assert self.game.state == GameState.MENU
        assert self.game.running is True
        assert self.game.wave == 1
        assert self.game.player is None
        assert self.game.sound_enabled == SOUND_ENABLED
        assert self.game.sound_volume == SOUND_VOLUME
        assert self.game.music_enabled == MUSIC_ENABLED
        assert self.game.show_fps is False
        assert self.game.difficulty == "Normal"
        assert self.game.particles_enabled is True

    def test_load_high_score_no_file(self):
        """Test loading high score when no file exists."""
        score = self.game.load_high_score()
        assert score == 0

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
        assert loaded_score == 1000

    def test_reset_game(self):
        """Test game reset functionality."""
        # Add some sprites to groups
        self.game.player_bullets.add(Bullet(100, 100, -5, "player"))
        self.game.bonuses.add(Bonus(200, 200))

        # Reset game
        self.game.reset_game()

        # Check everything is cleared and reset
        assert self.game.player is not None
        assert len(self.game.player_bullets) == 0
        assert len(self.game.bonuses) == 0
        assert self.game.wave == 1
        assert len(self.game.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS

    def test_state_transitions_menu_to_playing(self):
        """Test transition from menu to playing."""
        self.game.state = GameState.MENU

        # Simulate space key press
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager.play_music"):
            self.game.handle_events()
        assert self.game.state == GameState.PLAYING
        assert self.game.player is not None

    def test_state_transitions_menu_to_settings(self):
        """Test transition from menu to settings."""
        self.game.state = GameState.MENU

        # Simulate S key press
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.SETTINGS
        assert hasattr(self.game, "selected_setting")
        assert self.game.selected_setting == 0

    def test_state_transitions_playing_to_paused(self):
        """Test transition from playing to paused."""
        self.game.state = GameState.PLAYING
        self.game.reset_game()

        # Simulate escape key press
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.PAUSED

    def test_player_shoot(self):
        """Test player shooting mechanism."""
        self.game.reset_game()
        initial_bullets = len(self.game.player_bullets)

        # Mock time and sound
        with (
            patch("pygame.time.get_ticks", return_value=1000),
            patch("src.sounds.sound_manager.play"),
        ):
            self.game.player_shoot()

        assert len(self.game.player_bullets) == initial_bullets + 1

    def test_enemy_shoot(self):
        """Test enemy shooting mechanism."""
        self.game.reset_game()
        initial_bullets = len(self.game.enemy_bullets)

        # Mock random to ensure at least one enemy shoots
        with (
            patch("random.random", return_value=0.0001),
            patch("src.sounds.sound_manager.play"),
        ):
            self.game.enemy_shoot()

        # At least one enemy should have shot
        assert len(self.game.enemy_bullets) > initial_bullets

    def test_check_collisions_player_bullet_hits_enemy(self):
        """Test collision detection for player bullets hitting enemies."""
        self.game.reset_game()

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_score = self.game.player.score if self.game.player else 0
        initial_enemies = len(self.game.enemy_group.enemies)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Enemy should be destroyed and score increased
        assert len(self.game.enemy_group.enemies) == initial_enemies - 1
        if self.game.player:
            assert self.game.player.score == initial_score + ENEMY_SCORE
        assert len(self.game.player_bullets) == 0  # Bullet removed

    def test_check_collisions_enemy_bullet_hits_player(self):
        """Test collision detection for enemy bullets hitting player."""
        self.game.reset_game()

        # Create enemy bullet at player position
        assert self.game.player is not None  # Ensure player exists after reset_game
        bullet = Bullet(
            self.game.player.rect.centerx, self.game.player.rect.centery, 0, "enemy"
        )
        self.game.enemy_bullets.add(bullet)

        initial_lives = self.game.player.lives

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Player should lose a life
        if self.game.player:
            assert self.game.player.lives == initial_lives - 1
        assert len(self.game.enemy_bullets) == 0  # Bullet removed

    def test_check_collisions_player_collects_bonus(self):
        """Test collision detection for player collecting bonuses."""
        self.game.reset_game()

        # Create bonus at player position
        assert self.game.player is not None  # Ensure player exists after reset_game
        bonus = Bonus(self.game.player.rect.centerx, self.game.player.rect.centery)
        self.game.bonuses.add(bonus)

        initial_score = self.game.player.score

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Player should get bonus score
        if self.game.player:
            assert self.game.player.score == initial_score + BONUS_SCORE
        assert len(self.game.bonuses) == 0  # Bonus removed

    def test_game_over_no_lives(self):
        """Test game over when player has no lives."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state
        assert self.game.player is not None  # Ensure player exists after reset_game
        self.game.player.lives = 0

        with patch("src.sounds.sound_manager.play"):
            self.game.update()

        assert self.game.state == GameState.GAME_OVER

    def test_game_over_enemies_reach_player(self):
        """Test game over when enemies reach player."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state

        # Move an enemy close to player
        assert self.game.player is not None  # Ensure player exists after reset_game
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy.rect.bottom = self.game.player.rect.top - 30

        with patch("src.sounds.sound_manager.play"):
            self.game.update()

        assert self.game.state == GameState.GAME_OVER
        if self.game.player:
            assert self.game.player.lives == 0

    def test_wave_clear(self):
        """Test wave clear when all enemies defeated."""
        self.game.reset_game()
        self.game.state = GameState.PLAYING  # Ensure we're in playing state
        initial_score = self.game.player.score if self.game.player else 0

        # Clear all enemies
        self.game.enemy_group.enemies.empty()

        with patch("src.sounds.sound_manager.play"):
            self.game.update()

        assert self.game.state == GameState.WAVE_CLEAR
        if self.game.player:
            assert self.game.player.score == initial_score + WAVE_CLEAR_BONUS

    def test_next_wave(self):
        """Test progression to next wave."""
        self.game.reset_game()
        self.game.wave = 1

        with patch("src.sounds.sound_manager.play_music"):
            self.game.next_wave()

        assert self.game.wave == 2
        assert len(self.game.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS
        assert self.game.state == GameState.PLAYING

    def test_get_difficulty_modifier(self):
        """Test difficulty modifier calculation."""
        self.game.difficulty = "Easy"
        assert self.game.get_difficulty_modifier() == 0.7

        self.game.difficulty = "Normal"
        assert self.game.get_difficulty_modifier() == 1.0

        self.game.difficulty = "Hard"
        assert self.game.get_difficulty_modifier() == 1.5

    def test_get_music_theme(self):
        """Test music theme selection based on wave."""
        self.game.wave = 1
        assert self.game.get_music_theme() == 0  # Theme 1

        self.game.wave = 3
        assert self.game.get_music_theme() == 0  # Theme 1

        self.game.wave = 4
        assert self.game.get_music_theme() == 1  # Theme 2

        self.game.wave = 6
        assert self.game.get_music_theme() == 1  # Theme 2

        self.game.wave = 7
        assert self.game.get_music_theme() == 2  # Theme 3

        self.game.wave = 10
        assert self.game.get_music_theme() == 2  # Theme 3

    @patch("random.random")
    def test_bonus_spawn_on_enemy_kill(self, mock_random):
        """Test bonus spawning when enemy is killed."""
        self.game.reset_game()

        # Ensure bonus will spawn
        mock_random.return_value = 0.1  # Less than BONUS_SPAWN_CHANCE

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_bonuses = len(self.game.bonuses)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Bonus should be spawned
        assert len(self.game.bonuses) == initial_bonuses + 1


class TestGameStates:
    """Test cases for game state management."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()
        yield
        pygame.quit()

    def test_menu_state_escape_quits(self):
        """Test escape key quits from menu."""
        self.game.state = GameState.MENU
        self.game.running = True

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.running is False

    def test_paused_state_resume(self):
        """Test resuming from paused state."""
        self.game.state = GameState.PAUSED

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.PLAYING

    def test_paused_state_quit_to_menu(self):
        """Test quitting to menu from paused state."""
        self.game.state = GameState.PAUSED

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_q})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.MENU

    def test_game_over_continue(self):
        """Test continuing from game over state."""
        self.game.state = GameState.GAME_OVER

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.MENU

    def test_wave_clear_continue(self):
        """Test continuing from wave clear state."""
        self.game.state = GameState.WAVE_CLEAR
        self.game.wave = 1

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.wave == 2
        assert self.game.state == GameState.PLAYING


class TestSettingsMenu:
    """Test cases for settings menu functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()
        self.game.state = GameState.SETTINGS
        yield
        pygame.quit()

    def test_settings_navigation_up(self):
        """Test navigating up in settings menu."""
        self.game.settings_menu.selected_index = 2

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.settings_menu.selected_index == 1

    def test_settings_navigation_down(self):
        """Test navigating down in settings menu."""
        self.game.settings_menu.selected_index = 1

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.settings_menu.selected_index == 2

    def test_settings_navigation_boundaries(self):
        """Test navigation boundaries in settings menu."""
        # Test upper boundary
        self.game.settings_menu.selected_index = 0
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP})
        pygame.event.post(event)
        self.game.handle_events()
        assert self.game.settings_menu.selected_index == 0

        # Test lower boundary - we now have 6 settings (0-5)
        self.game.settings_menu.selected_index = 5
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
        pygame.event.post(event)
        self.game.handle_events()
        assert self.game.settings_menu.selected_index == 5

    def test_settings_sound_toggle(self):
        """Test toggling sound on/off."""
        initial_sound = self.game.sound_enabled
        self.game.settings_menu.selected_index = 0

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
        assert self.game.sound_enabled != initial_sound

    def test_settings_music_toggle(self):
        """Test toggling music on/off."""
        # Ensure sound is enabled first
        self.game.sound_enabled = True
        initial_music = self.game.music_enabled
        self.game.settings_menu.selected_index = 1

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
        assert self.game.music_enabled != initial_music

    def test_settings_volume_adjustment(self):
        """Test adjusting volume."""
        self.game.settings_menu.selected_index = 2
        self.game.sound_volume = 0.5

        # Test volume increase
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
        assert abs(self.game.sound_volume - 0.6) < 0.01

        # Test volume decrease
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
        assert abs(self.game.sound_volume - 0.5) < 0.01

    def test_settings_fps_toggle(self):
        """Test toggling FPS display."""
        initial_fps = self.game.show_fps
        self.game.settings_menu.selected_index = 3

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.show_fps != initial_fps

    def test_settings_particles_toggle(self):
        """Test toggling particles on/off."""
        initial_particles = self.game.particles_enabled
        self.game.settings_menu.selected_index = 4

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.particles_enabled != initial_particles

    def test_settings_difficulty_change(self):
        """Test changing difficulty."""
        self.game.settings_menu.selected_index = 5
        self.game.difficulty = "Normal"

        # Test changing to Hard
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        pygame.event.post(event)
        self.game.handle_events()
        assert self.game.difficulty == "Hard"

        # Test changing to Easy
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)
        self.game.handle_events()
        assert self.game.difficulty == "Normal"

    def test_settings_escape_to_menu(self):
        """Test returning to menu from settings."""
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pygame.event.post(event)

        self.game.handle_events()
        assert self.game.state == GameState.MENU


class TestGameIntegration:
    """Integration tests for game flow."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()
        yield
        pygame.quit()

    def test_full_game_flow(self):
        """Test complete game flow from menu to game over."""
        # Start at menu
        assert self.game.state == GameState.MENU

        # Start game
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager.play_music"):
            self.game.handle_events()

        assert self.game.state == GameState.PLAYING
        assert self.game.player is not None

        # Simulate player losing all lives
        assert self.game.player is not None  # Player should exist after starting game
        self.game.player.lives = 1
        self.game.player.hit()

        # Update should detect game over
        with patch("src.sounds.sound_manager.play"):
            self.game.update()
        assert self.game.state == GameState.GAME_OVER

        # Return to menu
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)
        self.game.handle_events()

        assert self.game.state == GameState.MENU

    def test_wave_progression(self):
        """Test progressing through multiple waves."""
        # Start game
        self.game.state = GameState.PLAYING
        self.game.reset_game()

        # Clear first wave
        self.game.enemy_group.enemies.empty()
        with patch("src.sounds.sound_manager.play"):
            self.game.update()
        assert self.game.state == GameState.WAVE_CLEAR

        # Continue to wave 2
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager.play_music"):
            self.game.handle_events()

        assert self.game.wave == 2
        assert self.game.state == GameState.PLAYING
        assert len(self.game.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS


class TestParticleEffects:
    """Test cases for particle effects functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()
        self.game.reset_game()
        yield
        pygame.quit()

    def test_particles_enabled_explosion_on_enemy_kill(self):
        """Test that explosions are created when particles are enabled."""
        self.game.particles_enabled = True

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_explosions = len(self.game.explosions)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Explosion should be created
        assert len(self.game.explosions) == initial_explosions + 1

    def test_particles_disabled_no_explosion_on_enemy_kill(self):
        """Test that no explosions are created when particles are disabled."""
        self.game.particles_enabled = False

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_explosions = len(self.game.explosions)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # No explosion should be created
        assert len(self.game.explosions) == initial_explosions

    def test_particles_enabled_sparkle_on_bonus_spawn(self):
        """Test that sparkle effects are created when particles are enabled."""
        self.game.particles_enabled = True

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_sparkles = len(self.game.sparkle_effects)

        # Mock random to ensure bonus spawns
        with (
            patch("random.random", return_value=0.1),
            patch("src.sounds.sound_manager.play"),
        ):
            self.game.check_collisions()

        # Sparkle effect should be created for bonus spawn
        assert len(self.game.sparkle_effects) > initial_sparkles

    def test_particles_disabled_no_sparkle_on_bonus_spawn(self):
        """Test that no sparkle effects are created when particles are disabled."""
        self.game.particles_enabled = False

        # Get an enemy position
        enemy = next(iter(self.game.enemy_group.enemies))
        enemy_pos = (enemy.rect.centerx, enemy.rect.centery)

        # Create a bullet at enemy position
        bullet = Bullet(enemy_pos[0], enemy_pos[1], 0, "player")
        self.game.player_bullets.add(bullet)

        initial_sparkles = len(self.game.sparkle_effects)

        # Mock random to ensure bonus spawns
        with (
            patch("random.random", return_value=0.1),
            patch("src.sounds.sound_manager.play"),
        ):
            self.game.check_collisions()

        # No sparkle effect should be created
        assert len(self.game.sparkle_effects) == initial_sparkles

    def test_particles_enabled_rainbow_pulse_on_bonus_collect(self):
        """Test that rainbow pulse is created when particles are enabled."""
        self.game.particles_enabled = True

        # Create bonus at player position
        assert self.game.player is not None
        bonus = Bonus(self.game.player.rect.centerx, self.game.player.rect.centery)
        self.game.bonuses.add(bonus)

        initial_pulses = len(self.game.rainbow_pulses)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # Rainbow pulse should be created
        assert len(self.game.rainbow_pulses) == initial_pulses + 1

    def test_particles_disabled_no_rainbow_pulse_on_bonus_collect(self):
        """Test that no rainbow pulse is created when particles are disabled."""
        self.game.particles_enabled = False

        # Create bonus at player position
        assert self.game.player is not None
        bonus = Bonus(self.game.player.rect.centerx, self.game.player.rect.centery)
        self.game.bonuses.add(bonus)

        initial_pulses = len(self.game.rainbow_pulses)

        # Check collisions with mocked sound
        with patch("src.sounds.sound_manager.play"):
            self.game.check_collisions()

        # No rainbow pulse should be created
        assert len(self.game.rainbow_pulses) == initial_pulses

    def test_particles_enabled_celebration_sparkles_on_wave_clear(self):
        """Test that celebration sparkles are created when particles are enabled."""
        self.game.state = GameState.PLAYING
        self.game.particles_enabled = True

        # Clear all enemies
        self.game.enemy_group.enemies.empty()

        initial_sparkles = len(self.game.sparkle_effects)

        with patch("src.sounds.sound_manager.play"):
            self.game.update()

        # Should have created 5 celebration sparkles
        assert len(self.game.sparkle_effects) == initial_sparkles + 5

    def test_particles_disabled_no_celebration_sparkles_on_wave_clear(self):
        """Test that no celebration sparkles are created when particles are disabled."""
        self.game.state = GameState.PLAYING
        self.game.particles_enabled = False

        # Clear all enemies
        self.game.enemy_group.enemies.empty()

        initial_sparkles = len(self.game.sparkle_effects)

        with patch("src.sounds.sound_manager.play"):
            self.game.update()

        # No sparkles should be created
        assert len(self.game.sparkle_effects) == initial_sparkles


class TestMusicSettings:
    """Test cases for music settings functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.game = Game()
        yield
        pygame.quit()

    def test_music_plays_when_enabled_on_game_start(self):
        """Test that music plays when enabled and game starts."""
        self.game.music_enabled = True
        self.game.state = GameState.MENU

        # Start game
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager.play_music") as mock_play_music:
            self.game.handle_events()
            mock_play_music.assert_called_once()

    def test_music_does_not_play_when_disabled_on_game_start(self):
        """Test that music doesn't play when disabled and game starts."""
        self.game.music_enabled = False
        self.game.state = GameState.MENU

        # Start game
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager.play_music") as mock_play_music:
            self.game.handle_events()
            mock_play_music.assert_not_called()

    def test_music_stops_when_disabled_in_settings(self):
        """Test that music stops when disabled in settings during gameplay."""
        self.game.music_enabled = True
        self.game.state = GameState.SETTINGS
        self.game.settings_menu.selected_index = 1  # Music setting

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
            # Music should be toggled off
            assert self.game.music_enabled is False

    def test_sound_disable_also_disables_music(self):
        """Test that disabling sound also disables music."""
        self.game.sound_enabled = True
        self.game.music_enabled = True
        self.game.state = GameState.SETTINGS
        self.game.settings_menu.selected_index = 0  # Sound setting

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        pygame.event.post(event)

        with patch("src.sounds.sound_manager"):
            self.game.handle_events()
            assert self.game.sound_enabled is False
            assert self.game.music_enabled is False
