"""Main game logic and state management."""

import pygame
import random
import json
import os
from typing import Optional
from config import *
from entities import Player, Enemy, Bullet, Bonus, Explosion, EnemyGroup
from sprites import sprite_cache
from sounds import sound_manager


class Game:
    """Main game class managing states and game logic."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)

        # Load and scale background image
        try:
            self.background = pygame.image.load("background.png").convert()
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

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.bonuses = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        # Game entities
        self.player = None
        self.enemy_group = EnemyGroup()

    def load_high_score(self) -> int:
        """Load high score from file."""
        try:
            if os.path.exists("highscore.json"):
                with open("highscore.json", "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
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

        # Reset wave and create enemies
        self.wave = 1
        self.enemy_group.create_formation(self.wave)
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

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.MENU

                elif self.state == GameState.WAVE_CLEAR:
                    if event.key == pygame.K_SPACE:
                        self.next_wave()

    def player_shoot(self):
        """Handle player shooting."""
        if self.player and self.player.can_shoot(pygame.time.get_ticks()):
            bullets = self.player.shoot(pygame.time.get_ticks())
            for bullet in bullets:
                self.player_bullets.add(bullet)
                self.all_sprites.add(bullet)
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
                bullet = enemy.shoot()
                self.enemy_bullets.add(bullet)
                self.all_sprites.add(bullet)
                # Play enemy shooting sound
                sound_manager.play("enemy_shoot")

    def update(self):
        """Update game state."""
        if self.state != GameState.PLAYING:
            return

        # Update player with keyboard input
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # Update all other sprites
        self.enemy_group.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.bonuses.update()
        self.explosions.update()

        # Enemy shooting
        self.enemy_shoot()

        # Check collisions
        self.check_collisions()

        # Check game over conditions
        if not self.player.is_alive():
            self.state = GameState.GAME_OVER
            self.save_high_score()
            # Play game over sound
            sound_manager.play("game_over")
        elif self.enemy_group.check_player_collision(self.player.rect):
            self.player.lives = 0
            self.state = GameState.GAME_OVER
            self.save_high_score()
            # Play game over sound
            sound_manager.play("game_over")
        elif self.enemy_group.is_empty():
            self.state = GameState.WAVE_CLEAR
            self.player.score += WAVE_CLEAR_BONUS
            # Play wave clear sound
            sound_manager.play("wave_clear")

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
                    self.player.score += ENEMY_SCORE
                    explosion = Explosion(enemy.rect.centerx, enemy.rect.centery)
                    self.explosions.add(explosion)
                    self.all_sprites.add(explosion)
                    # Play explosion sound
                    sound_manager.play("explosion")

                    # Chance to spawn bonus
                    if random.random() < BONUS_SPAWN_CHANCE:
                        bonus = Bonus(enemy.rect.centerx, enemy.rect.centery)
                        self.bonuses.add(bonus)
                        self.all_sprites.add(bonus)

        # Enemy bullets hitting player
        hit_player = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        if hit_player:
            if self.player.shield_active:
                # Play shield hit sound
                sound_manager.play("shield_hit")
            else:
                # Play explosion sound
                sound_manager.play("explosion")
            self.player.hit()
            explosion = Explosion(self.player.rect.centerx, self.player.rect.centery)
            self.explosions.add(explosion)
            self.all_sprites.add(explosion)

        # Player collecting bonuses
        collected_bonuses = pygame.sprite.spritecollide(self.player, self.bonuses, True)
        for bonus in collected_bonuses:
            self.apply_bonus_effect(bonus.shape_type)
            # Play bonus collection sound
            sound_manager.play("bonus_collect")

    def apply_bonus_effect(self, bonus_type: int):
        """Apply bonus effect based on Tetris block type."""
        current_time = pygame.time.get_ticks()

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
        self.enemy_group.create_formation(self.wave)
        self.all_sprites.add(self.enemy_group.enemies)
        self.state = GameState.PLAYING

    def draw_menu(self):
        """Draw main menu."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Title
        title_text = self.big_font.render("NEON INVADERS", True, NEON_GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)

        # High score
        high_score_text = self.font.render(
            f"High Score: {self.high_score}", True, NEON_YELLOW
        )
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(high_score_text, high_score_rect)

        # Instructions
        start_text = self.font.render("Press SPACE to Start", True, NEON_CYAN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(start_text, start_rect)

        controls_text = self.font.render(
            "Arrow Keys: Move | Space: Shoot", True, NEON_PURPLE
        )
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(controls_text, controls_rect)

        quit_text = self.font.render("Press ESC to Quit", True, NEON_PINK)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(quit_text, quit_rect)

    def draw_game(self):
        """Draw game play screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw all sprites
        self.all_sprites.draw(self.screen)

        # Draw UI
        score_text = self.font.render(f"Score: {self.player.score}", True, NEON_GREEN)
        self.screen.blit(score_text, (10, 10))

        lives_text = self.font.render(f"Lives: {self.player.lives}", True, NEON_CYAN)
        self.screen.blit(lives_text, (10, 50))

        wave_text = self.font.render(f"Wave: {self.wave}", True, NEON_YELLOW)
        self.screen.blit(wave_text, (SCREEN_WIDTH - 150, 10))

        # Draw active bonuses
        y_offset = 90
        if self.player.shield_active:
            shield_text = self.font.render("SHIELD ACTIVE", True, NEON_PINK)
            self.screen.blit(shield_text, (10, y_offset))
            y_offset += 30

        if self.player.rapid_fire_active:
            rapid_text = self.font.render("RAPID FIRE", True, NEON_GREEN)
            self.screen.blit(rapid_text, (10, y_offset))
            y_offset += 30

        if self.enemy_group.frozen:
            freeze_text = self.font.render("ENEMIES FROZEN", True, NEON_YELLOW)
            self.screen.blit(freeze_text, (10, y_offset))

        # Draw shield visual effect
        if self.player.shield_active:
            pygame.draw.circle(
                self.screen,
                (*NEON_CYAN, 100),
                (self.player.rect.centerx, self.player.rect.centery),
                35,
                3,
            )

    def draw_paused(self):
        """Draw pause screen."""
        self.draw_game()  # Draw game in background

        # Darken screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Pause text
        pause_text = self.big_font.render("PAUSED", True, NEON_YELLOW)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(pause_text, pause_rect)

        resume_text = self.font.render(
            "Press ESC to Resume | Q to Quit", True, NEON_CYAN
        )
        resume_rect = resume_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
        )
        self.screen.blit(resume_text, resume_rect)

    def draw_game_over(self):
        """Draw game over screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Darken background for game over
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game over text
        game_over_text = self.big_font.render("GAME OVER", True, NEON_RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(game_over_text, game_over_rect)

        # Final score
        score_text = self.font.render(
            f"Final Score: {self.player.score}", True, NEON_YELLOW
        )
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(score_text, score_rect)

        # High score
        if self.player.score > self.high_score:
            new_high_text = self.font.render("NEW HIGH SCORE!", True, NEON_GREEN)
            new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(new_high_text, new_high_rect)
        else:
            high_score_text = self.font.render(
                f"High Score: {self.high_score}", True, NEON_CYAN
            )
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(high_score_text, high_score_rect)

        # Continue text
        continue_text = self.font.render("Press SPACE to Continue", True, NEON_PURPLE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(continue_text, continue_rect)

    def draw_wave_clear(self):
        """Draw wave clear screen."""
        self.draw_game()  # Draw game in background

        # Wave clear text
        wave_clear_text = self.big_font.render(
            f"WAVE {self.wave} CLEAR!", True, NEON_GREEN
        )
        wave_clear_rect = wave_clear_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )
        self.screen.blit(wave_clear_text, wave_clear_rect)

        bonus_text = self.font.render(
            f"Wave Bonus: {WAVE_CLEAR_BONUS}", True, NEON_YELLOW
        )
        bonus_rect = bonus_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
        )
        self.screen.blit(bonus_text, bonus_rect)

        continue_text = self.font.render("Press SPACE to Continue", True, NEON_CYAN)
        continue_rect = continue_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        )
        self.screen.blit(continue_text, continue_rect)

    def draw(self):
        """Draw appropriate screen based on game state."""
        if self.state == GameState.MENU:
            self.draw_menu()
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
