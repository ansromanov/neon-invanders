"""Game entities: Player, Enemy, Bullet, and Bonus classes."""

import pygame
import random
from typing import List, Tuple
from config import *
from sprites import sprite_cache


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

    def update(self, keys):
        """Update player position based on input."""
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def can_shoot(self, current_time: int) -> bool:
        """Check if player can shoot based on cooldown."""
        return current_time - self.last_shot_time > PLAYER_SHOOT_COOLDOWN

    def shoot(self, current_time: int) -> "Bullet":
        """Create a bullet at player position."""
        self.last_shot_time = current_time
        return Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED, "player")

    def hit(self):
        """Handle player being hit."""
        self.lives -= 1

    def is_alive(self) -> bool:
        """Check if player has lives remaining."""
        return self.lives > 0


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
        return random.random() < ENEMY_SHOOT_CHANCE

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

    def create_formation(self, wave: int = 1):
        """Create the initial enemy formation."""
        self.enemies.empty()
        speed_multiplier = 1 + (wave - 1) * 0.2  # Increase speed each wave

        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = col * ENEMY_SPACING_X + 50
                y = row * ENEMY_SPACING_Y + ENEMY_START_Y
                enemy = Enemy(x, y, row)
                self.enemies.add(enemy)

    def update(self):
        """Update all enemies with formation movement."""
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

    def get_bottom_enemies(self) -> List[Enemy]:
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
