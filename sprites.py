"""Sprite creation and caching for game entities."""

import pygame

from config import *


class SpriteCache:
    """Cache for game sprites to avoid recreating them."""

    def __init__(self):
        self._cache = {}
        self._create_all_sprites()

    def _create_all_sprites(self):
        """Create all game sprites at initialization."""
        self._cache["player"] = self._create_player_sprite()
        self._cache["enemy"] = self._create_enemy_sprite()
        self._cache["player_bullet"] = self._create_bullet_sprite(
            NEON_GREEN, NEON_YELLOW
        )
        self._cache["enemy_bullet"] = self._create_bullet_sprite(NEON_RED, NEON_ORANGE)
        self._cache["explosion"] = self._create_explosion_frames()

        # Create tetris bonus sprites
        for i in range(5):
            self._cache[f"bonus_{i}"] = self._create_tetris_sprite(i)

    def get(self, sprite_name):
        """Get a sprite from the cache."""
        return self._cache.get(sprite_name)

    def _create_player_sprite(self):
        """Create the player ship sprite."""
        sprite = pygame.Surface((40, 30), pygame.SRCALPHA)

        # Main body - sleek fighter design
        pygame.draw.polygon(
            sprite,
            NEON_CYAN,
            [
                (20, 0),  # Nose
                (10, 20),  # Left wing base
                (5, 25),  # Left wing tip
                (0, 25),  # Left wing outer
                (8, 30),  # Left engine
                (20, 28),  # Center rear
                (32, 30),  # Right engine
                (40, 25),  # Right wing outer
                (35, 25),  # Right wing tip
                (30, 20),  # Right wing base
            ],
        )

        # Wing details
        pygame.draw.polygon(
            sprite,
            NEON_GREEN,
            [
                (20, 5),
                (12, 18),
                (20, 22),
                (28, 18),
            ],
            2,
        )

        # Cockpit with glow effect
        pygame.draw.circle(sprite, NEON_YELLOW, (20, 12), 4)
        pygame.draw.circle(sprite, NEON_ORANGE, (20, 12), 2)

        # Engine glow
        pygame.draw.circle(sprite, NEON_PURPLE, (8, 28), 3)
        pygame.draw.circle(sprite, NEON_PURPLE, (32, 28), 3)

        # Highlight lines
        pygame.draw.line(sprite, NEON_GREEN, (20, 0), (20, 8), 2)
        pygame.draw.line(sprite, NEON_CYAN, (5, 25), (12, 20), 1)
        pygame.draw.line(sprite, NEON_CYAN, (35, 25), (28, 20), 1)

        return sprite

    def _create_enemy_sprite(self):
        """Create the enemy sprite."""
        sprite = pygame.Surface((26, 20), pygame.SRCALPHA)
        # Enemy body
        pygame.draw.rect(sprite, NEON_PINK, (3, 6, 20, 10))
        pygame.draw.rect(sprite, NEON_PURPLE, (0, 9, 26, 5))
        # Eyes
        pygame.draw.circle(sprite, NEON_YELLOW, (8, 12), 3)
        pygame.draw.circle(sprite, NEON_YELLOW, (18, 12), 3)
        # Antennae
        pygame.draw.line(sprite, NEON_GREEN, (6, 6), (4, 0), 2)
        pygame.draw.line(sprite, NEON_GREEN, (20, 6), (22, 0), 2)
        return sprite

    def _create_bullet_sprite(self, primary_color, secondary_color):
        """Create a bullet sprite with given colors."""
        sprite = pygame.Surface((BULLET_WIDTH, BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(sprite, primary_color, (0, 0, BULLET_WIDTH, BULLET_HEIGHT))
        pygame.draw.ellipse(
            sprite, secondary_color, (1, 1, BULLET_WIDTH - 2, BULLET_HEIGHT - 2)
        )
        return sprite

    def _create_tetris_sprite(self, shape_type):
        """Create a tetris-themed bonus sprite."""
        sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
        colors = [NEON_CYAN, NEON_YELLOW, NEON_PURPLE, NEON_PINK, NEON_GREEN]
        color = colors[shape_type]

        shapes = [
            [(0, 0), (1, 0), (0, 1), (1, 1)],  # O
            [(1, 0), (0, 1), (1, 1), (2, 1)],  # T
            [(0, 0), (1, 0), (2, 0), (3, 0)],  # I
            [(0, 1), (1, 1), (1, 0), (2, 0)],  # S
            [(0, 0), (1, 0), (1, 1), (2, 1)],  # Z
        ]

        for x, y in shapes[shape_type]:
            pygame.draw.rect(sprite, color, (x * 5, y * 5, 5, 5))
            # Add glow effect
            pygame.draw.rect(sprite, color, (x * 5, y * 5, 5, 5), 1)

        return sprite

    def _create_explosion_frames(self):
        """Create explosion animation frames."""
        frames = []
        for i in range(8):
            size = 10 + i * 5
            frame = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            alpha = 255 - (i * 30)
            color = (*NEON_ORANGE, alpha)
            pygame.draw.circle(frame, color, (size, size), size, 2)
            if i < 4:
                inner_color = (*NEON_YELLOW, alpha)
                pygame.draw.circle(frame, inner_color, (size, size), size // 2)
            frames.append(frame)
        return frames


# Global sprite cache instance
sprite_cache = SpriteCache()
