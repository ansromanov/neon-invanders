"""Enhanced HUD (Heads-Up Display) system with animations and visual effects."""

import math

import pygame

from .config import (
    NEON_CYAN,
    NEON_GREEN,
    NEON_ORANGE,
    NEON_PINK,
    NEON_PURPLE,
    NEON_RED,
    NEON_YELLOW,
    RAPID_FIRE_DURATION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DURATION,
)
from .sprites import sprite_cache


class AnimatedText:
    """Text that can animate with various effects."""

    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple,
        pos: tuple,
        align: str = "center",
    ):
        self.text = text
        self.font = font
        self.base_color = color
        self.color = color
        self.pos = pos
        self.base_pos = pos
        self.animation_time = 0
        self.scale = 1.0
        self.alpha = 255
        self.effect: str | None = None
        self.effect_duration = 0
        self.effect_start_time = 0
        self.align = align  # "center" or "left"

    def start_effect(self, effect: str, duration: int = 1000):
        """Start an animation effect."""
        self.effect = effect
        self.effect_duration = duration
        self.effect_start_time = pygame.time.get_ticks()

    def update(self):
        """Update animation state."""
        if not self.effect:
            return

        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.effect_start_time
        progress = min(elapsed / self.effect_duration, 1.0)

        if self.effect == "pulse":
            # Pulsing scale effect
            self.scale = 1.0 + 0.2 * math.sin(elapsed * 0.01)
        elif self.effect == "bounce":
            # Bouncing position effect
            bounce = abs(math.sin(elapsed * 0.005)) * 10
            self.pos = (self.base_pos[0], self.base_pos[1] - bounce)
        elif self.effect == "flash":
            # Flashing color effect
            if int(elapsed / 100) % 2 == 0:
                self.color = NEON_YELLOW
            else:
                self.color = self.base_color
        elif self.effect == "fade_in":
            # Fade in effect
            self.alpha = int(255 * progress)
        elif self.effect == "slide_in":
            # Slide in from left
            offset = (1.0 - progress) * 100
            self.pos = (self.base_pos[0] - offset, self.base_pos[1])

        if progress >= 1.0:
            self.effect = None
            self.scale = 1.0
            self.alpha = 255
            self.pos = self.base_pos
            self.color = self.base_color

    def render(self, screen: pygame.Surface):
        """Render the animated text."""
        text_surface = self.font.render(self.text, True, self.color)

        if self.scale != 1.0:
            width = int(text_surface.get_width() * self.scale)
            height = int(text_surface.get_height() * self.scale)
            text_surface = pygame.transform.scale(text_surface, (width, height))

        if self.alpha < 255:
            text_surface.set_alpha(self.alpha)

        if self.align == "left":
            rect = text_surface.get_rect(topleft=self.pos)
        else:
            rect = text_surface.get_rect(center=self.pos)
        screen.blit(text_surface, rect)


