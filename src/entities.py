"""Game entities: Player, Enemy, Bullet, and Bonus classes."""

import random

import pygame

from .config import *
from .sprites import sprite_cache


class Player(pygame.sprite.Sprite):
    """Player spaceship entity."""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = sprite_cache.get("player")
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_LIVES
        self.last_shot_time = 0
        self.score = 0

        # Bonus effects
        self.triple_shot_active = False
        self.rapid_fire_active = False
        self.rapid_fire_end_time = 0
        self.shield_active = False
        self.shield_end_time = 0

    def can_shoot(self, current_time: int) -> bool:
        """Check if player can shoot based on cooldown."""
        cooldown = PLAYER_SHOOT_COOLDOWN
        if self.rapid_fire_active and current_time < self.rapid_fire_end_time:
            cooldown = PLAYER_SHOOT_COOLDOWN // 3  # 3x faster shooting
        return current_time - self.last_shot_time > cooldown

    def shoot(self, current_time: int) -> list["Bullet"]:
        """Create bullets at player position."""
        self.last_shot_time = current_time
        bullets = []

        if self.triple_shot_active:
            # Triple shot - triangular pattern
            bullets.append(
                TripleShotBullet(
                    self.rect.centerx - 10, self.rect.top, -BULLET_SPEED, "player", -0.2
                )
            )
            bullets.append(
                TripleShotBullet(
                    self.rect.centerx, self.rect.top - 5, -BULLET_SPEED, "player", 0
                )
            )
            bullets.append(
                TripleShotBullet(
                    self.rect.centerx + 10, self.rect.top, -BULLET_SPEED, "player", 0.2
                )
            )
            self.triple_shot_active = False  # One-time use
        else:
            bullets.append(
                Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED, "player")
            )

        return bullets

    def hit(self):
        """Handle player being hit."""
        if self.shield_active and pygame.time.get_ticks() < self.shield_end_time:
            # Shield absorbs the hit
            self.shield_active = False
            self.shield_end_time = 0
        else:
            self.lives -= 1

    def is_alive(self) -> bool:
        """Check if player has lives remaining."""
        return self.lives > 0

    def add_life(self):
        """Add an extra life."""
        self.lives += 1

    def activate_rapid_fire(self, current_time: int):
        """Activate rapid fire bonus."""
        self.rapid_fire_active = True
        self.rapid_fire_end_time = current_time + RAPID_FIRE_DURATION

    def activate_shield(self, current_time: int):
        """Activate shield bonus."""
        self.shield_active = True
        self.shield_end_time = current_time + SHIELD_DURATION

    def activate_triple_shot(self):
        """Activate triple shot for next shot."""
        self.triple_shot_active = True

    def update(self, keys):
        """Update player position based on input."""
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

        # Check if bonuses expired
        current_time = pygame.time.get_ticks()
        if self.rapid_fire_active and current_time > self.rapid_fire_end_time:
            self.rapid_fire_active = False
        if self.shield_active and current_time > self.shield_end_time:
            self.shield_active = False


class Enemy(pygame.sprite.Sprite):
    """Enemy invader entity."""

    def __init__(self, x: int, y: int, row: int = 0):
        super().__init__()
        self.image = sprite_cache.get("enemy")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.row = row
        self.direction = 1  # 1 for right, -1 for left
        self.drop_distance = 0

    def update(self):
        """Update enemy position."""
        if self.drop_distance > 0:
            self.rect.y += min(self.drop_distance, 2)
            self.drop_distance -= 2
        else:
            self.rect.x += ENEMY_SPEED_X * self.direction

    def reverse_direction(self):
        """Reverse horizontal movement direction and drop down."""
        self.direction *= -1
        self.drop_distance = ENEMY_SPEED_Y

    def can_shoot(self) -> bool:
        """Randomly determine if enemy shoots this frame."""
        # Get difficulty modifier from game
        difficulty = 1.0
        try:
            from .game import Game

            if hasattr(Game, "_instance") and Game._instance:
                difficulty = Game._instance.get_difficulty_modifier()
        except:
            pass
        return random.random() < ENEMY_SHOOT_CHANCE * difficulty

    def shoot(self) -> "Bullet":
        """Create a bullet at enemy position."""
        return Bullet(self.rect.centerx, self.rect.bottom, ENEMY_BULLET_SPEED, "enemy")


