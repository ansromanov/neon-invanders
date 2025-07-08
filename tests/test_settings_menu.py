"""Unit tests for the settings menu with scrolling functionality."""

import os
import sys
from unittest.mock import MagicMock, patch

import pygame
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import NEON_CYAN, NEON_GREEN, NEON_PURPLE, SCREEN_HEIGHT, GameState
from src.settings_menu import SettingsMenu


class MockGame:
    """Mock game object for testing."""

    def __init__(self):
        self.sound_enabled = True
        self.music_enabled = True
        self.sound_volume = 0.7
        self.show_fps = False
        self.particles_enabled = True
        self.difficulty = "Normal"
        self.state = GameState.SETTINGS


class TestSettingsMenu:
    """Test cases for SettingsMenu class."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.game = MockGame()
        self.settings_menu = SettingsMenu(self.screen, self.game)
        yield
        pygame.quit()

    def test_initialization(self):
        """Test settings menu is initialized correctly."""
        assert self.settings_menu.selected_index == 0
        assert self.settings_menu.scroll_offset == 0
        assert self.settings_menu.visible_area_top == 140
        assert self.settings_menu.visible_area_bottom == SCREEN_HEIGHT - 100
        assert len(self.settings_menu.all_settings) == 6  # Total number of settings

    def test_categories_structure(self):
        """Test categories are structured correctly."""
        assert len(self.settings_menu.categories) == 3

        # Check Audio category
        audio_cat = self.settings_menu.categories[0]
        assert audio_cat["name"] == "Audio"
        assert audio_cat["color"] == NEON_CYAN
        assert len(audio_cat["settings"]) == 3

        # Check Display category
        display_cat = self.settings_menu.categories[1]
        assert display_cat["name"] == "Display"
        assert display_cat["color"] == NEON_PURPLE
        assert len(display_cat["settings"]) == 2

        # Check Gameplay category
        gameplay_cat = self.settings_menu.categories[2]
        assert gameplay_cat["name"] == "Gameplay"
        assert gameplay_cat["color"] == NEON_GREEN
        assert len(gameplay_cat["settings"]) == 1

    def test_flattened_settings(self):
        """Test settings are flattened correctly for navigation."""
        # Check that all settings have category info
        for setting in self.settings_menu.all_settings:
            assert "category" in setting
            assert "category_color" in setting

        # Verify setting order
        assert self.settings_menu.all_settings[0]["name"] == "Sound"
        assert self.settings_menu.all_settings[1]["name"] == "Music"
        assert self.settings_menu.all_settings[2]["name"] == "Volume"
        assert self.settings_menu.all_settings[3]["name"] == "Show FPS"
        assert self.settings_menu.all_settings[4]["name"] == "Particles"
        assert self.settings_menu.all_settings[5]["name"] == "Difficulty"

    def test_navigation_up(self):
        """Test navigating up in settings menu."""
        self.settings_menu.selected_index = 3
        self.settings_menu.handle_navigation(pygame.K_UP)
        assert self.settings_menu.selected_index == 2

    def test_navigation_down(self):
        """Test navigating down in settings menu."""
        self.settings_menu.selected_index = 2
        self.settings_menu.handle_navigation(pygame.K_DOWN)
        assert self.settings_menu.selected_index == 3

    def test_navigation_boundaries(self):
        """Test navigation stays within boundaries."""
        # Test upper boundary
        self.settings_menu.selected_index = 0
        self.settings_menu.handle_navigation(pygame.K_UP)
        assert self.settings_menu.selected_index == 0

        # Test lower boundary
        self.settings_menu.selected_index = 5
        self.settings_menu.handle_navigation(pygame.K_DOWN)
        assert self.settings_menu.selected_index == 5

    @patch("src.settings_menu.sound_manager")
    def test_sound_toggle(self, mock_sound_manager):
        """Test toggling sound on/off."""
        self.settings_menu.selected_index = 0  # Sound setting

        # Test disabling sound (which should also disable music)
        self.game.sound_enabled = True
        self.game.music_enabled = True

        self.settings_menu.handle_value_change(pygame.K_LEFT)

        assert self.game.sound_enabled is False
        assert self.game.music_enabled is False
        mock_sound_manager.stop_music.assert_called_once()

        # Reset mock
        mock_sound_manager.reset_mock()

        # Test enabling sound
        self.settings_menu.handle_value_change(pygame.K_LEFT)

        assert self.game.sound_enabled is True
        # Music should remain off until explicitly enabled
        assert self.game.music_enabled is False

    def test_music_toggle_requires_sound(self):
        """Test music toggle only works when sound is enabled."""
        self.settings_menu.selected_index = 1  # Music setting

        # Test with sound enabled
        self.game.sound_enabled = True
        self.game.music_enabled = False
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.music_enabled is True

        # Test with sound disabled
        self.game.sound_enabled = False
        self.game.music_enabled = False
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.music_enabled is False  # Should not change

    def test_volume_adjustment(self):
        """Test volume adjustment."""
        self.settings_menu.selected_index = 2  # Volume setting
        self.game.sound_volume = 0.5

        # Test volume increase
        self.settings_menu.handle_value_change(pygame.K_RIGHT)
        assert abs(self.game.sound_volume - 0.6) < 0.01

        # Test volume decrease
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert abs(self.game.sound_volume - 0.5) < 0.01

        # Test volume boundaries
        self.game.sound_volume = 1.0
        self.settings_menu.handle_value_change(pygame.K_RIGHT)
        assert self.game.sound_volume == 1.0

        self.game.sound_volume = 0.0
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.sound_volume == 0.0

    def test_fps_toggle(self):
        """Test toggling FPS display."""
        self.settings_menu.selected_index = 3  # Show FPS setting
        initial_fps = self.game.show_fps

        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.show_fps != initial_fps

    def test_particles_toggle(self):
        """Test toggling particles."""
        self.settings_menu.selected_index = 4  # Particles setting
        initial_particles = self.game.particles_enabled

        self.settings_menu.handle_value_change(pygame.K_RIGHT)
        assert self.game.particles_enabled != initial_particles

    def test_difficulty_change(self):
        """Test changing difficulty."""
        self.settings_menu.selected_index = 5  # Difficulty setting
        self.game.difficulty = "Normal"

        # Test changing to Hard
        self.settings_menu.handle_value_change(pygame.K_RIGHT)
        assert self.game.difficulty == "Hard"

        # Test changing to Easy
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.difficulty == "Normal"

        # Test wrap around
        self.game.difficulty = "Easy"
        self.settings_menu.handle_value_change(pygame.K_LEFT)
        assert self.game.difficulty == "Hard"

    def test_content_height_calculation(self):
        """Test content height is calculated correctly."""
        # The calculation should include:
        # - Category headers and separators
        # - Settings with their spacing
        # - Extra space between categories
        assert self.settings_menu.content_height > 0
        assert (
            self.settings_menu.content_height > self.settings_menu.visible_area_height
        )

    def test_scroll_position_update(self):
        """Test scroll position updates when navigating."""
        # Start at top
        self.settings_menu.selected_index = 0
        self.settings_menu.scroll_offset = 0

        # Navigate to bottom setting
        self.settings_menu.selected_index = 5
        self.settings_menu._update_scroll_for_selection()

        # Should have scrolled down
        assert self.settings_menu.scroll_offset > 0

        # Navigate back to top
        self.settings_menu.selected_index = 0
        self.settings_menu._update_scroll_for_selection()

        # Should have scrolled back up
        assert self.settings_menu.scroll_offset == 0

    def test_scroll_boundaries(self):
        """Test scroll stays within boundaries."""
        # Test that scroll offset never goes negative
        self.settings_menu.selected_index = 0
        self.settings_menu._update_scroll_for_selection()
        assert self.settings_menu.scroll_offset >= 0

        # Test that scroll doesn't exceed content
        self.settings_menu.selected_index = 5
        self.settings_menu._update_scroll_for_selection()
        max_scroll = max(
            0,
            self.settings_menu.content_height - self.settings_menu.visible_area_height,
        )
        assert self.settings_menu.scroll_offset <= max_scroll

    def test_animation_update(self):
        """Test animation update."""
        initial_offset = self.settings_menu.animation_offset
        initial_timer = self.settings_menu.pulse_timer

        self.settings_menu.update()

        assert self.settings_menu.pulse_timer > initial_timer
        # Animation offset should change
        assert (
            self.settings_menu.animation_offset != initial_offset
            or self.settings_menu.pulse_timer < 0.2
        )

    def test_value_getters(self):
        """Test value getters return correct values."""
        for setting in self.settings_menu.all_settings:
            value = setting["value_getter"]()

            if setting["name"] == "Sound":
                assert value == self.game.sound_enabled
            elif setting["name"] == "Music":
                assert value == self.game.music_enabled
            elif setting["name"] == "Volume":
                assert value == self.game.sound_volume
            elif setting["name"] == "Show FPS":
                assert value == self.game.show_fps
            elif setting["name"] == "Particles":
                assert value == self.game.particles_enabled
            elif setting["name"] == "Difficulty":
                assert value == self.game.difficulty


class TestSettingsMenuDrawing:
    """Test cases for settings menu drawing functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.game = MockGame()
        self.settings_menu = SettingsMenu(self.screen, self.game)
        yield
        pygame.quit()

    def test_draw_slider(self):
        """Test slider drawing."""
        # Test drawing doesn't raise errors
        self.settings_menu.draw_slider(100, 100, 200, 40, 0.5, NEON_CYAN, selected=True)
        self.settings_menu.draw_slider(
            100, 200, 200, 40, 0.0, NEON_CYAN, selected=False
        )
        self.settings_menu.draw_slider(
            100, 300, 200, 40, 1.0, NEON_CYAN, selected=False
        )

    def test_draw_toggle(self):
        """Test toggle drawing."""
        # Test drawing doesn't raise errors
        self.settings_menu.draw_toggle(
            100, 100, 80, 30, True, NEON_PURPLE, selected=True
        )
        self.settings_menu.draw_toggle(
            100, 200, 80, 30, False, NEON_PURPLE, selected=False
        )

    def test_draw_choice_selector(self):
        """Test choice selector drawing."""
        # Test drawing doesn't raise errors
        choices = ["Easy", "Normal", "Hard"]
        self.settings_menu.draw_choice_selector(
            300, 100, choices, "Normal", NEON_GREEN, selected=True
        )
        self.settings_menu.draw_choice_selector(
            300, 200, choices, "Hard", NEON_GREEN, selected=False
        )

    @patch("src.neon_effects.NeonText.draw_glowing_text")
    def test_draw_calls_neon_text(self, mock_draw_glowing_text):
        """Test that draw method calls NeonText for title."""
        self.settings_menu.draw()

        # Should draw title and instructions
        assert mock_draw_glowing_text.call_count >= 2

        # Check title call
        title_call = mock_draw_glowing_text.call_args_list[0]
        assert "SETTINGS" in str(title_call)

    def test_draw_with_scroll(self):
        """Test drawing with scroll offset."""
        # Set scroll offset
        self.settings_menu.scroll_offset = 50

        # Test drawing doesn't raise errors
        self.settings_menu.draw()

    @patch("pygame.draw.rect")
    @patch("pygame.draw.circle")
    @patch("pygame.draw.line")
    @patch("src.neon_effects.NeonText.draw_glowing_text")
    def test_draw_with_clipping(
        self, mock_draw_glowing_text, mock_draw_line, mock_draw_circle, mock_draw_rect
    ):
        """Test that clipping is properly set and removed."""
        # Create a mock surface with tracking for set_clip calls
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_surface.get_width.return_value = 800
        mock_surface.get_height.return_value = 600

        # Track clip calls
        clip_calls = []

        def track_set_clip(rect):
            clip_calls.append(rect)

        mock_surface.set_clip.side_effect = track_set_clip

        # Create settings menu with mock surface
        settings_menu = SettingsMenu(mock_surface, self.game)

        # Draw the menu
        settings_menu.draw()

        # Should have called set_clip twice (once to set, once to remove with None)
        assert mock_surface.set_clip.call_count == 2
        assert len(clip_calls) == 2

        # First call should set a clip rect
        assert clip_calls[0] is not None
        assert isinstance(clip_calls[0], pygame.Rect)

        # Second call should remove clipping by passing None
        assert clip_calls[1] is None


