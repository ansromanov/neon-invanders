"""Sprite creation and caching for game entities."""

import math
import random

import pygame

from .config import *


class SpriteCache:
    """Cache for game sprites to avoid recreating them."""

    def __init__(self):
        self._cache = {}
        self._create_all_sprites()

    def _create_all_sprites(self):
        """Create all game sprites at initialization."""
        self._cache["player"] = self._create_player_sprite()
        self._cache["enemy_frames"] = self._create_enemy_animation_frames()
        self._cache["enemy"] = self._cache["enemy_frames"][0]  # Default frame
        self._cache["player_bullet"] = self._create_bullet_sprite(
            NEON_GREEN, NEON_YELLOW
        )
        self._cache["enemy_bullet"] = self._create_bullet_sprite(NEON_RED, NEON_ORANGE)
        self._cache["explosion"] = self._create_explosion_frames()

        # Create tetris bonus sprites
        for i in range(5):
            self._cache[f"bonus_{i}"] = self._create_tetris_sprite(i)

        # Create HUD elements
        self._cache["heart"] = self._create_heart_sprite()
        self._cache["shield_icon"] = self._create_shield_icon_sprite()

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

    def _create_enemy_animation_frames(self):
        """Create animated enemy sprites with enhanced animations."""
        frames = []

        # Create 8 animation frames for smoother animation
        for frame_num in range(8):
            sprite = pygame.Surface((26, 20), pygame.SRCALPHA)

            # Animate the body with a pulsing/breathing effect
            pulse = math.sin(frame_num * math.pi / 4) * 2

            # Enemy body with organic movement
            body_width = int(20 + pulse)
            body_height = int(10 - pulse / 2)
            body_x = (26 - body_width) // 2
            body_y = (20 - body_height) // 2 + 2

            # Main body with gradient effect
            pygame.draw.ellipse(
                sprite, NEON_PINK, (body_x, body_y, body_width, body_height)
            )
            pygame.draw.ellipse(
                sprite,
                NEON_PURPLE,
                (body_x + 2, body_y + 2, body_width - 4, body_height - 4),
            )

            # Animated eyes with more expression
            eye_y = 12 + int(pulse / 2)

            if frame_num == 3 or frame_num == 7:  # Blinking frames
                # Eyes closed
                pygame.draw.line(sprite, NEON_YELLOW, (6, eye_y), (10, eye_y), 2)
                pygame.draw.line(sprite, NEON_YELLOW, (16, eye_y), (20, eye_y), 2)
            else:
                # Eyes open with animated pupils
                eye_size = 3
                left_eye_x = 8 + int(pulse / 2)
                right_eye_x = 18 - int(pulse / 2)

                # Eye whites
                pygame.draw.circle(sprite, NEON_YELLOW, (left_eye_x, eye_y), eye_size)
                pygame.draw.circle(sprite, NEON_YELLOW, (right_eye_x, eye_y), eye_size)

                # Pupils that look around
                look_offset = int(math.sin(frame_num * math.pi / 2) * 2)
                pygame.draw.circle(sprite, BLACK, (left_eye_x + look_offset, eye_y), 2)
                pygame.draw.circle(sprite, BLACK, (right_eye_x + look_offset, eye_y), 2)

            # Animated tentacles/antennae with organic movement
            wave1 = math.sin(frame_num * math.pi / 3) * 3
            wave2 = math.cos(frame_num * math.pi / 3) * 3

            # Left antenna with curve
            points_left = [
                (body_x + 3, body_y),
                (body_x + 1 + int(wave1), body_y - 3),
                (body_x - 1 + int(wave2), 2),
            ]
            pygame.draw.lines(sprite, NEON_GREEN, False, points_left, 2)

            # Right antenna with curve
            points_right = [
                (body_x + body_width - 3, body_y),
                (body_x + body_width - 1 - int(wave1), body_y - 3),
                (body_x + body_width + 1 - int(wave2), 2),
            ]
            pygame.draw.lines(sprite, NEON_GREEN, False, points_right, 2)

            # Add pulsing glow effect
            if frame_num % 2 == 0:
                glow_intensity = 30 + int(pulse * 10)
                glow_surf = pygame.Surface((30, 24), pygame.SRCALPHA)
                pygame.draw.ellipse(
                    glow_surf, (*NEON_PINK, glow_intensity), (0, 0, 30, 24)
                )
                sprite.blit(glow_surf, (-2, -2), special_flags=pygame.BLEND_ADD)

            frames.append(sprite)

        # Also create elite enemy frames
        self._cache["elite_enemy_frames"] = self._create_elite_enemy_frames()

        return frames

    def _create_elite_enemy_frames(self):
        """Create animated elite enemy sprites with unique animations."""
        frames = []

        for frame_num in range(8):
            sprite = pygame.Surface((30, 24), pygame.SRCALPHA)

            # Elite enemies have a more aggressive look
            pulse = math.sin(frame_num * math.pi / 4) * 3

            # Spiky body shape
            center_x, center_y = 15, 12

            # Create star/spike pattern
            num_spikes = 6
            for i in range(num_spikes):
                angle1 = (i * 2 * math.pi / num_spikes) + (frame_num * math.pi / 16)
                angle2 = ((i + 0.5) * 2 * math.pi / num_spikes) + (
                    frame_num * math.pi / 16
                )

                # Outer spike
                x1 = center_x + math.cos(angle1) * (10 + pulse)
                y1 = center_y + math.sin(angle1) * (8 + pulse)

                # Inner point
                x2 = center_x + math.cos(angle2) * 5
                y2 = center_y + math.sin(angle2) * 4

                pygame.draw.polygon(
                    sprite,
                    NEON_RED,
                    [(center_x, center_y), (int(x1), int(y1)), (int(x2), int(y2))],
                )

            # Central core
            pygame.draw.circle(sprite, NEON_ORANGE, (center_x, center_y), 6)
            pygame.draw.circle(sprite, NEON_YELLOW, (center_x, center_y), 4)

            # Angry eyes
            if frame_num != 4:  # Not blinking
                eye_offset = int(math.sin(frame_num * math.pi / 2))
                pygame.draw.circle(sprite, WHITE, (center_x - 3, center_y - 1), 2)
                pygame.draw.circle(sprite, WHITE, (center_x + 3, center_y - 1), 2)
                pygame.draw.circle(
                    sprite, NEON_RED, (center_x - 3 + eye_offset, center_y - 1), 1
                )
                pygame.draw.circle(
                    sprite, NEON_RED, (center_x + 3 + eye_offset, center_y - 1), 1
                )

            # Electric effect around elite enemies
            if frame_num % 3 == 0:
                for _ in range(3):
                    start_angle = random.random() * 2 * math.pi
                    start_x = center_x + math.cos(start_angle) * 12
                    start_y = center_y + math.sin(start_angle) * 10
                    end_x = start_x + random.randint(-5, 5)
                    end_y = start_y + random.randint(-5, 5)
                    pygame.draw.line(
                        sprite,
                        NEON_CYAN,
                        (int(start_x), int(start_y)),
                        (int(end_x), int(end_y)),
                        1,
                    )

            frames.append(sprite)

        return frames

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

    def _create_heart_sprite(self):
        """Create a heart sprite for lives display."""
        sprite = pygame.Surface((20, 18), pygame.SRCALPHA)

        # Draw heart shape
        # Top curves
        pygame.draw.circle(sprite, NEON_RED, (6, 6), 5)
        pygame.draw.circle(sprite, NEON_RED, (14, 6), 5)
        # Bottom triangle
        pygame.draw.polygon(sprite, NEON_RED, [(2, 8), (10, 17), (18, 8)])

        # Inner highlight
        pygame.draw.circle(sprite, (*NEON_PINK, 128), (7, 7), 2)

        return sprite

    def _create_shield_icon_sprite(self):
        """Create a shield icon for HUD."""
        sprite = pygame.Surface((20, 22), pygame.SRCALPHA)

        # Shield outline
        points = [
            (10, 2),  # Top center
            (18, 6),  # Top right
            (18, 12),  # Right side
            (10, 20),  # Bottom point
            (2, 12),  # Left side
            (2, 6),  # Top left
        ]
        pygame.draw.polygon(sprite, NEON_CYAN, points)
        pygame.draw.polygon(sprite, (*NEON_CYAN, 128), points, 2)

        # Inner design
        pygame.draw.line(sprite, NEON_GREEN, (10, 5), (10, 15), 2)
        pygame.draw.line(sprite, NEON_GREEN, (6, 9), (14, 9), 2)

        return sprite


# Global sprite cache instance
sprite_cache = SpriteCache()
