"""Game entities: Player, Enemy, Bullet, and Bonus classes."""

import random
from typing import Union

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
        bullets: list[Bullet] = []

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

    def __init__(self, x: int, y: int, row: int = 0, is_elite: bool = False):
        super().__init__()
        self.is_elite = is_elite

        # Load appropriate animation frames
        if self.is_elite:
            self.frames = sprite_cache.get("elite_enemy_frames")
        else:
            self.frames = sprite_cache.get("enemy_frames")

        self.current_frame = 0
        self.animation_speed = 0.1  # Frames per game frame
        self.animation_counter = 0.0

        # Set initial image
        self.image = self.frames[0] if self.frames else sprite_cache.get("enemy")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.row = row
        self.direction = 1  # 1 for right, -1 for left
        self.drop_distance = 0
        self.last_special_attack = 0  # For elite enemy special attacks

    def update(self):
        """Update enemy position and animation."""
        # Update animation
        if self.frames:
            self.animation_counter += self.animation_speed
            if self.animation_counter >= 1.0:
                self.animation_counter = 0.0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]

        # Update position
        if self.drop_distance > 0:
            self.rect.y += min(self.drop_distance, 2)
            self.drop_distance -= 2
        else:
            # Elite enemies move faster
            speed_multiplier = 1.5 if self.is_elite else 1.0
            self.rect.x += int(ENEMY_SPEED_X * self.direction * speed_multiplier)

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
        except Exception:
            pass

        # Elite enemies shoot more frequently
        shoot_chance = ENEMY_SHOOT_CHANCE * difficulty
        if self.is_elite:
            shoot_chance *= 3  # 3x more likely to shoot

        return random.random() < shoot_chance

    def shoot(
        self,
    ) -> Union["Bullet", "EliteBullet", list["Bullet"], list["EliteBullet"]]:
        """Create a bullet at enemy position. Elite enemies can shoot multiple bullets."""
        if self.is_elite:
            current_time = pygame.time.get_ticks()
            # Elite enemies have special attack patterns
            if (
                current_time - self.last_special_attack > 5000
            ):  # Special attack every 5 seconds
                self.last_special_attack = current_time
                # Triple shot spread pattern
                bullets = []
                bullets.append(
                    EliteBullet(
                        self.rect.centerx - 10,
                        self.rect.bottom,
                        ENEMY_BULLET_SPEED,
                        "enemy",
                        -1,
                    )
                )
                bullets.append(
                    EliteBullet(
                        self.rect.centerx,
                        self.rect.bottom,
                        ENEMY_BULLET_SPEED,
                        "enemy",
                        0,
                    )
                )
                bullets.append(
                    EliteBullet(
                        self.rect.centerx + 10,
                        self.rect.bottom,
                        ENEMY_BULLET_SPEED,
                        "enemy",
                        1,
                    )
                )
                return bullets
            # Regular shot but faster
            return EliteBullet(
                self.rect.centerx,
                self.rect.bottom,
                int(ENEMY_BULLET_SPEED * 1.5),
                "enemy",
                0,
            )
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
        # Initialize optional attributes for pooling compatibility
        self.x_velocity: float = 0.0
        self.x_direction = 0

    def update(self):
        """Update bullet position."""
        self.rect.y += self.speed

        # Remove bullet if it goes off screen
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
            # Return bullet to pool when killed
            try:
                from .performance import bullet_pool

                bullet_pool.release_bullet(self)
            except ImportError:
                pass


