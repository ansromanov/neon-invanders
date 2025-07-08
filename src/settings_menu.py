"""Enhanced settings menu with improved layout and visual effects."""

from typing import Any

import pygame

from .config import (
    NEON_CYAN,
    NEON_GREEN,
    NEON_PINK,
    NEON_PURPLE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    GameState,
)
from .neon_effects import NeonEffect, NeonText
from .sounds import sound_manager


class SettingsMenu:
    """Enhanced settings menu with categories and visual improvements."""

    def __init__(self, screen: pygame.Surface, game):
        self.screen = screen
        self.game = game
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 72)

        # Visual effects
        self.neon_effect = NeonEffect(NEON_CYAN)

        # Categories
        self.categories: list[dict[str, Any]] = [
            {
                "name": "Audio",
                "color": NEON_CYAN,
                "settings": [
                    {
                        "name": "Sound",
                        "type": "toggle",
                        "value_getter": lambda: self.game.sound_enabled,
                    },
                    {
                        "name": "Music",
                        "type": "toggle",
                        "value_getter": lambda: self.game.music_enabled,
                    },
                    {
                        "name": "Volume",
                        "type": "slider",
                        "value_getter": lambda: self.game.sound_volume,
                    },
                ],
            },
            {
                "name": "Display",
                "color": NEON_PURPLE,
                "settings": [
                    {
                        "name": "Show FPS",
                        "type": "toggle",
                        "value_getter": lambda: self.game.show_fps,
                    },
                    {
                        "name": "Particles",
                        "type": "toggle",
                        "value_getter": lambda: self.game.particles_enabled,
                    },
                ],
            },
            {
                "name": "Gameplay",
                "color": NEON_GREEN,
                "settings": [
                    {
                        "name": "Difficulty",
                        "type": "choice",
                        "value_getter": lambda: self.game.difficulty,
                        "choices": ["Easy", "Normal", "Hard"],
                    },
                ],
            },
        ]

        # Flatten settings for navigation
        self.all_settings: list[dict[str, Any]] = []
        for category in self.categories:
            for setting in category["settings"]:
                # Create a copy of the setting to avoid modifying the original
                setting_copy = dict(setting)  # Use dict() to create a copy
                setting_copy["category"] = category["name"]
                setting_copy["category_color"] = category["color"]
                self.all_settings.append(setting_copy)

        self.selected_index = 0
        self.animation_offset = 0
        self.pulse_timer = 0

        # Scrolling support
        self.scroll_offset = 0
        self.visible_area_top = 140  # Below title
        self.visible_area_bottom = SCREEN_HEIGHT - 100  # Above instructions
        self.visible_area_height = self.visible_area_bottom - self.visible_area_top

        # Calculate total content height
        self._calculate_content_height()

    def _calculate_content_height(self):
        """Calculate the total height of all settings content."""
        y_offset = 0
        current_category = None

        for category in self.categories:
            if current_category != category["name"]:
                current_category = category["name"]
                if y_offset > 0:
                    y_offset += 35  # Space for separator
                y_offset += 50  # Category header

            # Settings in this category
            y_offset += len(category["settings"]) * 70
            y_offset += 20  # Extra space between categories

        self.content_height = y_offset

    def handle_navigation(self, key):
        """Handle keyboard navigation in settings menu."""
        old_index = self.selected_index

        if key == pygame.K_UP:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == pygame.K_DOWN:
            self.selected_index = min(
                len(self.all_settings) - 1, self.selected_index + 1
            )
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:
            self.handle_value_change(key)

        # Update scroll position if selection changed
        if old_index != self.selected_index:
            self._update_scroll_for_selection()

    def _update_scroll_for_selection(self):
        """Update scroll position to keep selected item visible."""
        # Calculate y position of selected item
        y_offset = 0
        current_category = None
        setting_index = 0
        selected_y = 0

        for category in self.categories:
            if current_category != category["name"]:
                current_category = category["name"]
                if y_offset > 0:
                    y_offset += 35  # Space for separator
                y_offset += 50  # Category header

            for _setting in category["settings"]:
                if setting_index == self.selected_index:
                    selected_y = y_offset
                    break
                y_offset += 70
                setting_index += 1
            else:
                y_offset += 20  # Extra space between categories
                continue
            break

        # Calculate actual screen position
        screen_y = selected_y - self.scroll_offset

        # Adjust scroll if needed
        margin = 50
        if screen_y < margin:
            # Item is too high, scroll up
            self.scroll_offset = max(0, selected_y - margin)
        elif screen_y > self.visible_area_height - margin:
            # Item is too low, scroll down
            self.scroll_offset = min(
                max(0, self.content_height - self.visible_area_height),
                selected_y - self.visible_area_height + margin,
            )

    def handle_value_change(self, key):
        """Handle changing setting values."""
        setting = self.all_settings[self.selected_index]

        if setting["type"] == "toggle":
            if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                if setting["name"] == "Sound":
                    self.game.sound_enabled = not self.game.sound_enabled
                    sound_manager.sound_enabled = self.game.sound_enabled
                    if not self.game.sound_enabled:
                        sound_manager.stop_music()
                        self.game.music_enabled = False
                elif setting["name"] == "Music":
                    if (
                        self.game.sound_enabled
                    ):  # Only allow music toggle if sound is on
                        self.game.music_enabled = not self.game.music_enabled
                        if not self.game.music_enabled:
                            sound_manager.stop_music()
                        elif self.game.state == GameState.PLAYING:
                            theme = self.game.get_music_theme()
                            sound_manager.play_music(theme)
                elif setting["name"] == "Show FPS":
                    self.game.show_fps = not self.game.show_fps
                elif setting["name"] == "Particles":
                    self.game.particles_enabled = not self.game.particles_enabled

        elif setting["type"] == "slider":
            if setting["name"] == "Volume":
                if key == pygame.K_LEFT and self.game.sound_volume > 0:
                    self.game.sound_volume = max(0, self.game.sound_volume - 0.1)
                elif key == pygame.K_RIGHT and self.game.sound_volume < 1:
                    self.game.sound_volume = min(1, self.game.sound_volume + 0.1)
                # Update sound volumes
                for sound in sound_manager.sounds.values():
                    sound.set_volume(self.game.sound_volume)
                sound_manager.set_music_volume(self.game.sound_volume)

        elif setting["type"] == "choice" and setting["name"] == "Difficulty":
            choices = setting["choices"]
            current_idx = choices.index(self.game.difficulty)
            if key == pygame.K_LEFT:
                current_idx = (current_idx - 1) % len(choices)
            elif key == pygame.K_RIGHT:
                current_idx = (current_idx + 1) % len(choices)
            self.game.difficulty = choices[current_idx]

    def update(self):
        """Update animations."""
        self.pulse_timer += 0.1
        # Create a simple oscillation without using math.sin
        # This creates a smooth back-and-forth animation
        cycle = self.pulse_timer % (2 * 3.14159)  # Approximate 2*pi
        if cycle < 3.14159:
            self.animation_offset = (cycle / 3.14159) * 5
        else:
            self.animation_offset = ((2 * 3.14159 - cycle) / 3.14159) * 5

    def draw_slider(self, x, y, width, height, value, color, selected=False):
        """Draw a visual slider."""
        # Background track
        track_rect = pygame.Rect(x, y + height // 3, width, height // 3)
        pygame.draw.rect(
            self.screen, (*color, 50), track_rect, border_radius=height // 6
        )

        # Filled portion
        filled_width = int(width * value)
        if filled_width > 0:
            filled_rect = pygame.Rect(x, y + height // 3, filled_width, height // 3)
            pygame.draw.rect(self.screen, color, filled_rect, border_radius=height // 6)

        # Handle
        handle_x = x + filled_width
        handle_radius = height // 2
        if selected:
            # Glow effect for selected handle
            self.neon_effect.draw_glowing_circle(
                self.screen, (handle_x, y + height // 2), handle_radius + 3, 2
            )
        pygame.draw.circle(
            self.screen, color, (handle_x, y + height // 2), handle_radius
        )

        # Value text
        percent_text = f"{int(value * 100)}%"
        value_surface = self.small_font.render(percent_text, True, color)
        value_rect = value_surface.get_rect(center=(x + width // 2, y + height + 20))
        self.screen.blit(value_surface, value_rect)

    def draw_toggle(self, x, y, width, height, enabled, color, selected=False):
        """Draw a visual toggle switch."""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        bg_color = (*color, 100) if enabled else (*color, 30)
        pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=height // 2)

        # Border
        if selected:
            self.neon_effect.draw_glowing_rect(
                self.screen, bg_rect, 2, border_radius=height // 2
            )
        else:
            pygame.draw.rect(self.screen, color, bg_rect, 2, border_radius=height // 2)

        # Toggle circle
        circle_x = x + width - height // 2 - 5 if enabled else x + height // 2 + 5
        circle_y = y + height // 2
        circle_radius = height // 2 - 5

        if selected and enabled:
            # Glow for active selected toggle
            self.neon_effect.draw_glowing_circle(
                self.screen, (circle_x, circle_y), circle_radius + 2, 0
            )

        pygame.draw.circle(
            self.screen,
            color if enabled else (*color, 100),
            (circle_x, circle_y),
            circle_radius,
        )

        # Status text
        status_text = "ON" if enabled else "OFF"
        text_color = color if enabled else (*color, 100)
        status_surface = self.small_font.render(status_text, True, text_color)
        text_x = x + width + 20
        text_rect = status_surface.get_rect(midleft=(text_x, y + height // 2))
        self.screen.blit(status_surface, text_rect)

    def draw_choice_selector(
        self,
        x,
        y,
        choices,  # noqa: ARG002
        current_choice,
        color,
        selected=False,
    ):
        """Draw a choice selector with arrows."""
        # Current choice text
        choice_surface = self.font.render(current_choice, True, color)
        choice_rect = choice_surface.get_rect(center=(x, y))

        if selected:
            # Background highlight
            bg_rect = choice_rect.inflate(100, 20)
            pygame.draw.rect(self.screen, (*color, 30), bg_rect, border_radius=10)

        self.screen.blit(choice_surface, choice_rect)

        if selected:
            # Animated arrows
            arrow_offset = self.animation_offset

            # Left arrow
            left_arrow = self.font.render("◄", True, NEON_PINK)
            left_rect = left_arrow.get_rect(
                midright=(choice_rect.left - 20 - arrow_offset, y)
            )
            self.screen.blit(left_arrow, left_rect)

            # Right arrow
            right_arrow = self.font.render("►", True, NEON_PINK)
            right_rect = right_arrow.get_rect(
                midleft=(choice_rect.right + 20 + arrow_offset, y)
            )
            self.screen.blit(right_arrow, right_rect)

    def draw(self):
        """Draw the enhanced settings menu."""
        # Title with enhanced glow
        NeonText.draw_glowing_text(
            self.screen,
            "SETTINGS",
            self.big_font,
            (SCREEN_WIDTH // 2, 80),
            NEON_GREEN,
            glow_intensity=4,
        )

        # Create a clipping rect for the scrollable area
        clip_rect = pygame.Rect(
            0, self.visible_area_top, SCREEN_WIDTH, self.visible_area_height
        )
        self.screen.set_clip(clip_rect)

        # Draw categories and settings with scroll offset
        y_offset = self.visible_area_top - self.scroll_offset
        current_category = None
        setting_index = 0

        for category in self.categories:
            # Category header
            if current_category != category["name"]:
                current_category = category["name"]

                # Category separator line
                if y_offset > self.visible_area_top - self.scroll_offset:
                    line_y = y_offset - 15
                    # Only draw if visible
                    if self.visible_area_top <= line_y <= self.visible_area_bottom:
                        # Create a new NeonEffect for the category color
                        category_effect = NeonEffect(category["color"])
                        category_effect.draw_glowing_line(
                            self.screen,
                            (SCREEN_WIDTH // 4, line_y),
                            (3 * SCREEN_WIDTH // 4, line_y),
                            1,
                        )

                # Category name
                if (
                    self.visible_area_top - 50
                    <= y_offset
                    <= self.visible_area_bottom + 50
                ):
                    category_surface = self.font.render(
                        category["name"].upper(), True, category["color"]
                    )
                    category_rect = category_surface.get_rect(
                        center=(SCREEN_WIDTH // 2, y_offset)
                    )
                    self.screen.blit(category_surface, category_rect)
                y_offset += 50

            # Draw settings in this category
            for setting in category["settings"]:
                # Only draw if visible
                if (
                    self.visible_area_top - 100
                    <= y_offset
                    <= self.visible_area_bottom + 100
                ):
                    is_selected = setting_index == self.selected_index

                    # Setting name
                    name_color = (
                        category["color"] if is_selected else (*category["color"], 180)
                    )
                    name_surface = self.font.render(
                        setting["name"] + ":", True, name_color
                    )
                    name_rect = name_surface.get_rect(
                        midright=(SCREEN_WIDTH // 2 - 30, y_offset)
                    )
                    self.screen.blit(name_surface, name_rect)

                    # Setting value/control
                    control_x = SCREEN_WIDTH // 2 + 30

                    if setting["type"] == "toggle":
                        self.draw_toggle(
                            control_x,
                            y_offset - 15,
                            80,
                            30,
                            setting["value_getter"](),
                            category["color"],
                            is_selected,
                        )
                    elif setting["type"] == "slider":
                        self.draw_slider(
                            control_x,
                            y_offset - 20,
                            150,
                            40,
                            setting["value_getter"](),
                            category["color"],
                            is_selected,
                        )
                    elif setting["type"] == "choice":
                        self.draw_choice_selector(
                            control_x + 75,
                            y_offset,
                            setting["choices"],
                            setting["value_getter"](),
                            category["color"],
                            is_selected,
                        )

                y_offset += 70
                setting_index += 1

            y_offset += 20  # Extra space between categories

        # Remove clipping
        self.screen.set_clip(None)

        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            # Up arrow indicator
            up_arrow = self.font.render("▲", True, NEON_PURPLE)
            up_rect = up_arrow.get_rect(
                center=(SCREEN_WIDTH // 2, self.visible_area_top - 20)
            )
            self.screen.blit(up_arrow, up_rect)

        if self.scroll_offset < self.content_height - self.visible_area_height:
            # Down arrow indicator
            down_arrow = self.font.render("▼", True, NEON_PURPLE)
            down_rect = down_arrow.get_rect(
                center=(SCREEN_WIDTH // 2, self.visible_area_bottom + 20)
            )
            self.screen.blit(down_arrow, down_rect)

        # Instructions at bottom with better styling
        instruction_bg = pygame.Rect(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), instruction_bg)

        NeonText.draw_glowing_text(
            self.screen,
            "↑/↓ Navigate    ←/→ Change Value    ESC Back to Menu",
            self.small_font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50),
            NEON_PURPLE,
            glow_intensity=2,
        )