class TestSettingsMenuIntegration:
    """Integration tests for settings menu with game."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.game = MockGame()
        self.settings_menu = SettingsMenu(self.screen, self.game)
        yield
        pygame.quit()

    @patch("src.settings_menu.sound_manager")
    def test_sound_and_music_interaction(self, mock_sound_manager):
        """Test interaction between sound and music settings."""
        # Enable both sound and music
        self.game.sound_enabled = True
        self.game.music_enabled = True

        # Disable sound
        self.settings_menu.selected_index = 0
        self.settings_menu.handle_value_change(pygame.K_LEFT)

        # Should disable both sound and music
        assert self.game.sound_enabled is False
        assert self.game.music_enabled is False
        mock_sound_manager.stop_music.assert_called()

    @patch("src.settings_menu.sound_manager")
    def test_volume_updates_all_sounds(self, mock_sound_manager):
        """Test volume change updates all sounds."""
        # Mock sounds dictionary
        mock_sounds = {
            "shoot": MagicMock(),
            "explosion": MagicMock(),
            "bonus": MagicMock(),
        }
        mock_sound_manager.sounds = mock_sounds

        # Change volume
        self.settings_menu.selected_index = 2
        self.game.sound_volume = 0.5
        self.settings_menu.handle_value_change(pygame.K_RIGHT)

        # All sounds should have volume updated
        for sound in mock_sounds.values():
            sound.set_volume.assert_called_with(0.6)

        # Music volume should also be updated
        mock_sound_manager.set_music_volume.assert_called_with(0.6)

    def test_navigation_with_scrolling(self):
        """Test navigation triggers appropriate scrolling."""
        # Start at top
        self.settings_menu.selected_index = 0
        self.settings_menu.scroll_offset = 0

        # Navigate down through all settings
        for _ in range(5):
            self.settings_menu.handle_navigation(pygame.K_DOWN)

        # Should be at last setting
        assert self.settings_menu.selected_index == 5

        # Should have scrolled
        assert self.settings_menu.scroll_offset > 0

        # Navigate back up
        for _ in range(5):
            self.settings_menu.handle_navigation(pygame.K_UP)

        # Should be back at first setting
        assert self.settings_menu.selected_index == 0

        # Should have scrolled back
        assert self.settings_menu.scroll_offset == 0

    def test_full_settings_cycle(self):
        """Test cycling through all settings and changing values."""
        # Test each setting
        for i, setting in enumerate(self.settings_menu.all_settings):
            self.settings_menu.selected_index = i

            if setting["type"] == "toggle":
                initial_value = setting["value_getter"]()
                self.settings_menu.handle_value_change(pygame.K_LEFT)
                # Value should change (unless it's music with sound disabled)
                if setting["name"] != "Music" or self.game.sound_enabled:
                    assert setting["value_getter"]() != initial_value

            elif setting["type"] == "slider":
                self.game.sound_volume = 0.5
                self.settings_menu.handle_value_change(pygame.K_RIGHT)
                assert abs(setting["value_getter"]() - 0.6) < 0.01

            elif setting["type"] == "choice":
                self.game.difficulty = "Normal"
                self.settings_menu.handle_value_change(pygame.K_RIGHT)
                assert setting["value_getter"]() == "Hard"
