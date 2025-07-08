"""Performance optimizations for the game."""

import random
from typing import TypedDict

import pygame


class RenderCache:
    """Cache for pre-rendered surfaces to avoid repeated rendering."""

    def __init__(self) -> None:
        self.cache: dict[str, pygame.Surface] = {}
        self.glow_cache: dict[tuple[tuple[int, int, int], int], pygame.Surface] = {}

    def get_glow_surface(
        self, color: tuple[int, int, int], radius: int
    ) -> pygame.Surface:
        """Get or create a cached glow surface."""
        key = (color, radius)
        if key not in self.glow_cache:
            size = radius * 4
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            center = size // 2

            # Create glow with fewer layers for performance
            for i in range(0, radius, 2):  # Skip every other layer
                alpha = int(255 * (1 - i / radius) * 0.2)  # Reduced alpha
                r = radius - i
                glow_color = (*color, alpha)
                pygame.draw.circle(surface, glow_color, (center, center), r)

            self.glow_cache[key] = surface

        return self.glow_cache[key]

    def clear(self) -> None:
        """Clear all caches."""
        self.cache.clear()
        self.glow_cache.clear()


class OptimizedStarField:
    """Optimized starfield with pre-rendered stars."""

    def __init__(self, star_count: int):
        self.stars = []
        self.star_surface = pygame.Surface((800, 600), pygame.SRCALPHA)

        # Pre-render star sprites
        self.star_sprites = []
        for size in range(1, 4):
            surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            # Simple star without expensive glow
            pygame.draw.circle(surface, (100, 200, 200), (size * 2, size * 2), size)
            self.star_sprites.append(surface)

        # Initialize stars
        import random

        for _ in range(star_count):
            self.stars.append(
                {
                    "x": random.randint(0, 800),
                    "y": random.randint(0, 600),
                    "speed": random.uniform(0.5, 2),
                    "sprite_idx": random.randint(0, 2),
                    "brightness": random.uniform(0.5, 1.0),
                }
            )

    def update(self) -> None:
        """Update star positions."""
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > 600:
                star["y"] = 0
                star["x"] = random.randint(0, 800)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw stars efficiently."""
        self.star_surface.fill((0, 0, 0, 0))

        for star in self.stars:
            sprite = self.star_sprites[int(star["sprite_idx"])]
            # Apply brightness without creating new surface
            pos = (
                int(star["x"]) - sprite.get_width() // 2,
                int(star["y"]) - sprite.get_height() // 2,
            )
            self.star_surface.blit(sprite, pos)

        surface.blit(self.star_surface, (0, 0))


class Particle(TypedDict):
    active: bool
    x: float
    y: float
    vx: float
    vy: float
    life: int
    max_life: int
    color: tuple[int, int, int]
    size: int


class ParticlePool:
    """Efficient particle system with object pooling."""

    def __init__(self, max_particles: int = 200):
        self.particles: list[Particle] = []
        self.active_count = 0
        self.max_particles = max_particles

        # Pre-allocate particles
        for _ in range(max_particles):
            self.particles.append(
                Particle(
                    active=False,
                    x=0.0,
                    y=0.0,
                    vx=0.0,
                    vy=0.0,
                    life=0,
                    max_life=30,
                    color=(255, 255, 255),
                    size=2,
                )
            )

    def emit(self, x: float, y: float, count: int, color: tuple[int, int, int]) -> None:
        """Emit particles from pool."""
        import math
        import random

        emitted = 0
        for particle in self.particles:
            if not particle["active"] and emitted < count:
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 3)

                particle["active"] = True
                particle["x"] = x
                particle["y"] = y
                particle["vx"] = math.cos(angle) * speed
                particle["vy"] = math.sin(angle) * speed
                particle["life"] = particle["max_life"]
                particle["color"] = color
                particle["size"] = random.randint(1, 3)

                emitted += 1
                self.active_count += 1

                if emitted >= count:
                    break

    def update(self) -> None:
        """Update active particles."""
        for particle in self.particles:
            if particle["active"]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["vy"] += 0.1  # Gravity
                particle["life"] -= 1

                if particle["life"] <= 0:
                    particle["active"] = False
                    self.active_count -= 1

    def draw(self, surface: pygame.Surface) -> None:
        """Draw particles efficiently."""
        for particle in self.particles:
            if particle["active"]:
                alpha = float(particle["life"]) / float(particle["max_life"])
                # Draw simple circles without glow
                color = (
                    particle["color"][0],
                    particle["color"][1],
                    particle["color"][2],
                    int(alpha * 150),
                )
                pos = (int(particle["x"]), int(particle["y"]))

                # Use pygame.gfxdraw for antialiased circles (faster)
                try:
                    import pygame.gfxdraw

                    pygame.gfxdraw.filled_circle(
                        surface, pos[0], pos[1], int(particle["size"]), color
                    )
                except:
                    pygame.draw.circle(surface, color[:3], pos, int(particle["size"]))


class FastNeonEffect:
    """Optimized neon effects using cached surfaces."""

    def __init__(self, cache: RenderCache):
        self.cache = cache

    def draw_fast_glow_line(
        self,
        surface: pygame.Surface,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        width: int = 2,
    ):
        """Draw line with simple glow effect."""
        # Draw just one glow layer
        glow_color = (*color, 50)
        pygame.draw.line(surface, glow_color, start, end, width + 4)
        # Draw core
        pygame.draw.line(surface, color, start, end, width)

    def draw_fast_glow_circle(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
    ):
        """Draw circle with cached glow."""
        glow_surf = self.cache.get_glow_surface(color, radius + 5)
        surface.blit(
            glow_surf,
            (
                center[0] - glow_surf.get_width() // 2,
                center[1] - glow_surf.get_height() // 2,
            ),
        )
        pygame.draw.circle(surface, color, center, radius)


# Global instances
render_cache = RenderCache()
particle_pool = ParticlePool(max_particles=150)  # Reduced particle count
fast_neon = FastNeonEffect(render_cache)
