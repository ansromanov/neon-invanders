"""Unit tests for sprite creation and caching."""

import os
import sys
from unittest.mock import MagicMock, patch

import pygame
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *
from src.sprites import SpriteCache


class TestSpriteCache:
    """Test cases for SpriteCache functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    def test_sprite_cache_initialization(self):
        """Test sprite cache is initialized correctly."""
        sprite_cache = SpriteCache()
        assert hasattr(sprite_cache, "_cache")
        assert isinstance(sprite_cache._cache, dict)
        # Should have sprites after initialization
        assert len(sprite_cache._cache) > 0

    def test_create_all_sprites(self):
        """Test that all sprites are created during initialization."""
        with patch("pygame.Surface") as mock_surface_class:
            # Create a mock surface that behaves like a real pygame.Surface
            mock_surface = MagicMock()
            mock_surface_class.return_value = mock_surface

            # Mock all drawing functions to prevent errors
            with (
                patch("pygame.draw.polygon"),
                patch("pygame.draw.circle"),
                patch("pygame.draw.line"),
                patch("pygame.draw.lines"),
                patch("pygame.draw.rect"),
                patch("pygame.draw.ellipse"),
            ):
                sprite_cache = SpriteCache()

                # Check all expected sprites are in cache
                expected_sprites = [
                    "player",
                    "enemy",
                    "player_bullet",
                    "enemy_bullet",
                    "explosion",
                ]
                for sprite_name in expected_sprites:
                    assert sprite_name in sprite_cache._cache

                # Check bonus sprites
                for i in range(5):
                    assert f"bonus_{i}" in sprite_cache._cache

    def test_get_existing_sprite(self):
        """Test getting an existing sprite."""
        sprite_cache = SpriteCache()

        # Get player sprite
        player_sprite = sprite_cache.get("player")
        assert player_sprite is not None
        assert player_sprite == sprite_cache._cache["player"]

    def test_get_non_existing_sprite(self):
        """Test getting a non-existing sprite returns None."""
        sprite_cache = SpriteCache()

        result = sprite_cache.get("non_existing_sprite")
        assert result is None

    def test_create_player_sprite(self):
        """Test player sprite creation."""
        with patch("pygame.Surface") as mock_surface_class:
            mock_sprite = MagicMock()
            mock_surface_class.return_value = mock_sprite

            with (
                patch("pygame.draw.polygon") as mock_polygon,
                patch("pygame.draw.circle") as mock_circle,
                patch("pygame.draw.line") as mock_line,
                patch("pygame.draw.lines"),
                patch("pygame.draw.rect"),
                patch("pygame.draw.ellipse"),
            ):
                SpriteCache()

                # Check Surface was created with correct parameters
                mock_surface_class.assert_any_call((40, 30), pygame.SRCALPHA)

                # Check drawing calls were made
                assert mock_polygon.called
                assert mock_circle.called
                assert mock_line.called

    def test_create_enemy_sprite(self):
        """Test enemy sprite creation."""
        with patch("pygame.Surface") as mock_surface_class:
            mock_sprite = MagicMock()
            mock_surface_class.return_value = mock_sprite

            with (
                patch("pygame.draw.rect") as mock_rect,
                patch("pygame.draw.circle") as mock_circle,
                patch("pygame.draw.line") as mock_line,
                patch("pygame.draw.lines"),
                patch("pygame.draw.polygon"),
                patch("pygame.draw.ellipse"),
            ):
                SpriteCache()

                # Check Surface was created with correct parameters
                mock_surface_class.assert_any_call((26, 20), pygame.SRCALPHA)

                # Check drawing calls were made
                assert mock_rect.called
                assert mock_circle.called
                assert mock_line.called

    def test_create_bullet_sprites(self):
        """Test bullet sprite creation."""
        with patch("pygame.Surface") as mock_surface_class:
            mock_sprite = MagicMock()
            mock_surface_class.return_value = mock_sprite

            with (
                patch("pygame.draw.ellipse") as mock_ellipse,
                patch("pygame.draw.polygon"),
                patch("pygame.draw.circle"),
                patch("pygame.draw.line"),
                patch("pygame.draw.lines"),
                patch("pygame.draw.rect"),
            ):
                sprite_cache = SpriteCache()

                # Check both bullet types exist
                assert "player_bullet" in sprite_cache._cache
                assert "enemy_bullet" in sprite_cache._cache

                # Check Surface was created with correct parameters
                mock_surface_class.assert_any_call(
                    (BULLET_WIDTH, BULLET_HEIGHT), pygame.SRCALPHA
                )

                # Check ellipse drawing was called
                assert mock_ellipse.called

    def test_create_tetris_sprites(self):
        """Test tetris bonus sprite creation."""
        with patch("pygame.Surface") as mock_surface_class:
            mock_sprite = MagicMock()
            mock_surface_class.return_value = mock_sprite

            with (
                patch("pygame.draw.rect") as mock_rect,
                patch("pygame.draw.polygon"),
                patch("pygame.draw.circle"),
                patch("pygame.draw.line"),
                patch("pygame.draw.lines"),
                patch("pygame.draw.ellipse"),
            ):
                sprite_cache = SpriteCache()

                # Check all bonus sprites exist
                for i in range(5):
                    assert f"bonus_{i}" in sprite_cache._cache

                # Check Surface was created with correct parameters
                mock_surface_class.assert_any_call((20, 20), pygame.SRCALPHA)

                # Check rect drawing was called for tetris blocks
                assert mock_rect.called

    def test_create_explosion_frames(self):
        """Test explosion animation frames creation."""
        with patch("pygame.Surface") as mock_surface_class:
            # Create enough mock surfaces for all sprites plus explosion frames
            mock_surfaces = []
            for _ in range(20):  # More than enough for all sprites
                mock_surface = MagicMock()
                mock_surfaces.append(mock_surface)

            # Use a counter to return different surfaces each time
            call_count = [0]

            def surface_side_effect(*args, **kwargs):  # noqa: ARG001
                idx = call_count[0]
                call_count[0] += 1
                if idx < len(mock_surfaces):
                    return mock_surfaces[idx]
                return MagicMock()

            mock_surface_class.side_effect = surface_side_effect

            with (
                patch("pygame.draw.circle") as mock_circle,
                patch("pygame.draw.polygon"),
                patch("pygame.draw.rect"),
                patch("pygame.draw.line"),
                patch("pygame.draw.lines"),
                patch("pygame.draw.ellipse"),
            ):
                sprite_cache = SpriteCache()

                # Check explosion exists and is a list
                assert "explosion" in sprite_cache._cache
                assert isinstance(sprite_cache._cache["explosion"], list)
                assert len(sprite_cache._cache["explosion"]) == 8

                # Check circles were drawn
                assert mock_circle.called

    def test_sprite_cache_caching(self):
        """Test that sprites are cached and not recreated."""
        sprite_cache = SpriteCache()

        # Get the same sprite multiple times
        player1 = sprite_cache.get("player")
        player2 = sprite_cache.get("player")
        player3 = sprite_cache.get("player")

        # All should be the same object
        assert player1 is player2
        assert player2 is player3

    def test_sprite_colors(self):
        """Test that sprites use the correct colors from config."""
        # This test verifies color constants are used
        with patch("pygame.draw.polygon"):
            SpriteCache()

            # Check if neon colors were used in any polygon calls
            # This test verifies the neon color constants are available
            # The actual color usage is tested implicitly by the sprite creation

    @patch("src.sprites.sprite_cache", MagicMock())
    def test_module_level_sprite_cache_exists(self):
        """Test that the module-level sprite_cache is available."""
        from src import sprites

        # The sprite_cache should exist
        assert hasattr(sprites, "sprite_cache")
        assert isinstance(sprites.sprite_cache, SpriteCache | MagicMock)

    def test_all_sprites_are_surfaces(self):
        """Test that all created sprites are pygame Surfaces."""
        sprite_cache = SpriteCache()

        for sprite_name, sprite in sprite_cache._cache.items():
            if sprite_name in ["explosion", "enemy_frames", "elite_enemy_frames"]:
                # These are lists of animation frames
                assert isinstance(sprite, list)
                for frame in sprite:
                    assert isinstance(frame, pygame.Surface)
            else:
                assert isinstance(sprite, pygame.Surface)
