"""Neon visual effects for the retro game."""

import math
import random
from typing import Any

import pygame

from .config import (
    NEON_CYAN,
    NEON_GREEN,
    NEON_ORANGE,
    NEON_PINK,
    NEON_PURPLE,
    NEON_RED,
    NEON_YELLOW,
    PARTICLE_COUNT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STAR_COUNT,
)


class NeonEffect:
    """Base class for neon effects."""

    def __init__(self, color: tuple[int, int, int], glow_radius: int = 10):
        self.color = color
        self.glow_radius = glow_radius
        self.glow_surface = None
        self.create_glow_surface()

    def create_glow_surface(self):
        """Create a surface for the glow effect."""
        size = self.glow_radius * 4
        self.glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        # Create multiple layers of glow
        for i in range(self.glow_radius):
            alpha = int(255 * (1 - i / self.glow_radius) * 0.3)
            radius = self.glow_radius - i
            color = (*self.color, alpha)
            pygame.draw.circle(self.glow_surface, color, (center, center), radius)

    def draw_glowing_line(
        self,
        surface: pygame.Surface,
        start_pos: tuple[int, int],
        end_pos: tuple[int, int],
        width: int = 2,
    ):
        """Draw a line with neon glow effect."""
        # Draw the glow
        for i in range(3):
            glow_width = width + (3 - i) * 2
            alpha = 50 + i * 30
            glow_color = (*self.color, alpha)

            # Create a temporary surface for the glow
            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pygame.draw.line(temp_surface, glow_color, start_pos, end_pos, glow_width)
            surface.blit(temp_surface, (0, 0))

        # Draw the core line
        pygame.draw.line(surface, self.color, start_pos, end_pos, width)

    def draw_glowing_circle(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        width: int = 0,
    ):
        """Draw a circle with neon glow effect."""
        # Draw the glow layers
        for i in range(3):
            glow_radius = radius + (3 - i) * 3
            alpha = 30 + i * 20
            glow_color = (*self.color, alpha)

            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pygame.draw.circle(temp_surface, glow_color, center, glow_radius, width)
            surface.blit(temp_surface, (0, 0))

        # Draw the core circle
        pygame.draw.circle(surface, self.color, center, radius, width)

    def draw_glowing_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        width: int = 0,
        border_radius: int = 0,
    ):
        """Draw a rectangle with neon glow effect."""
        # Draw glow layers
        for i in range(3):
            glow_size = (3 - i) * 3
            glow_rect = rect.inflate(glow_size * 2, glow_size * 2)
            alpha = 30 + i * 20
            glow_color = (*self.color, alpha)

            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            if border_radius > 0:
                pygame.draw.rect(
                    temp_surface, glow_color, glow_rect, width, border_radius
                )
            else:
                pygame.draw.rect(temp_surface, glow_color, glow_rect, width)
            surface.blit(temp_surface, (0, 0))

        # Draw the core rectangle
        if border_radius > 0:
            pygame.draw.rect(surface, self.color, rect, width, border_radius)
        else:
            pygame.draw.rect(surface, self.color, rect, width)


class NeonTrail:
    """Creates a neon trail effect for moving objects."""

    def __init__(self, color: tuple[int, int, int], max_length: int = 10):
        self.color = color
        self.max_length = max_length
        self.trail_points: list[tuple[int, int]] = []

    def add_point(self, pos: tuple[int, int]):
        """Add a point to the trail."""
        self.trail_points.append(pos)
        if len(self.trail_points) > self.max_length:
            self.trail_points.pop(0)

    def draw(self, surface: pygame.Surface):
        """Draw the neon trail."""
        if len(self.trail_points) < 2:
            return

        for i in range(1, len(self.trail_points)):
            # Calculate alpha based on position in trail
            alpha = int(255 * (i / len(self.trail_points)) * 0.5)
            width = max(1, int(3 * (i / len(self.trail_points))))

            # Draw glow
            glow_alpha = alpha // 3
            glow_width = width + 4
            glow_color = (*self.color, glow_alpha)

            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pygame.draw.line(
                temp_surface,
                glow_color,
                self.trail_points[i - 1],
                self.trail_points[i],
                glow_width,
            )
            surface.blit(temp_surface, (0, 0))

            # Draw core line
            color = (*self.color, alpha)
            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            pygame.draw.line(
                temp_surface,
                color,
                self.trail_points[i - 1],
                self.trail_points[i],
                width,
            )
            surface.blit(temp_surface, (0, 0))

    def clear(self):
        """Clear the trail."""
        self.trail_points.clear()


