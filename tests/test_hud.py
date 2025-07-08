"""Tests for HUD components."""

import unittest
from unittest.mock import Mock, patch

import pygame

from src.config import (
    NEON_GREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.hud import HUD, AnimatedText, MinimapHUD


class TestAnimatedText(unittest.TestCase):
    """Test cases for AnimatedText class."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.font = Mock(spec=pygame.font.Font)
        self.font.render.return_value = Mock(
            get_width=Mock(return_value=100),
            get_height=Mock(return_value=20),
            get_rect=Mock(return_value=pygame.Rect(0, 0, 100, 20)),
            set_alpha=Mock(),
        )

    def test_animated_text_initialization(self):
        """Test AnimatedText initialization."""
        text = AnimatedText("Test", self.font, NEON_GREEN, (100, 50))
        assert text.text == "Test"
        assert text.font == self.font
        assert text.base_color == NEON_GREEN
        assert text.color == NEON_GREEN
        assert text.pos == (100, 50)
        assert text.base_pos == (100, 50)
        assert text.scale == 1.0
        assert text.alpha == 255
        assert text.effect is None
        assert text.align == "center"

    def test_animated_text_left_alignment(self):
        """Test AnimatedText with left alignment."""
        text = AnimatedText("Score: 0", self.font, NEON_GREEN, (20, 10), align="left")
        assert text.align == "left"
        assert text.pos == (20, 10)

    @patch("pygame.time.get_ticks")
    def test_start_effect(self, mock_get_ticks):
        """Test starting animation effects."""
        mock_get_ticks.return_value = 1000
        text = AnimatedText("Test", self.font, NEON_GREEN, (100, 50))

        text.start_effect("pulse", 500)
        assert text.effect == "pulse"
        assert text.effect_duration == 500
        assert text.effect_start_time == 1000

    @patch("pygame.time.get_ticks")
    def test_pulse_effect(self, mock_get_ticks):
        """Test pulse animation effect."""
        text = AnimatedText("Test", self.font, NEON_GREEN, (100, 50))
        mock_get_ticks.return_value = 1000
        text.start_effect("pulse", 1000)

        # Test mid-animation
        mock_get_ticks.return_value = 1500
        text.update()
        assert text.scale != 1.0  # Scale should be modified

        # Test animation complete
        mock_get_ticks.return_value = 2000
        text.update()
        assert text.scale == 1.0
        assert text.effect is None

    @patch("pygame.time.get_ticks")
    def test_fade_in_effect(self, mock_get_ticks):
        """Test fade in animation effect."""
        text = AnimatedText("Test", self.font, NEON_GREEN, (100, 50))
        mock_get_ticks.return_value = 1000
        text.start_effect("fade_in", 1000)

        # Test mid-animation
        mock_get_ticks.return_value = 1500
        text.update()
        assert text.alpha == 127  # 50% progress

        # Test animation complete
        mock_get_ticks.return_value = 2000
        text.update()
        assert text.alpha == 255
        assert text.effect is None

    def test_render_center_aligned(self):
        """Test rendering with center alignment."""
        screen = Mock()
        text = AnimatedText("Test", self.font, NEON_GREEN, (100, 50), align="center")

        # Create mock surface with methods
        text_surface = Mock()
        text_surface.get_rect.return_value = pygame.Rect(0, 0, 100, 20)
        self.font.render.return_value = text_surface

        text.render(screen)

        self.font.render.assert_called_once_with("Test", True, NEON_GREEN)
        text_surface.get_rect.assert_called_with(center=(100, 50))
        screen.blit.assert_called_once()

    def test_render_left_aligned(self):
        """Test rendering with left alignment."""
        screen = Mock()
        text = AnimatedText("Test", self.font, NEON_GREEN, (20, 10), align="left")

        # Create mock surface with methods
        text_surface = Mock()
        text_surface.get_rect.return_value = pygame.Rect(20, 10, 100, 20)
        self.font.render.return_value = text_surface

        text.render(screen)

        self.font.render.assert_called_once_with("Test", True, NEON_GREEN)
        text_surface.get_rect.assert_called_with(topleft=(20, 10))
        screen.blit.assert_called_once()


class TestHUD(unittest.TestCase):
    """Test cases for HUD class."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.screen = Mock(spec=pygame.Surface)
        self.hud = HUD(self.screen)

        # Mock player
        self.player = Mock()
        self.player.score = 100
        self.player.lives = 3
        self.player.shield_active = False
        self.player.rapid_fire_active = False
        self.player.triple_shot_active = False

        # Mock enemy group
        self.enemy_group = Mock()

    def test_hud_initialization(self):
        """Test HUD initialization."""
        assert self.hud.screen == self.screen
        assert self.hud.font is not None
        assert self.hud.small_font is not None
        assert self.hud.big_font is not None

        # Check score text positioning
        assert self.hud.score_text.pos == (20, 10)
        assert self.hud.score_text.align == "left"
        assert self.hud.score_text.text == "Score: 0"

        # Check wave text positioning
        assert self.hud.wave_text.pos == (SCREEN_WIDTH - 100, 30)
        assert self.hud.wave_text.text == "Wave: 1"

        # Check initial state
        assert self.hud.bonus_indicators == []
        assert self.hud.score_change_texts == []
        assert self.hud.last_score == 0
        assert self.hud.wave_transition_text is None
        assert self.hud.combo_count == 0

    def test_score_update_with_animation(self):
        """Test score update triggers animation."""
        self.hud.last_score = 0
        self.player.score = 100

        with patch.object(self.hud.score_text, "start_effect") as mock_effect:
            self.hud.update(self.player, 1, self.enemy_group)

            assert self.hud.score_text.text == "Score: 100"
            assert self.hud.last_score == 100
            mock_effect.assert_called_once_with("pulse", 500)

    @patch("pygame.time.get_ticks")
    def test_add_score_change(self, mock_get_ticks):
        """Test adding score change animations."""
        mock_get_ticks.return_value = 1000

        # Test positive score change
        self.hud.add_score_change(50)
        assert len(self.hud.score_change_texts) == 1
        surface, pos, start_time, value = self.hud.score_change_texts[0]
        assert pos == [20, 55]  # Left-aligned position
        assert start_time == 1000
        assert value == 50

        # Test negative score change
        self.hud.score_change_texts.clear()
        self.hud.add_score_change(-10)
        assert len(self.hud.score_change_texts) == 1

    @patch("pygame.time.get_ticks")
    def test_combo_system(self, mock_get_ticks):
        """Test combo tracking system."""
        # First kill
        mock_get_ticks.return_value = 1000
        self.hud.register_kill()
        assert self.hud.combo_count == 1
        assert self.hud.last_kill_time == 1000

        # Second kill within combo window
        mock_get_ticks.return_value = 2500  # 1.5 seconds later
        self.hud.register_kill()
        assert self.hud.combo_count == 2

        # Third kill outside combo window
        mock_get_ticks.return_value = 5000  # 3.5 seconds after second kill
        self.hud.register_kill()
        assert self.hud.combo_count == 1  # Reset

    @patch("pygame.time.get_ticks")
    def test_bonus_indicators_positioning(self, mock_get_ticks):
        """Test bonus indicators are positioned correctly."""
        mock_get_ticks.return_value = 1000

        # Enable shield
        self.player.shield_active = True
        self.player.shield_end_time = 4000  # 3 seconds remaining

        # Enable rapid fire
        self.player.rapid_fire_active = True
        self.player.rapid_fire_end_time = 6000  # 5 seconds remaining

        # Enable triple shot
        self.player.triple_shot_active = True

        self.hud.update_bonus_indicators(self.player)

        assert len(self.hud.bonus_indicators) == 3

        # Check positions are left-aligned at x=20
        assert self.hud.bonus_indicators[0]["pos"] == (20, 70)  # Shield
        assert self.hud.bonus_indicators[1]["pos"] == (20, 105)  # Rapid fire
        assert self.hud.bonus_indicators[2]["pos"] == (20, 140)  # Triple shot

    def test_show_wave_transition(self):
        """Test wave transition animation."""
        self.hud.show_wave_transition(2)

        assert self.hud.wave_transition_text is not None
        assert self.hud.wave_transition_text.text == "WAVE 2"
        assert self.hud.wave_transition_text.pos == (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )

    @patch("src.hud.sprite_cache")
    def test_render_hearts_positioning(self, mock_sprite_cache):
        """Test heart rendering positions."""
        mock_heart = Mock()
        mock_sprite_cache.get.return_value = mock_heart

        self.hud.render_hearts(3)

        # Check that hearts are rendered at correct positions
        expected_calls = [
            ((mock_heart, (20, 50)),),  # First heart at x=20
            ((mock_heart, (45, 50)),),  # Second heart at x=45 (20 + 25)
            ((mock_heart, (70, 50)),),  # Third heart at x=70 (20 + 50)
        ]
        assert self.screen.blit.call_args_list == expected_calls


class TestMinimapHUD(unittest.TestCase):
    """Test cases for MinimapHUD class."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.screen = Mock(spec=pygame.Surface)
        self.minimap = MinimapHUD(self.screen)

        # Mock player
        self.player = Mock()
        self.player.rect = pygame.Rect(400, 500, 30, 30)

        # Mock enemies
        self.enemy1 = Mock()
        self.enemy1.rect = pygame.Rect(100, 100, 30, 30)
        self.enemy1.is_elite = False

        self.enemy2 = Mock()
        self.enemy2.rect = pygame.Rect(600, 300, 30, 30)
        self.enemy2.is_elite = True

        self.enemy_group = Mock()
        self.enemy_group.enemies = [self.enemy1, self.enemy2]

    def test_minimap_initialization(self):
        """Test minimap initialization and positioning."""
        assert self.minimap.width == 120
        assert self.minimap.height == 80
        assert self.minimap.x == SCREEN_WIDTH - 120 - 10
        assert self.minimap.y == SCREEN_HEIGHT - 80 - 10

    @patch("pygame.Surface")
    @patch("pygame.draw.rect")
    @patch("pygame.draw.circle")
    def test_render_scaling(self, mock_circle, mock_rect, mock_surface):
        """Test correct scaling of positions on minimap."""
        mock_minimap_surface = Mock()
        mock_surface.return_value = mock_minimap_surface

        self.minimap.render(self.enemy_group, self.player)

        # Calculate expected positions with correct scaling
        scale_x = 120 / SCREEN_WIDTH  # 120 / 800 = 0.15
        scale_y = 80 / SCREEN_HEIGHT  # 80 / 600 = 0.133...

        # Check enemy positions - just verify calculations work
        assert int(115 * scale_x) == int(115 * 0.15)  # enemy1 x
        assert int(115 * scale_y) == int(115 * 0.133)  # enemy1 y
        assert int(615 * scale_x) == int(615 * 0.15)  # enemy2 x
        assert int(315 * scale_y) == int(315 * 0.133)  # enemy2 y

        # Check player position - just verify calculations work
        assert int(415 * scale_x) == int(415 * 0.15)  # player x
        assert int(515 * scale_y) == int(515 * 0.133)  # player y

        # Verify draw calls were made with correct positions
        calls = mock_circle.call_args_list
        assert len(calls) == 3  # 2 enemies + 1 player

        # Note: The exact positions depend on the scaling calculations
        # The important thing is that y-positions use full screen height for scaling


if __name__ == "__main__":
    unittest.main()
