"""Optimized game with performance improvements."""

import random

import pygame

from .config import (
    BONUS_SPAWN_CHANCE,
    ENEMY_SCORE,
    NEON_CYAN,
    NEON_GREEN,
    NEON_GRID_ENABLED,
    NEON_ORANGE,
    NEON_PURPLE,
    NEON_RED,
    PLAYER_TRAIL_ENABLED,
    PLAYER_TRAIL_LENGTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STAR_COUNT,
    STARS_ENABLED,
    WAVE_CLEAR_BONUS,
    GameState,
)
from .entities import Bonus
from .game import Game
from .neon_effects import (
    NeonGrid,
    NeonTrail,
    RainbowPulse,
    SparkleEffect,
)
from .performance_optimizations import (
    OptimizedStarField,
    fast_neon,
    particle_pool,
)
from .sounds import sound_manager


class OptimizedNeonGrid(NeonGrid):
    """Optimized neon grid with cached rendering."""

    def __init__(
        self,
        grid_size: int = 50,
        color: tuple[int, int, int] = NEON_CYAN,
        alpha: int = 30,
    ):
        super().__init__(grid_size, color, alpha)
        self.grid_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.needs_redraw = True

    def update(self):
        """Update grid animation."""
        super().update()
        self.needs_redraw = True

    def draw(self, surface: pygame.Surface):
        """Draw the animated grid with caching."""
        if self.needs_redraw:
            self.grid_surface.fill((0, 0, 0, 0))

            # Draw vertical lines
            for x in range(0, SCREEN_WIDTH + self.grid_size, self.grid_size):
                pygame.draw.line(
                    self.grid_surface,
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
                        self.grid_surface,
                        self.color,
                        (0, adjusted_y),
                        (SCREEN_WIDTH, adjusted_y),
                        1,
                    )

            self.needs_redraw = False

        surface.blit(self.grid_surface, (0, 0))


class OptimizedNeonTrail(NeonTrail):
    """Optimized trail with reduced rendering."""

    def draw(self, surface: pygame.Surface):
        """Draw the neon trail efficiently."""
        if len(self.trail_points) < 2:
            return

        # Draw trail as a single line strip with varying width
        points = list(self.trail_points)

        for i in range(1, len(points)):
            alpha = int(180 * (i / len(points)))
            width = max(1, int(2 * (i / len(points))))

            # Simple line without multiple glow layers
            color = (*self.color, alpha)
            pygame.draw.line(surface, color[:3], points[i - 1], points[i], width)