class HUD:
    """Enhanced HUD system with visual improvements."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)

        # HUD elements with animation support
        self.score_text = AnimatedText(
            "Score: 0", self.font, NEON_GREEN, (20, 10), align="left"
        )
        self.wave_text = AnimatedText(
            "Wave: 1", self.font, NEON_YELLOW, (SCREEN_WIDTH - 100, 30)
        )

        # Bonus indicators
        self.bonus_indicators: list[dict] = []

        # Score change animation
        self.score_change_texts: list[tuple] = []
        self.last_score = 0

        # Wave transition
        self.wave_transition_text: AnimatedText | None = None

        # Combo system
        self.combo_count = 0
        self.combo_timer = 0
        self.last_kill_time = 0

    def update(self, player, wave: int, enemy_group):  # noqa: ARG002
        """Update HUD elements."""
        # Update score with animation
        if player and player.score != self.last_score:
            score_diff = player.score - self.last_score
            self.last_score = player.score
            self.score_text.text = f"Score: {player.score}"
            self.score_text.start_effect("pulse", 500)

            # Add floating score change
            self.add_score_change(score_diff)

        # Update wave
        self.wave_text.text = f"Wave: {wave}"

        # Update animations
        self.score_text.update()
        self.wave_text.update()

        # Update floating score texts
        current_time = pygame.time.get_ticks()
        self.score_change_texts = [
            (text, pos, start_time, value)
            for text, pos, start_time, value in self.score_change_texts
            if current_time - start_time < 2000
        ]

        # Update combo timer
        if current_time - self.last_kill_time > 2000:
            self.combo_count = 0

        # Update bonus indicators
        self.update_bonus_indicators(player)

    def add_score_change(self, value: int):
        """Add a floating score change indicator."""
        if value > 0:
            text = f"+{value}"
            color = NEON_GREEN
        else:
            text = str(value)
            color = NEON_RED

        surface = self.small_font.render(text, True, color)
        pos = [20, 55]  # Position score changes below the score text
        self.score_change_texts.append((surface, pos, pygame.time.get_ticks(), value))

    def register_kill(self):
        """Register an enemy kill for combo tracking."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_kill_time < 2000:  # 2 second combo window
            self.combo_count += 1
        else:
            self.combo_count = 1
        self.last_kill_time = current_time

    def update_bonus_indicators(self, player):
        """Update active bonus indicators."""
        self.bonus_indicators.clear()

        if not player:
            return

        y_offset = 70
        current_time = pygame.time.get_ticks()

        # Shield indicator
        if player.shield_active and current_time < player.shield_end_time:
            remaining = (player.shield_end_time - current_time) / 1000
            self.bonus_indicators.append(
                {
                    "icon": "shield",
                    "text": f"Shield: {remaining:.1f}s",
                    "color": NEON_CYAN,
                    "pos": (20, y_offset),
                    "progress": remaining / (SHIELD_DURATION / 1000),
                }
            )
            y_offset += 35

        # Rapid fire indicator
        if player.rapid_fire_active and current_time < player.rapid_fire_end_time:
            remaining = (player.rapid_fire_end_time - current_time) / 1000
            self.bonus_indicators.append(
                {
                    "icon": "rapid",
                    "text": f"Rapid Fire: {remaining:.1f}s",
                    "color": NEON_GREEN,
                    "pos": (20, y_offset),
                    "progress": remaining / (RAPID_FIRE_DURATION / 1000),
                }
            )
            y_offset += 35

        # Triple shot indicator
        if player.triple_shot_active:
            self.bonus_indicators.append(
                {
                    "icon": "triple",
                    "text": "Triple Shot Ready!",
                    "color": NEON_PURPLE,
                    "pos": (20, y_offset),
                    "progress": 1.0,
                }
            )
            y_offset += 35

    def show_wave_transition(self, wave: int):
        """Show wave transition animation."""
        self.wave_transition_text = AnimatedText(
            f"WAVE {wave}",
            self.big_font,
            NEON_YELLOW,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        )
        self.wave_transition_text.start_effect("fade_in", 1000)

    def render(self):
        """Render all HUD elements."""
        # Draw main HUD elements
        self.score_text.render(self.screen)
        self.wave_text.render(self.screen)

        # Draw floating score changes
        current_time = pygame.time.get_ticks()
        for text_surface, pos, start_time, _value in self.score_change_texts:
            age = current_time - start_time
            # Float upward and fade out
            pos[1] -= 1
            alpha = max(0, 255 - (age / 2000) * 255)
            text_surface.set_alpha(int(alpha))
            self.screen.blit(text_surface, pos)

        # Draw combo indicator
        if self.combo_count > 1:
            combo_text = self.font.render(
                f"COMBO x{self.combo_count}!", True, NEON_ORANGE
            )
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(combo_text, combo_rect)

        # Draw bonus indicators with progress bars
        for indicator in self.bonus_indicators:
            # Draw icon or text
            text = self.small_font.render(indicator["text"], True, indicator["color"])
            self.screen.blit(text, indicator["pos"])

            # Draw progress bar
            bar_width = 100
            bar_height = 4
            bar_x = indicator["pos"][0]
            bar_y = indicator["pos"][1] + 25

            # Background
            pygame.draw.rect(
                self.screen,
                (*indicator["color"], 64),
                (bar_x, bar_y, bar_width, bar_height),
            )
            # Progress
            pygame.draw.rect(
                self.screen,
                indicator["color"],
                (bar_x, bar_y, int(bar_width * indicator["progress"]), bar_height),
            )

        # Draw wave transition if active
        if self.wave_transition_text:
            self.wave_transition_text.update()
            self.wave_transition_text.render(self.screen)
            if not self.wave_transition_text.effect:
                self.wave_transition_text = None

    def render_hearts(self, lives: int):
        """Render heart icons for lives display."""
        heart_sprite = sprite_cache.get("heart")
        if heart_sprite:
            for i in range(lives):
                self.screen.blit(heart_sprite, (20 + i * 25, 50))


class MinimapHUD:
    """Mini radar showing enemy positions."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = 120  # 20% smaller (150 * 0.8)
        self.height = 80  # 20% smaller (100 * 0.8)
        self.x = SCREEN_WIDTH - self.width - 10
        self.y = SCREEN_HEIGHT - self.height - 10  # Bottom right

    def render(self, enemy_group, player):
        """Render the minimap."""
        # Create a surface with per-pixel alpha for transparency
        minimap_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background with 50% transparency
        pygame.draw.rect(
            minimap_surface, (*NEON_CYAN, 16), (0, 0, self.width, self.height)
        )
        pygame.draw.rect(
            minimap_surface, (*NEON_CYAN, 128), (0, 0, self.width, self.height), 2
        )

        # Scale factors
        scale_x = self.width / SCREEN_WIDTH
        scale_y = self.height / SCREEN_HEIGHT

        # Draw enemies
        for enemy in enemy_group.enemies:
            x = int(enemy.rect.centerx * scale_x)
            y = int(enemy.rect.centery * scale_y)
            color = (*NEON_RED, 200) if enemy.is_elite else (*NEON_PINK, 200)
            pygame.draw.circle(minimap_surface, color, (x, y), 2)

        # Draw player
        if player:
            x = int(player.rect.centerx * scale_x)
            y = int(player.rect.centery * scale_y)
            pygame.draw.circle(minimap_surface, (*NEON_GREEN, 255), (x, y), 3)

        # Blit the minimap surface with transparency
        self.screen.blit(minimap_surface, (self.x, self.y))