class NeonPulse:
    """Creates a pulsing neon effect."""

    def __init__(
        self,
        center: tuple[int, int],
        color: tuple[int, int, int],
        max_radius: int = 50,
        speed: float = 2.0,
    ):
        self.center = center
        self.color = color
        self.max_radius = max_radius
        self.speed = speed
        self.current_radius = 0
        self.alpha = 255
        self.active = True

    def update(self):
        """Update the pulse animation."""
        if not self.active:
            return

        self.current_radius += self.speed
        self.alpha = int(255 * (1 - self.current_radius / self.max_radius))

        if self.current_radius >= self.max_radius:
            self.active = False

    def draw(self, surface: pygame.Surface):
        """Draw the pulse effect."""
        if not self.active or self.alpha <= 0:
            return

        # Draw multiple rings for better effect
        for i in range(3):
            radius = int(self.current_radius - i * 5)
            if radius > 0:
                alpha = max(0, self.alpha - i * 50)
                color = (*self.color, alpha)

                temp_surface = pygame.Surface(
                    (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
                )
                pygame.draw.circle(temp_surface, color, self.center, radius, 2)
                surface.blit(temp_surface, (0, 0))


class NeonParticle:
    """Individual neon particle for particle effects."""

    def __init__(
        self,
        pos: tuple[int, int],
        velocity: tuple[float, float],
        color: tuple[int, int, int],
        lifetime: int = 60,
        size: int = 3,
    ):
        self.pos = [float(pos[0]), float(pos[1])]
        self.velocity = [float(velocity[0]), float(velocity[1])]
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.active = True

    def update(self):
        """Update particle position and lifetime."""
        if not self.active:
            return

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.lifetime -= 1

        # Add slight gravity effect
        self.velocity[1] += 0.1

        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface: pygame.Surface):
        """Draw the particle with glow."""
        if not self.active:
            return

        # Make particles more transparent
        alpha = int(110 * (self.lifetime / self.max_lifetime))  # Reduced from 255

        # Draw glow
        glow_size = self.size + 3
        glow_alpha = alpha // 4  # More transparent glow
        glow_color = (*self.color, glow_alpha)

        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(
            temp_surface, glow_color, (int(self.pos[0]), int(self.pos[1])), glow_size
        )
        surface.blit(temp_surface, (0, 0))

        # Draw core
        color = (*self.color, alpha)
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(
            temp_surface, color, (int(self.pos[0]), int(self.pos[1])), self.size
        )
        surface.blit(temp_surface, (0, 0))


class NeonExplosion:
    """Creates a neon explosion effect with particles."""

    def __init__(
        self,
        center: tuple[int, int],
        color: tuple[int, int, int],
        particle_count: int | None = None,
    ):
        self.center = center
        self.particles = []

        # Use config value if particle_count not specified
        if particle_count is None:
            particle_count = PARTICLE_COUNT

        # Create particles
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            velocity = (
                math.cos(angle) * speed,
                math.sin(angle) * speed - 2,  # Slight upward bias
            )

            # Vary particle properties
            size = random.randint(2, 4)
            lifetime = random.randint(30, 60)

            particle = NeonParticle(center, velocity, color, lifetime, size)
            self.particles.append(particle)

        # Also create a pulse effect
        self.pulse = NeonPulse(center, color, max_radius=30, speed=3)

    def update(self):
        """Update all particles and effects."""
        for particle in self.particles:
            particle.update()
        self.pulse.update()

        # Remove inactive particles
        self.particles = [p for p in self.particles if p.active]

    def draw(self, surface: pygame.Surface):
        """Draw the explosion effect."""
        self.pulse.draw(surface)
        for particle in self.particles:
            particle.draw(surface)

    def is_active(self) -> bool:
        """Check if the explosion is still active."""
        return len(self.particles) > 0 or self.pulse.active


class NeonGrid:
    """Creates a retro neon grid background effect."""

    def __init__(
        self,
        grid_size: int = 50,
        color: tuple[int, int, int] = NEON_CYAN,
        alpha: int = 30,
    ):
        self.grid_size = grid_size
        self.color = (*color, alpha)
        self.offset = 0
        self.scroll_speed = 0.5

    def update(self):
        """Update grid animation."""
        self.offset += self.scroll_speed
        if self.offset >= self.grid_size:
            self.offset = 0

    def draw(self, surface: pygame.Surface):
        """Draw the animated grid."""
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Draw vertical lines
        for x in range(0, SCREEN_WIDTH + self.grid_size, self.grid_size):
            pygame.draw.line(
                temp_surface,
                self.color,
                (x, 0),
                (x, SCREEN_HEIGHT),
                1,
            )

        # Draw horizontal lines with perspective effect
        for y in range(0, SCREEN_HEIGHT + self.grid_size, self.grid_size):
            # Make lines closer together near the bottom (perspective)
            adjusted_y = int(y + self.offset * (y / SCREEN_HEIGHT))
            if adjusted_y < SCREEN_HEIGHT:
                pygame.draw.line(
                    temp_surface,
                    self.color,
                    (0, adjusted_y),
                    (SCREEN_WIDTH, adjusted_y),
                    1,
                )

        surface.blit(temp_surface, (0, 0))