class OptimizedGame(Game):
    """Game class with performance optimizations."""

    def __init__(self):
        """Initialize with optimized components."""
        super().__init__()

        # Replace visual effects with optimized versions
        if STARS_ENABLED:
            self.starfield = OptimizedStarField(
                min(STAR_COUNT, 10)
            )  # Reduce star count

        if NEON_GRID_ENABLED:
            self.neon_grid = OptimizedNeonGrid(
                80, NEON_PURPLE, 15
            )  # Larger grid, less lines

        if PLAYER_TRAIL_ENABLED:
            self.player_trail = OptimizedNeonTrail(
                NEON_GREEN, min(PLAYER_TRAIL_LENGTH, 8)
            )

        # Limit visual effects
        self.max_rainbow_pulses = 3
        self.max_sparkle_effects = 5

        # Frame skip for expensive effects
        self.effect_frame_skip = 0

    def _update_visual_effects(self):
        """Update visual effects with frame skipping."""
        self.effect_frame_skip = (self.effect_frame_skip + 1) % 2

        if self.starfield:
            self.starfield.update()
        if self.neon_grid and self.effect_frame_skip == 0:
            self.neon_grid.update()

        self.menu_heartbeat.update()

        # Update rainbow pulses with limit
        for pulse in self.rainbow_pulses[:]:
            pulse.update()
            if not pulse.active:
                self.rainbow_pulses.remove(pulse)

        # Limit rainbow pulses
        if len(self.rainbow_pulses) > self.max_rainbow_pulses:
            self.rainbow_pulses = self.rainbow_pulses[-self.max_rainbow_pulses :]

        # Update sparkle effects with limit
        for sparkle in self.sparkle_effects[:]:
            if self.effect_frame_skip == 0:
                sparkle.update()
            if not sparkle.active:
                self.sparkle_effects.remove(sparkle)

        # Limit sparkle effects
        if len(self.sparkle_effects) > self.max_sparkle_effects:
            self.sparkle_effects = self.sparkle_effects[-self.max_sparkle_effects :]

    def check_collisions(self):
        """Check collisions with optimized particle effects."""
        # Player bullets hitting enemies
        for bullet in self.player_bullets:
            hit_enemies = pygame.sprite.spritecollide(
                bullet, self.enemy_group.enemies, True
            )
            if hit_enemies:
                bullet.kill()
                for enemy in hit_enemies:
                    if self.player:
                        self.player.score += ENEMY_SCORE
                    # Register kill for combo system
                    self.hud.register_kill()

                    # Use optimized particle pool
                    if self.particles_enabled:
                        particle_pool.emit(
                            enemy.rect.centerx, enemy.rect.centery, 5, NEON_ORANGE
                        )

                    # Play explosion sound
                    sound_manager.play("explosion")

                    # Chance to spawn bonus
                    if random.random() < BONUS_SPAWN_CHANCE:
                        bonus = Bonus(enemy.rect.centerx, enemy.rect.centery)
                        self.bonuses.add(bonus)
                        self.all_sprites.add(bonus)
                        # Limit sparkle effects
                        if (
                            self.particles_enabled
                            and len(self.sparkle_effects) < self.max_sparkle_effects
                        ):
                            self.sparkle_effects.append(
                                SparkleEffect((bonus.rect.centerx, bonus.rect.centery))
                            )

        # Enemy bullets hitting player
        if self.player:
            hit_player = pygame.sprite.spritecollide(
                self.player, self.enemy_bullets, True
            )
            if hit_player:
                if self.player.shield_active:
                    # Play shield hit sound
                    sound_manager.play("shield_hit")
                else:
                    # Play explosion sound
                    sound_manager.play("explosion")
                self.player.hit()

                # Use optimized particle pool
                if self.particles_enabled:
                    particle_pool.emit(
                        self.player.rect.centerx, self.player.rect.centery, 8, NEON_RED
                    )

        # Player collecting bonuses
        if self.player:
            collected_bonuses = pygame.sprite.spritecollide(
                self.player, self.bonuses, True
            )
            for bonus in collected_bonuses:
                self.apply_bonus_effect(bonus.shape_type)
                # Play bonus collection sound
                sound_manager.play("bonus_collect")
                # Add rainbow pulse with limit
                if (
                    self.particles_enabled
                    and len(self.rainbow_pulses) < self.max_rainbow_pulses
                ):
                    self.rainbow_pulses.append(
                        RainbowPulse((bonus.rect.centerx, bonus.rect.centery))
                    )

    def draw_game(self):
        """Draw game with optimized rendering."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw starfield if enabled
        if self.starfield:
            self.starfield.draw(self.screen)

        # Draw player trail if enabled
        if self.player_trail:
            self.player_trail.draw(self.screen)

        # Draw all sprites
        self.all_sprites.draw(self.screen)

        # Draw shield with optimized glow
        if self.player and self.player.shield_active:
            fast_neon.draw_fast_glow_circle(
                self.screen,
                (self.player.rect.centerx, self.player.rect.centery),
                35,
                NEON_CYAN,
            )

        # Update and draw particle pool
        if self.particles_enabled:
            particle_pool.update()
            particle_pool.draw(self.screen)

            # Draw rainbow pulses
            for pulse in self.rainbow_pulses:
                pulse.draw(self.screen)

            # Draw sparkle effects
            for sparkle in self.sparkle_effects:
                sparkle.draw(self.screen)

        # Draw HUD elements
        self.hud.render()

        # Draw hearts for lives
        if self.player:
            self.hud.render_hearts(self.player.lives)

        # Draw minimap
        self.minimap.render(self.enemy_group, self.player)

        # Draw FPS if enabled
        if self.show_fps:
            fps_text = self.font.render(
                f"FPS: {int(self.clock.get_fps())}", True, NEON_ORANGE
            )
            self.screen.blit(fps_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))

    def _handle_wave_clear(self):
        """Handle wave clear with limited particles."""
        self.state = GameState.WAVE_CLEAR
        self.player.score += WAVE_CLEAR_BONUS
        sound_manager.play("wave_clear")

        # Add limited celebration sparkles
        if self.particles_enabled:
            for _ in range(min(3, self.max_sparkle_effects)):
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(100, SCREEN_HEIGHT - 100)
                if len(self.sparkle_effects) < self.max_sparkle_effects:
                    self.sparkle_effects.append(SparkleEffect((x, y)))
