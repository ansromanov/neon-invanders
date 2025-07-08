"""Performance optimization utilities for the game."""

from collections import deque
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .entities import Bullet, Explosion


class BulletPool:
    """Object pool for bullet sprites to reduce allocation overhead."""

    def __init__(self, pool_size: int = 100):
        self.pool_size = pool_size
        self.available: deque[Bullet] = deque()
        self.active: set[Bullet] = set()

    def get_bullet(self, bullet_class, *args, **kwargs) -> "Bullet":
        """Get a bullet from the pool or create a new one."""
        # Try to reuse an available bullet
        while self.available:
            bullet = self.available.popleft()
            if isinstance(bullet, bullet_class):
                # Reinitialize the bullet with new parameters
                # Reset the bullet state instead of calling __init__
                bullet.rect.centerx = args[0]
                bullet.rect.centery = args[1]
                bullet.speed = args[2]
                bullet.owner = args[3]
                # Reset optional attributes
                bullet.x_velocity = 0
                bullet.x_direction = 0
                self.active.add(bullet)
                return bullet  # type: ignore[no-any-return]
            # Put it back if it's not the right type
            self.available.append(bullet)
            break

        # Create a new bullet if none available
        bullet = bullet_class(*args, **kwargs)
        self.active.add(bullet)
        return bullet  # type: ignore[no-any-return]

    def release_bullet(self, bullet: "Bullet") -> None:
        """Return a bullet to the pool."""
        if bullet in self.active:
            self.active.remove(bullet)
            if len(self.available) < self.pool_size:
                self.available.append(bullet)
                # Reset the bullet's groups
                bullet.kill()


class ExplosionPool:
    """Object pool for explosion sprites."""

    def __init__(self, pool_size: int = 50):
        self.pool_size = pool_size
        self.available: deque[Explosion] = deque()
        self.active: set[Explosion] = set()

    def get_explosion(self, explosion_class, *args, **kwargs) -> "Explosion":
        """Get an explosion from the pool or create a new one."""
        if self.available:
            explosion = self.available.popleft()
            # Reset explosion state instead of calling __init__
            explosion.rect.centerx = args[0]
            explosion.rect.centery = args[1]
            explosion.current_frame = 0
            explosion.animation_counter = 0
            explosion.image = explosion.frames[0]
            self.active.add(explosion)
            return explosion

        # Create new explosion if none available
        explosion = explosion_class(*args, **kwargs)
        self.active.add(explosion)
        return explosion  # type: ignore[no-any-return]

    def release_explosion(self, explosion: "Explosion") -> None:
        """Return an explosion to the pool."""
        if explosion in self.active:
            self.active.remove(explosion)
            if len(self.available) < self.pool_size:
                self.available.append(explosion)
                explosion.kill()


class OptimizedGroup(pygame.sprite.Group):
    """Optimized sprite group with spatial partitioning for collision detection."""

    def __init__(self, *sprites):
        super().__init__(*sprites)
        self.grid_size = 100  # Size of each grid cell
        self.grid = {}

    def add(self, *sprites):
        """Add sprites and update grid."""
        super().add(*sprites)
        for sprite in sprites:
            self._add_to_grid(sprite)

    def remove(self, *sprites):
        """Remove sprites and update grid."""
        super().remove(*sprites)
        for sprite in sprites:
            self._remove_from_grid(sprite)

    def _get_grid_key(self, rect):
        """Get grid cell key for a rect."""
        return (rect.centerx // self.grid_size, rect.centery // self.grid_size)

    def _add_to_grid(self, sprite):
        """Add sprite to spatial grid."""
        if hasattr(sprite, "rect"):
            key = self._get_grid_key(sprite.rect)
            if key not in self.grid:
                self.grid[key] = set()
            self.grid[key].add(sprite)

    def _remove_from_grid(self, sprite):
        """Remove sprite from spatial grid."""
        if hasattr(sprite, "rect"):
            key = self._get_grid_key(sprite.rect)
            if key in self.grid:
                self.grid[key].discard(sprite)
                if not self.grid[key]:
                    del self.grid[key]

    def update(self, *args):
        """Update sprites and maintain grid."""
        # Store old positions
        old_positions = {}
        for sprite in self.sprites():
            if hasattr(sprite, "rect"):
                old_positions[sprite] = self._get_grid_key(sprite.rect)

        # Update sprites
        super().update(*args)

        # Update grid for moved sprites
        for sprite in self.sprites():
            if hasattr(sprite, "rect") and sprite in old_positions:
                new_key = self._get_grid_key(sprite.rect)
                old_key = old_positions[sprite]
                if new_key != old_key:
                    self._remove_from_grid(sprite)
                    self._add_to_grid(sprite)

    def get_sprites_near(self, rect, radius=1):
        """Get sprites in nearby grid cells."""
        center_key = self._get_grid_key(rect)
        nearby_sprites = set()

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                key = (center_key[0] + dx, center_key[1] + dy)
                if key in self.grid:
                    nearby_sprites.update(self.grid[key])

        return list(nearby_sprites)


class DirtySprite(pygame.sprite.Sprite):
    """Sprite that tracks if it needs redrawing."""

    def __init__(self):
        super().__init__()
        self.dirty = 1  # 0 = clean, 1 = dirty, 2 = always dirty
        self._old_rect = None

    def update(self, *args):
        """Update sprite and mark as dirty if moved."""
        if hasattr(self, "rect"):
            self._old_rect = self.rect.copy()
        super().update(*args)
        if hasattr(self, "rect") and self._old_rect and self.rect != self._old_rect:
            self.dirty = 1


# Global object pools
bullet_pool = BulletPool(pool_size=200)
explosion_pool = ExplosionPool(pool_size=100)