class NeonText:
    """Creates glowing neon text effects."""

    @staticmethod
    def draw_glowing_text(
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        pos: tuple[int, int],
        color: tuple[int, int, int],
        glow_intensity: int = 3,
    ):
        """Draw text with neon glow effect."""
        # Create text surface
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=pos)

        # Draw glow layers
        for i in range(glow_intensity):
            glow_size = (glow_intensity - i) * 2
            glow_alpha = 50 + i * 30

            # Create glow surface
            glow_surface = font.render(text, True, (*color, glow_alpha))
            glow_surface = pygame.transform.smoothscale(
                glow_surface,
                (
                    glow_surface.get_width() + glow_size,
                    glow_surface.get_height() + glow_size,
                ),
            )

            # Draw glow
            glow_rect = glow_surface.get_rect(center=pos)
            temp_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )
            temp_surface.blit(glow_surface, glow_rect)
            surface.blit(temp_surface, (0, 0))

        # Draw core text
        surface.blit(text_surface, text_rect)


class RainbowPulse:
    """Creates a cute rainbow pulse effect."""

    def __init__(self, center: tuple[int, int], max_radius: int = 60):
        self.center = center
        self.max_radius = max_radius
        self.current_radius = 0
        self.speed = 1.5
        self.active = True
        self.hue = 0

    def update(self):
        """Update the rainbow pulse."""
        if not self.active:
            return

        self.current_radius += self.speed
        self.hue = (self.hue + 5) % 360

        if self.current_radius >= self.max_radius:
            self.active = False

    def draw(self, surface: pygame.Surface):
        """Draw the rainbow pulse."""
        if not self.active:
            return

        # Create rainbow colors
        for i in range(5):
            radius = int(self.current_radius - i * 3)
            if radius > 0:
                hue = (self.hue + i * 30) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 50 - i * 10)

                temp_surface = pygame.Surface(
                    (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
                )
                pygame.draw.circle(temp_surface, color, self.center, radius, 2)
                surface.blit(temp_surface, (0, 0))


class StarField:
    """Creates an animated starfield background."""

    def __init__(self, star_count: int | None = None):
        self.stars = []
        # Use config value if star_count not specified
        if star_count is None:
            star_count = STAR_COUNT

        for _ in range(star_count):
            self.stars.append(
                {
                    "x": random.randint(0, SCREEN_WIDTH),
                    "y": random.randint(0, SCREEN_HEIGHT),
                    "speed": random.uniform(0.5, 3),
                    "size": random.randint(1, 3),
                    "brightness": random.uniform(0.3, 0.8),  # Slightly dimmer
                    "twinkle": random.uniform(0, math.pi * 2),
                }
            )

    def update(self):
        """Update star positions."""
        for star in self.stars:
            star["y"] += star["speed"]
            star["twinkle"] += 0.1

            if star["y"] > SCREEN_HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface: pygame.Surface):
        """Draw the starfield."""
        for star in self.stars:
            # Calculate twinkle effect
            twinkle = (math.sin(star["twinkle"]) + 1) * 0.5
            alpha = int(star["brightness"] * twinkle * 255)

            # Draw star with glow
            color = (*NEON_CYAN, min(alpha, 180))  # Cap transparency
            pos = (int(star["x"]), int(star["y"]))

            # Glow
            glow_surf = pygame.Surface(
                (star["size"] * 4, star["size"] * 4), pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow_surf,
                (*NEON_CYAN, alpha // 4),  # More transparent glow
                (star["size"] * 2, star["size"] * 2),
                star["size"] * 2,
            )
            surface.blit(
                glow_surf, (pos[0] - star["size"] * 2, pos[1] - star["size"] * 2)
            )

            # Core
            pygame.draw.circle(surface, color, pos, star["size"])


class HeartBeat:
    """Creates a cute heartbeat animation effect."""

    def __init__(self, pos: tuple[int, int], color: tuple[int, int, int] = NEON_PINK):
        self.pos = pos
        self.color = color
        self.scale = 1.0
        self.beat_phase = 0
        self.active = True

    def update(self):
        """Update heartbeat animation."""
        self.beat_phase += 0.15
        # Create double-beat pattern like real heartbeat
        self.scale = 1.0 + math.sin(self.beat_phase) * 0.3
        if math.sin(self.beat_phase - 0.3) > 0.8:
            self.scale += 0.2

    def draw(self, surface: pygame.Surface):
        """Draw animated heart."""
        size = int(20 * self.scale)
        heart_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # Draw heart shape
        center_x, center_y = size, size

        # Left curve
        pygame.draw.circle(
            heart_surf,
            self.color,
            (center_x - size // 4, center_y - size // 4),
            size // 3,
        )
        # Right curve
        pygame.draw.circle(
            heart_surf,
            self.color,
            (center_x + size // 4, center_y - size // 4),
            size // 3,
        )
        # Bottom triangle
        points = [
            (center_x - size // 2, center_y),
            (center_x + size // 2, center_y),
            (center_x, center_y + size // 2),
        ]
        pygame.draw.polygon(heart_surf, self.color, points)

        # Add glow
        glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 50), (size * 1.5, size * 1.5), size)

        # Blit to main surface
        surface.blit(glow_surf, (self.pos[0] - size * 1.5, self.pos[1] - size * 1.5))
        surface.blit(heart_surf, (self.pos[0] - size, self.pos[1] - size))


class SparkleEffect:
    """Creates cute sparkle effects."""

    def __init__(self, pos: tuple[int, int]):
        self.pos = pos
        self.sparkles: list[dict[str, Any]] = []
        self.spawn_timer = 0
        self.active = True

    def update(self):
        """Update sparkles."""
        self.spawn_timer += 1

        # Spawn new sparkle
        if self.spawn_timer % 5 == 0:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2)
            self.sparkles.append(
                {
                    "x": self.pos[0],
                    "y": self.pos[1],
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 30,
                    "max_life": 30,
                    "size": random.randint(2, 4),
                    "color": random.choice(
                        [NEON_YELLOW, NEON_CYAN, NEON_PINK, NEON_GREEN]
                    ),
                }
            )

        # Update existing sparkles
        for sparkle in self.sparkles[:]:
            sparkle["x"] += sparkle["vx"]
            sparkle["y"] += sparkle["vy"]
            sparkle["life"] -= 1

            if sparkle["life"] <= 0:
                self.sparkles.remove(sparkle)

    def draw(self, surface: pygame.Surface):
        """Draw sparkles."""
        for sparkle in self.sparkles:
            alpha = int(255 * (sparkle["life"] / sparkle["max_life"]))

            # Draw star shape
            cx, cy = int(sparkle["x"]), int(sparkle["y"])
            size = sparkle["size"]

            # Four-pointed star
            points = [
                (cx, cy - size),
                (cx + size // 2, cy - size // 2),
                (cx + size, cy),
                (cx + size // 2, cy + size // 2),
                (cx, cy + size),
                (cx - size // 2, cy + size // 2),
                (cx - size, cy),
                (cx - size // 2, cy - size // 2),
            ]

            # Draw with glow
            temp_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(temp_surf, (*sparkle["color"], alpha), points)
            surface.blit(temp_surf, (0, 0))


# Preset color schemes for different game elements
NEON_COLORS = {
    "player": NEON_GREEN,
    "enemy": NEON_RED,
    "elite_enemy": NEON_PURPLE,
    "bullet": NEON_YELLOW,
    "bonus": NEON_CYAN,
    "shield": NEON_PINK,
    "explosion": NEON_ORANGE,
}


def create_neon_surface(
    original_surface: pygame.Surface,
    color: tuple[int, int, int],
    glow_radius: int = 5,
) -> pygame.Surface:
    """Apply neon glow effect to a surface."""
    # Create a larger surface for the glow
    width = original_surface.get_width() + glow_radius * 4
    height = original_surface.get_height() + glow_radius * 4
    neon_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Create colored version of the original
    colored = original_surface.copy()
    colored.fill(color, special_flags=pygame.BLEND_MULT)

    # Draw glow layers
    for i in range(glow_radius):
        alpha = int(100 * (1 - i / glow_radius))
        glow_color = (*color, alpha)

        # Scale the surface for glow
        scale_factor = 1 + (i * 0.1)
        scaled = pygame.transform.smoothscale(
            colored,
            (
                int(colored.get_width() * scale_factor),
                int(colored.get_height() * scale_factor),
            ),
        )

        # Tint with glow color
        tinted = scaled.copy()
        tinted.fill(glow_color, special_flags=pygame.BLEND_MULT)

        # Center on the neon surface
        pos = (
            (width - scaled.get_width()) // 2,
            (height - scaled.get_height()) // 2,
        )
        neon_surface.blit(tinted, pos)

    # Draw the core
    core_pos = (
        (width - original_surface.get_width()) // 2,
        (height - original_surface.get_height()) // 2,
    )
    neon_surface.blit(colored, core_pos)

    return neon_surface