class Bullet(pygame.sprite.Sprite):
    """Bullet entity for both player and enemies."""

    def __init__(self, x: int, y: int, speed: int, owner: str):
        super().__init__()
        sprite_name = "player_bullet" if owner == "player" else "enemy_bullet"
        self.image = sprite_cache.get(sprite_name)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = speed
        self.owner = owner

    def update(self):
        """Update bullet position."""
        self.rect.y += self.speed

        # Remove bullet if it goes off screen
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


class TripleShotBullet(Bullet):
    """Special bullet for triple shot that moves at an angle."""

    def __init__(self, x: int, y: int, speed: int, owner: str, x_velocity: float):
        super().__init__(x, y, speed, owner)
        self.x_velocity = x_velocity

    def update(self):
        """Update bullet position with angled movement."""
        self.rect.y += self.speed
        self.rect.x += int(self.x_velocity * abs(self.speed))

        # Remove bullet if it goes off screen
        if (
            self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT
            or self.rect.right < 0
            or self.rect.left > SCREEN_WIDTH
        ):
            self.kill()


class Bonus(pygame.sprite.Sprite):
    """Tetris-themed bonus pickup."""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.shape_type = random.randint(0, 4)
        self.image = sprite_cache.get(f"bonus_{self.shape_type}")
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = BONUS_FALL_SPEED
        self.value = BONUS_SCORE

    def update(self):
        """Update bonus position."""
        self.rect.y += self.speed

        # Remove bonus if it falls off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """Explosion animation effect."""

    def __init__(self, x: int, y: int):
        super().__init__()
        self.frames = sprite_cache.get("explosion")
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.animation_speed = 2
        self.animation_counter = 0

    def update(self):
        """Update explosion animation."""
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.current_frame]
                self.rect = self.image.get_rect(center=self.rect.center)


class EnemyGroup:
    """Manages the formation of enemies with classic Space Invaders movement."""

    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.moving_right = True
        self.drop_timer = 0
        self.frozen = False
        self.freeze_end_time = 0

    def create_formation(self, wave: int = 1, difficulty_modifier: float = 1.0):
        """Create the initial enemy formation."""
        self.enemies.empty()
        speed_multiplier = (
            1 + (wave - 1) * 0.2
        ) * difficulty_modifier  # Increase speed each wave with difficulty

        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = col * ENEMY_SPACING_X + 50
                y = row * ENEMY_SPACING_Y + ENEMY_START_Y
                enemy = Enemy(x, y, row)
                self.enemies.add(enemy)

    def update(self):
        """Update all enemies with formation movement."""
        # Check if freeze expired
        if self.frozen and pygame.time.get_ticks() > self.freeze_end_time:
            self.frozen = False

        # Don't move if frozen
        if self.frozen:
            return

        # Check if any enemy hit the edge
        hit_edge = False
        for enemy in self.enemies:
            if (enemy.rect.right >= SCREEN_WIDTH - 10 and enemy.direction > 0) or (
                enemy.rect.left <= 10 and enemy.direction < 0
            ):
                hit_edge = True
                break

        # If hit edge, reverse all enemies
        if hit_edge:
            for enemy in self.enemies:
                enemy.reverse_direction()

        # Update all enemies
        self.enemies.update()

    def get_bottom_enemies(self) -> list[Enemy]:
        """Get enemies that can shoot (bottom row of each column)."""
        # Group enemies by column
        columns = {}
        for enemy in self.enemies:
            col = enemy.rect.centerx // ENEMY_SPACING_X
            if col not in columns:
                columns[col] = []
            columns[col].append(enemy)

        # Get bottom enemy from each column
        bottom_enemies = []
        for enemies in columns.values():
            if enemies:
                bottom_enemy = max(enemies, key=lambda e: e.rect.bottom)
                bottom_enemies.append(bottom_enemy)

        return bottom_enemies

    def is_empty(self) -> bool:
        """Check if all enemies are defeated."""
        return len(self.enemies) == 0

    def check_player_collision(self, player_rect: pygame.Rect) -> bool:
        """Check if any enemy reached the player's position."""
        for enemy in self.enemies:
            if enemy.rect.bottom > player_rect.top - 50:
                return True
        return False

    def freeze(self, duration: int):
        """Freeze all enemies for specified duration."""
        self.frozen = True
        self.freeze_end_time = pygame.time.get_ticks() + duration
