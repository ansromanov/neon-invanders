"""Main game logic and state management."""

import json
import os
import random

import pygame

from .config import *
from .entities import (
    Bonus,
    EliteBullet,
    EnemyGroup,
    Explosion,
    Player,
    TripleShotBullet,
)
from .hud import HUD, MinimapHUD
from .neon_effects import (
    HeartBeat,
    NeonEffect,
    NeonGrid,
    NeonText,
    NeonTrail,
    RainbowPulse,
    SparkleEffect,
    StarField,
)
from .performance import OptimizedGroup, bullet_pool, explosion_pool
from .settings_menu import SettingsMenu
from .sounds import sound_manager


class Game:
    """Main game class managing states and game logic."""

    _instance = None

    def __init__(self):
        Game._instance = self
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)

        # Load and scale background image
        try:
            self.background = pygame.image.load("assets/background.png").convert()
            self.background = pygame.transform.scale(
                self.background, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except pygame.error:
            # If background.png doesn't exist, create a simple gradient background
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                color_value = int(20 + (y / SCREEN_HEIGHT) * 30)
                pygame.draw.line(
                    self.background,
                    (color_value, 0, color_value),
                    (0, y),
                    (SCREEN_WIDTH, y),
                )

        # Game state
        self.state = GameState.MENU
        self.running = True
        self.wave = 1
        self.high_score = self.load_high_score()

        # Sprite groups - use optimized groups for better collision detection
        self.all_sprites = pygame.sprite.Group()
        self.player_bullets = OptimizedGroup()
        self.enemy_bullets = OptimizedGroup()
        self.bonuses = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        # Game entities
        self.player = None
        self.enemy_group = EnemyGroup()

        # HUD systems
        self.hud = HUD(self.screen)
        self.minimap = MinimapHUD(self.screen)

        # Settings
        self.sound_enabled = SOUND_ENABLED
        self.sound_volume = SOUND_VOLUME
        self.music_enabled = MUSIC_ENABLED
        self.show_fps = False
        self.difficulty = "Normal"  # Easy, Normal, Hard
        self.particles_enabled = True  # Enable/disable particle effects

        # Settings menu
        self.settings_menu = SettingsMenu(self.screen, self)
        self.selected_setting = 0  # Keep for backward compatibility

        # Visual effects
        self.starfield = StarField(STAR_COUNT) if STARS_ENABLED else None
        self.neon_grid = NeonGrid(60, NEON_PURPLE, 20) if NEON_GRID_ENABLED else None
        self.rainbow_pulses = []  # For bonus collection effects
        self.sparkle_effects = []  # For various sparkle animations
        self.player_trail = (
            NeonTrail(NEON_GREEN, PLAYER_TRAIL_LENGTH) if PLAYER_TRAIL_ENABLED else None
        )
        self.menu_heartbeat = HeartBeat((SCREEN_WIDTH - 50, 50), NEON_RED)
        self.neon_effect = NeonEffect(NEON_CYAN)

    def load_high_score(self) -> int:
        """Load high score from file."""
        try:
            if os.path.exists("highscore.json"):
                with open("highscore.json") as f:
                    data = json.load(f)
                    score = data.get("high_score", 0)
                    return int(score) if isinstance(score, int | float) else 0
        except:
            pass
        return 0

    def save_high_score(self):
        """Save high score to file."""
        if self.player and self.player.score > self.high_score:
            self.high_score = self.player.score
            try:
                with open("highscore.json", "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except:
                pass

    def reset_game(self):
        """Reset game to initial state."""
        # Clear all sprite groups
        self.all_sprites.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.bonuses.empty()
        self.explosions.empty()

        # Create player
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        self.all_sprites.add(self.player)

        # Reset wave and create enemies with difficulty modifier
        self.wave = 1
        self.enemy_group.create_formation(self.wave, self.get_difficulty_modifier())
        self.all_sprites.add(self.enemy_group.enemies)

    def handle_events(self):
        """Handle all game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAYING
                        self.reset_game()
                        # Start background music with appropriate theme if enabled
                        if self.music_enabled:
                            theme = self.get_music_theme()
                            sound_manager.play_music(theme)
                    elif event.key == pygame.K_s:
                        self.state = GameState.SETTINGS
                        self.selected_setting = 0
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == GameState.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player_shoot()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.PAUSED

                elif self.state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.PLAYING
                    elif event.key == pygame.K_q:
                        self.state = GameState.MENU
                        sound_manager.stop_music()  # Stop music when quitting to menu

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.MENU
                        sound_manager.stop_music()  # Stop music when returning to menu

                elif self.state == GameState.WAVE_CLEAR:
                    if event.key == pygame.K_SPACE:
                        self.next_wave()

                elif self.state == GameState.SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    else:
                        # Delegate navigation to settings menu
                        self.settings_menu.handle_navigation(event.key)

    def player_shoot(self):
        """Handle player shooting."""
        if self.player and self.player.can_shoot(pygame.time.get_ticks()):
            bullets = self.player.shoot(pygame.time.get_ticks())
            for bullet in bullets:
                # Use bullet pool - handle special bullet types
                if isinstance(bullet, TripleShotBullet):
                    pooled_bullet = bullet_pool.get_bullet(
                        TripleShotBullet,
                        bullet.rect.centerx,
                        bullet.rect.centery,
                        bullet.speed,
                        bullet.owner,
                        bullet.x_velocity,
                    )
                else:
                    pooled_bullet = bullet_pool.get_bullet(
                        type(bullet),
                        bullet.rect.centerx,
                        bullet.rect.centery,
                        bullet.speed,
                        bullet.owner,
                    )
                self.player_bullets.add(pooled_bullet)
                self.all_sprites.add(pooled_bullet)
            # Play shooting sound
            sound_manager.play("player_shoot")

    def enemy_shoot(self):
        """Handle enemy shooting."""
        # Don't shoot if frozen
        if self.enemy_group.frozen:
            return

        bottom_enemies = self.enemy_group.get_bottom_enemies()
        for enemy in bottom_enemies:
            if enemy.can_shoot():
                result = enemy.shoot()
                # Elite enemies can return a list of bullets
                if isinstance(result, list):
                    for bullet in result:
                        # Handle EliteBullet with x_direction parameter
                        if hasattr(bullet, "x_direction"):
                            pooled_bullet = bullet_pool.get_bullet(
                                EliteBullet,
                                bullet.rect.centerx,
                                bullet.rect.centery,
                                bullet.speed,
                                bullet.owner,
                                bullet.x_direction,
                            )
                        else:
                            pooled_bullet = bullet_pool.get_bullet(
                                type(bullet),
                                bullet.rect.centerx,
                                bullet.rect.centery,
                                bullet.speed,
                                bullet.owner,
                            )
                        self.enemy_bullets.add(pooled_bullet)
                        self.all_sprites.add(pooled_bullet)
                else:
                    # Handle single bullet
                    if hasattr(result, "x_direction"):
                        pooled_bullet = bullet_pool.get_bullet(
                            EliteBullet,
                            result.rect.centerx,
                            result.rect.centery,
                            result.speed,
                            result.owner,
                            result.x_direction,
                        )
                    else:
                        pooled_bullet = bullet_pool.get_bullet(
                            type(result),
                            result.rect.centerx,
                            result.rect.centery,
                            result.speed,
                            result.owner,
                        )
                    self.enemy_bullets.add(pooled_bullet)
                    self.all_sprites.add(pooled_bullet)
                # Play enemy shooting sound
                sound_manager.play("enemy_shoot")

    def _update_visual_effects(self):
        """Update visual effects like starfield, grid, and particles."""
        if self.starfield:
            self.starfield.update()
        if self.neon_grid:
            self.neon_grid.update()
        self.menu_heartbeat.update()

        # Update rainbow pulses
        for pulse in self.rainbow_pulses[:]:
            pulse.update()
            if not pulse.active:
                self.rainbow_pulses.remove(pulse)

        # Update sparkle effects
        for sparkle in self.sparkle_effects[:]:
            sparkle.update()
            if not sparkle.active:
                self.sparkle_effects.remove(sparkle)

    def _update_game_playing(self):
        """Update game logic when in PLAYING state."""
        # Update player with keyboard input
        keys = pygame.key.get_pressed()
        if self.player:
            self.player.update(keys)
            # Add trail effect for player movement if enabled
            if self.player_trail:
                self.player_trail.add_point(
                    (self.player.rect.centerx, self.player.rect.centery)
                )

        # Update all other sprites
        self.enemy_group.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.bonuses.update()
        self.explosions.update()

        # Update HUD
        self.hud.update(self.player, self.wave, self.enemy_group)

        # Enemy shooting
        self.enemy_shoot()

        # Check collisions
        self.check_collisions()

        # Check game over conditions
        self._check_game_over_conditions()

    def _check_game_over_conditions(self):
        """Check for game over conditions."""
        if not self.player:
            return

        if not self.player.is_alive():
            self._handle_game_over()
        elif self.enemy_group.check_player_collision(self.player.rect):
            self.player.lives = 0
            self._handle_game_over()
        elif self.enemy_group.is_empty():
            self._handle_wave_clear()

    def _handle_game_over(self):
        """Handle game over state transition."""
        self.state = GameState.GAME_OVER
        self.save_high_score()
        sound_manager.play("game_over")
        sound_manager.stop_music()
        if self.player_trail:
            self.player_trail.clear()

    def _handle_wave_clear(self):
        """Handle wave clear state transition."""
        self.state = GameState.WAVE_CLEAR
        self.player.score += WAVE_CLEAR_BONUS
        sound_manager.play("wave_clear")

        # Add celebration sparkles only if particles enabled
        if self.particles_enabled:
            for _ in range(5):
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(100, SCREEN_HEIGHT - 100)
                self.sparkle_effects.append(SparkleEffect((x, y)))

    def update(self):
        """Update game state."""
        # Always update visual effects
        self._update_visual_effects()

        # Update settings menu animations
        if self.state == GameState.SETTINGS:
            self.settings_menu.update()

        # Update game logic only when playing
        if self.state == GameState.PLAYING:
            self._update_game_playing()

    def check_collisions(self):
        """Check all game collisions."""
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
                    # Use explosion pool only if particles are enabled
                    if self.particles_enabled:
                        explosion = explosion_pool.get_explosion(
                            Explosion, enemy.rect.centerx, enemy.rect.centery
                        )
                        self.explosions.add(explosion)
                        self.all_sprites.add(explosion)
                    # Play explosion sound
                    sound_manager.play("explosion")

                    # Chance to spawn bonus
                    if random.random() < BONUS_SPAWN_CHANCE:
                        bonus = Bonus(enemy.rect.centerx, enemy.rect.centery)
                        self.bonuses.add(bonus)
                        self.all_sprites.add(bonus)
                        # Add sparkle effect for bonus spawn only if particles enabled
                        if self.particles_enabled:
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
                # Use explosion pool only if particles are enabled
                if self.particles_enabled:
                    explosion = explosion_pool.get_explosion(
                        Explosion, self.player.rect.centerx, self.player.rect.centery
                    )
                    self.explosions.add(explosion)
                    self.all_sprites.add(explosion)

        # Player collecting bonuses
        if self.player:
            collected_bonuses = pygame.sprite.spritecollide(
                self.player, self.bonuses, True
            )
            for bonus in collected_bonuses:
                self.apply_bonus_effect(bonus.shape_type)
                # Play bonus collection sound
                sound_manager.play("bonus_collect")
                # Add rainbow pulse effect at collection point only if particles enabled
                if self.particles_enabled:
                    self.rainbow_pulses.append(
                        RainbowPulse((bonus.rect.centerx, bonus.rect.centery))
                    )

    def apply_bonus_effect(self, bonus_type: int):
        """Apply bonus effect based on Tetris block type."""
        current_time = pygame.time.get_ticks()

        if self.player:
            if bonus_type == BonusType.EXTRA_LIFE:
                # O-block (cyan) - add 1 life
                self.player.add_life()
                self.player.score += BONUS_SCORE

            elif bonus_type == BonusType.FREEZE_ENEMIES:
                # T-block (yellow) - freeze enemies for 5 seconds
                self.enemy_group.freeze(FREEZE_DURATION)
                self.player.score += BONUS_SCORE

            elif bonus_type == BonusType.TRIPLE_SHOT:
                # I-block (purple) - triple shot
                self.player.activate_triple_shot()
                self.player.score += BONUS_SCORE

            elif bonus_type == BonusType.SHIELD:
                # S-block (pink) - temporary shield
                self.player.activate_shield(current_time)
                self.player.score += BONUS_SCORE

            elif bonus_type == BonusType.RAPID_FIRE:
                # Z-block (green) - rapid fire
                self.player.activate_rapid_fire(current_time)
                self.player.score += BONUS_SCORE

        # Play power-up sound for all bonus types
        sound_manager.play("power_up")

    def next_wave(self):
        """Progress to next wave."""
        self.wave += 1
        self.enemy_group.create_formation(self.wave, self.get_difficulty_modifier())
        self.all_sprites.add(self.enemy_group.enemies)
        self.state = GameState.PLAYING

        # Show wave transition in HUD
        self.hud.show_wave_transition(self.wave)

        # Change music theme based on wave if music is enabled
        if self.music_enabled:
            theme = self.get_music_theme()
            sound_manager.play_music(theme)

    def get_difficulty_modifier(self):
        """Get difficulty modifier for enemy behavior."""
        if self.difficulty == "Easy":
            return 0.7  # 30% slower/less aggressive
        if self.difficulty == "Hard":
            return 1.5  # 50% faster/more aggressive
        return 1.0  # Normal

    def get_music_theme(self) -> int:
        """Get music theme index based on current wave."""
        if self.wave <= 3:
            return 0  # Theme 1: Original Synthwave
        if self.wave <= 6:
            return 1  # Theme 2: Dark Techno
        return 2  # Theme 3: Epic Boss Battle

    def handle_setting_change(self, key):
        """Handle changing settings values."""
        if self.selected_setting == 0:  # Sound
            if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                self.sound_enabled = not self.sound_enabled
                # Update global sound state
                global SOUND_ENABLED
                SOUND_ENABLED = self.sound_enabled
                # Update sound manager
                sound_manager.sound_enabled = self.sound_enabled
                # Stop music if sound is disabled
                if not self.sound_enabled:
                    sound_manager.stop_music()
                    self.music_enabled = False  # Also disable music when sound is off
        elif self.selected_setting == 1:  # Music
            if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                self.music_enabled = not self.music_enabled
                # Update global music state
                global MUSIC_ENABLED
                MUSIC_ENABLED = self.music_enabled
                # Stop or start music based on setting
                if not self.music_enabled:
                    sound_manager.stop_music()
                elif self.state == GameState.PLAYING and self.sound_enabled:
                    # Restart music if in game and sound is enabled
                    theme = self.get_music_theme()
                    sound_manager.play_music(theme)
        elif self.selected_setting == 2:  # Volume
            if key == pygame.K_LEFT and self.sound_volume > 0:
                self.sound_volume = max(0, self.sound_volume - 0.1)
            elif key == pygame.K_RIGHT and self.sound_volume < 1:
                self.sound_volume = min(1, self.sound_volume + 0.1)
            # Update all sound volumes
            for sound in sound_manager.sounds.values():
                sound.set_volume(self.sound_volume)
            # Also update music volume
            sound_manager.set_music_volume(self.sound_volume)
        elif self.selected_setting == 3:  # FPS Display
            if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                self.show_fps = not self.show_fps
        elif self.selected_setting == 4:  # Particles
            if key == pygame.K_LEFT or key == pygame.K_RIGHT:
                self.particles_enabled = not self.particles_enabled
        elif self.selected_setting == 5:  # Difficulty
            difficulties = ["Easy", "Normal", "Hard"]
            current_idx = difficulties.index(self.difficulty)
            if key == pygame.K_LEFT:
                current_idx = (current_idx - 1) % len(difficulties)
            elif key == pygame.K_RIGHT:
                current_idx = (current_idx + 1) % len(difficulties)
            self.difficulty = difficulties[current_idx]

    def draw_menu(self):
        """Draw main menu."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw starfield if enabled
        if self.starfield:
            self.starfield.draw(self.screen)

        # Draw neon grid with perspective if enabled
        if self.neon_grid:
            self.neon_grid.draw(self.screen)

        # Title with neon glow effect
        NeonText.draw_glowing_text(
            self.screen,
            "NEON INVADERS",
            self.big_font,
            (SCREEN_WIDTH // 2, 150),
            NEON_GREEN,
            glow_intensity=4,
        )

        # High score
        NeonText.draw_glowing_text(
            self.screen,
            f"High Score: {self.high_score}",
            self.font,
            (SCREEN_WIDTH // 2, 250),
            NEON_YELLOW,
        )

        # Instructions with pulsing effect
        pulse_offset = abs(pygame.time.get_ticks() % 2000 - 1000) / 1000.0
        start_color = (
            int(NEON_CYAN[0] * (0.7 + 0.3 * pulse_offset)),
            int(NEON_CYAN[1] * (0.7 + 0.3 * pulse_offset)),
            int(NEON_CYAN[2] * (0.7 + 0.3 * pulse_offset)),
        )

        NeonText.draw_glowing_text(
            self.screen,
            "Press SPACE to Start",
            self.font,
            (SCREEN_WIDTH // 2, 350),
            start_color,
        )

        NeonText.draw_glowing_text(
            self.screen,
            "Press S for Settings",
            self.font,
            (SCREEN_WIDTH // 2, 400),
            NEON_PURPLE,
        )

        NeonText.draw_glowing_text(
            self.screen,
            "Press ESC to Quit",
            self.font,
            (SCREEN_WIDTH // 2, 450),
            NEON_PINK,
        )

        # Draw heartbeat animation in corner
        self.menu_heartbeat.draw(self.screen)

        # Draw rainbow pulses
        for pulse in self.rainbow_pulses:
            pulse.draw(self.screen)

    def draw_game(self):
        """Draw game play screen."""
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

        # Draw shield visual effect with enhanced glow
        if self.player and self.player.shield_active:
            self.neon_effect.draw_glowing_circle(
                self.screen, (self.player.rect.centerx, self.player.rect.centery), 35, 3
            )

        # Draw rainbow pulses only if particles enabled
        if self.particles_enabled:
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

    def draw_paused(self):
        """Draw pause screen."""
        self.draw_game()  # Draw game in background

        # Darken screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Pause text with glow
        NeonText.draw_glowing_text(
            self.screen,
            "PAUSED",
            self.big_font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            NEON_YELLOW,
            glow_intensity=4,
        )

        NeonText.draw_glowing_text(
            self.screen,
            "Press ESC to Resume | Q to Quit",
            self.font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80),
            NEON_CYAN,
        )

    def draw_game_over(self):
        """Draw game over screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw starfield if enabled
        if self.starfield:
            self.starfield.draw(self.screen)

        # Darken background for game over
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game over text with dramatic glow
        NeonText.draw_glowing_text(
            self.screen,
            "GAME OVER",
            self.big_font,
            (SCREEN_WIDTH // 2, 150),
            NEON_RED,
            glow_intensity=5,
        )

        # Final score
        if self.player:
            NeonText.draw_glowing_text(
                self.screen,
                f"Final Score: {self.player.score}",
                self.font,
                (SCREEN_WIDTH // 2, 250),
                NEON_YELLOW,
            )

            # High score
            if self.player.score > self.high_score:
                # Animate new high score with rainbow effect
                time_offset = pygame.time.get_ticks() / 100
                hue = int(time_offset * 10) % 360
                color = pygame.Color(0)
                color.hsva = (hue, 100, 100, 100)

                NeonText.draw_glowing_text(
                    self.screen,
                    "NEW HIGH SCORE!",
                    self.font,
                    (SCREEN_WIDTH // 2, 300),
                    (color.r, color.g, color.b),
                    glow_intensity=3,
                )

                # Add sparkles around new high score only if particles enabled
                if self.particles_enabled and random.random() < 0.3:
                    x = SCREEN_WIDTH // 2 + random.randint(-150, 150)
                    y = 300 + random.randint(-20, 20)
                    self.sparkle_effects.append(SparkleEffect((x, y)))
            else:
                NeonText.draw_glowing_text(
                    self.screen,
                    f"High Score: {self.high_score}",
                    self.font,
                    (SCREEN_WIDTH // 2, 300),
                    NEON_CYAN,
                )

        # Continue text
        NeonText.draw_glowing_text(
            self.screen,
            "Press SPACE to Continue",
            self.font,
            (SCREEN_WIDTH // 2, 400),
            NEON_PURPLE,
        )

        # Draw sparkle effects only if particles enabled
        if self.particles_enabled:
            for sparkle in self.sparkle_effects:
                sparkle.draw(self.screen)

    def draw_wave_clear(self):
        """Draw wave clear screen."""
        self.draw_game()  # Draw game in background

        # Wave clear text with celebration effect
        NeonText.draw_glowing_text(
            self.screen,
            f"WAVE {self.wave} CLEAR!",
            self.big_font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            NEON_GREEN,
            glow_intensity=4,
        )

        NeonText.draw_glowing_text(
            self.screen,
            f"Wave Bonus: {WAVE_CLEAR_BONUS}",
            self.font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60),
            NEON_YELLOW,
        )

        NeonText.draw_glowing_text(
            self.screen,
            "Press SPACE to Continue",
            self.font,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100),
            NEON_CYAN,
        )

        # Draw celebration sparkles only if particles enabled
        if self.particles_enabled:
            for sparkle in self.sparkle_effects:
                sparkle.draw(self.screen)

    def draw_settings(self):
        """Draw settings menu."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw starfield if enabled
        if self.starfield:
            self.starfield.draw(self.screen)

        # Draw grid if enabled
        if self.neon_grid:
            self.neon_grid.draw(self.screen)

        # Delegate drawing to the enhanced settings menu
        self.settings_menu.draw()

    def draw(self):
        """Draw appropriate screen based on game state."""
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_paused()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.WAVE_CLEAR:
            self.draw_wave_clear()

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