class EliteBullet(Bullet):
    """Special bullet for elite enemies with angled movement."""

    def __init__(self, x: int, y: int, speed: int, owner: str, x_direction: int):
        super().__init__(x, y, speed, owner)
        self.x_direction = x_direction  # -1 for left, 0 for straight, 1 for right
        # Make elite bullets visually distinct (purple tint)
        purple_surface = pygame.Surface(self.image.get_size())
        purple_surface.fill((255, 100, 255))
        self.image.blit(purple_surface, (0, 0), special_flags=pygame.BLEND_MULT)

    def update(self):
        """Update bullet position with angled movement."""
        self.rect.y += self.speed
        self.rect.x += self.x_direction * 2  # Horizontal movement

        # Remove bullet if it goes off screen
        if (
            self.rect.bottom < 0
            or self.rect.top > SCREEN_HEIGHT
            or self.rect.left > SCREEN_WIDTH
            or self.rect.right < 0
        ):
            self.kill()


class TripleShotBullet(Bullet):
    """Special bullet for triple shot that moves at an angle."""

    def __init__(self, x: int, y: int, speed: int, owner: str, x_velocity: float):
        super().__init__(x, y, speed, owner)
        self.x_velocity: float = x_velocity

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
                # Return explosion to pool when animation completes
                try:
                    from .performance import explosion_pool

                    explosion_pool.release_explosion(self)
                except ImportError:
                    pass
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
        # Cache for bottom enemies to reduce recalculation
        self._bottom_enemies_cache = []
        self._cache_dirty = True

    def create_formation(self, wave: int = 1, difficulty_modifier: float = 1.0):  # noqa: ARG002
        """Create the initial enemy formation."""
        self.enemies.empty()
        # Speed multiplier increases with wave and difficulty
        # (currently not used, but preserved for future enhancements)
        # speed_multiplier = (
        #     1 + (wave - 1) * 0.2
        # ) * difficulty_modifier

        # Calculate number of elite enemies for waves 2+
        total_enemies = ENEMY_ROWS * ENEMY_COLS
        elite_count = 0
        if wave >= 2:
            # 10% elite enemies, increasing slightly with wave
            elite_percentage = 0.1 + (wave - 2) * 0.02  # +2% per wave after wave 2
            elite_count = int(total_enemies * min(elite_percentage, 0.3))  # Cap at 30%

        # Create list of positions and randomly assign elites
        positions = []
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = col * ENEMY_SPACING_X + 50
                y = row * ENEMY_SPACING_Y + ENEMY_START_Y
                positions.append((x, y, row))

        # Randomly select positions for elite enemies
        if elite_count > 0:
            elite_positions = random.sample(positions, elite_count)
        else:
            elite_positions = []

        # Create enemies
        for x, y, row in positions:
            is_elite = (x, y, row) in elite_positions
            enemy = Enemy(x, y, row, is_elite)
            self.enemies.add(enemy)

        # Mark cache as dirty when formation changes
        self._cache_dirty = True

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

        # Mark cache as dirty if any enemies were removed
        if len(self.enemies) != len(self._bottom_enemies_cache):
            self._cache_dirty = True

    def get_bottom_enemies(self) -> list[Enemy]:
        """Get enemies that can shoot (bottom row of each column)."""
        # Use cached result if available
        if not self._cache_dirty and self._bottom_enemies_cache:
            # Validate cache - remove any dead enemies
            self._bottom_enemies_cache = [
                e for e in self._bottom_enemies_cache if e.alive()
            ]
            if self._bottom_enemies_cache:
                return list(self._bottom_enemies_cache)

        # Recalculate bottom enemies
        columns: dict[int, list[Enemy]] = {}
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

        # Cache the result
        self._bottom_enemies_cache = bottom_enemies
        self._cache_dirty = False

        return bottom_enemies

    def is_empty(self) -> bool:
        """Check if all enemies are defeated."""
        return len(self.enemies) == 0

    def check_player_collision(self, player_rect: pygame.Rect) -> bool:
        """Check if any enemy reached the player's position."""
        return any(enemy.rect.bottom > player_rect.top - 50 for enemy in self.enemies)

    def freeze(self, duration: int):
        """Freeze all enemies for specified duration."""
        self.frozen = True
        self.freeze_end_time = pygame.time.get_ticks() + duration
