"""Unit tests for game entities."""

import os
import sys
from unittest.mock import patch

import pygame
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    BONUS_FALL_SPEED,
    BONUS_SCORE,
    BULLET_SPEED,
    ENEMY_BULLET_SPEED,
    ENEMY_COLS,
    ENEMY_ROWS,
    ENEMY_SPACING_X,
    ENEMY_SPEED_X,
    ENEMY_SPEED_Y,
    PLAYER_LIVES,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_SPEED,
    RAPID_FIRE_DURATION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DURATION,
)
from src.entities import (
    Bonus,
    Bullet,
    EliteBullet,
    Enemy,
    EnemyGroup,
    Explosion,
    Player,
    TripleShotBullet,
)
from src.sprites import sprite_cache


class TestPlayer:
    """Test cases for Player entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.player = Player(400, 500)
        yield
        pygame.quit()

    def test_player_initialization(self):
        """Test player is initialized correctly."""
        assert self.player.rect.centerx == 400
        assert self.player.rect.centery == 500
        assert self.player.speed == PLAYER_SPEED
        assert self.player.lives == PLAYER_LIVES
        assert self.player.score == 0
        assert self.player.triple_shot_active is False
        assert self.player.rapid_fire_active is False
        assert self.player.shield_active is False

    def test_player_movement_left(self):
        """Test player moves left correctly."""
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x - PLAYER_SPEED

    def test_player_movement_right(self):
        """Test player moves right correctly."""
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x + PLAYER_SPEED

    def test_player_boundary_left(self):
        """Test player can't move past left boundary."""
        self.player.rect.left = 5
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x - PLAYER_SPEED

        self.player.rect.left = 0
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x  # Should not move

    def test_player_boundary_right(self):
        """Test player can't move past right boundary."""
        self.player.rect.right = SCREEN_WIDTH - 5
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x + PLAYER_SPEED

        self.player.rect.right = SCREEN_WIDTH
        initial_x = self.player.rect.x
        self.player.update(keys)
        assert self.player.rect.x == initial_x  # Should not move

    def test_player_can_shoot(self):
        """Test player shooting cooldown."""
        current_time = 1000
        assert self.player.can_shoot(current_time) is True

        # Shoot and check cooldown
        bullets = self.player.shoot(current_time)
        assert isinstance(bullets, list)
        assert len(bullets) == 1
        assert isinstance(bullets[0], Bullet)
        assert self.player.can_shoot(current_time + 100) is False
        assert self.player.can_shoot(current_time + PLAYER_SHOOT_COOLDOWN + 1) is True

    def test_player_triple_shot(self):
        """Test player triple shot functionality."""
        self.player.activate_triple_shot()
        assert self.player.triple_shot_active is True

        current_time = 1000
        bullets = self.player.shoot(current_time)
        assert len(bullets) == 3
        assert all(isinstance(b, TripleShotBullet) for b in bullets)
        assert self.player.triple_shot_active is False  # One-time use

    def test_player_rapid_fire(self):
        """Test player rapid fire functionality."""
        current_time = 1000
        self.player.activate_rapid_fire(current_time)
        assert self.player.rapid_fire_active is True
        assert self.player.rapid_fire_end_time == current_time + RAPID_FIRE_DURATION

        # Test faster shooting cooldown
        self.player.shoot(current_time)
        # With rapid fire, cooldown should be 1/3 of normal (250 // 3 = 83)
        rapid_cooldown = PLAYER_SHOOT_COOLDOWN // 3
        assert self.player.can_shoot(current_time + rapid_cooldown) is False
        assert self.player.can_shoot(current_time + rapid_cooldown + 1) is True

        # Test expiration
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: False}
        self.player.update(keys)
        with patch(
            "pygame.time.get_ticks", return_value=current_time + RAPID_FIRE_DURATION + 1
        ):
            self.player.update(keys)
        assert self.player.rapid_fire_active is False

    def test_player_shield(self):
        """Test player shield functionality."""
        current_time = 1000
        self.player.activate_shield(current_time)
        assert self.player.shield_active is True
        assert self.player.shield_end_time == current_time + SHIELD_DURATION

        # Test shield blocks hit
        with patch("pygame.time.get_ticks", return_value=current_time + 100):
            initial_lives = self.player.lives
            self.player.hit()
            assert self.player.lives == initial_lives  # No life lost
            assert self.player.shield_active is False  # Shield consumed

    def test_player_hit(self):
        """Test player loses life when hit."""
        initial_lives = self.player.lives
        self.player.hit()
        assert self.player.lives == initial_lives - 1

    def test_player_is_alive(self):
        """Test player alive status."""
        assert self.player.is_alive() is True
        self.player.lives = 1
        assert self.player.is_alive() is True
        self.player.lives = 0
        assert self.player.is_alive() is False

    def test_player_add_life(self):
        """Test adding extra life."""
        initial_lives = self.player.lives
        self.player.add_life()
        assert self.player.lives == initial_lives + 1


class TestEnemy:
    """Test cases for Enemy entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.enemy = Enemy(100, 100, 0)
        yield
        pygame.quit()

    def test_enemy_initialization(self):
        """Test enemy is initialized correctly."""
        assert self.enemy.rect.x == 100
        assert self.enemy.rect.y == 100
        assert self.enemy.row == 0
        assert self.enemy.direction == 1
        assert self.enemy.drop_distance == 0

    def test_enemy_horizontal_movement(self):
        """Test enemy moves horizontally."""
        initial_x = self.enemy.rect.x
        self.enemy.update()
        assert self.enemy.rect.x == initial_x + ENEMY_SPEED_X

    def test_enemy_reverse_direction(self):
        """Test enemy reverses direction and drops."""
        self.enemy.reverse_direction()
        assert self.enemy.direction == -1
        assert self.enemy.drop_distance == ENEMY_SPEED_Y

    def test_enemy_drop_movement(self):
        """Test enemy drops down when required."""
        initial_y = self.enemy.rect.y
        self.enemy.drop_distance = 10
        self.enemy.update()
        assert self.enemy.rect.y == initial_y + 2
        assert self.enemy.drop_distance == 8

    @patch("random.random")
    def test_enemy_can_shoot(self, mock_random):
        """Test enemy shooting probability."""
        mock_random.return_value = 0.0001
        assert self.enemy.can_shoot() is True

        mock_random.return_value = 0.01
        assert self.enemy.can_shoot() is False

    def test_enemy_shoot(self):
        """Test enemy creates bullet."""
        bullet = self.enemy.shoot()
        assert isinstance(bullet, Bullet)
        assert bullet.rect.centerx == self.enemy.rect.centerx
        assert bullet.rect.centery == self.enemy.rect.bottom
        assert bullet.speed == ENEMY_BULLET_SPEED
        assert bullet.owner == "enemy"

    def test_elite_enemy_initialization(self):
        """Test elite enemy is initialized correctly."""
        elite_enemy = Enemy(100, 100, 0, is_elite=True)
        assert elite_enemy.is_elite is True
        assert elite_enemy.rect.x == 100
        assert elite_enemy.rect.y == 100
        assert elite_enemy.last_special_attack == 0

    def test_elite_enemy_moves_faster(self):
        """Test elite enemy moves faster than regular enemy."""
        elite_enemy = Enemy(100, 100, 0, is_elite=True)
        regular_enemy = Enemy(100, 200, 0, is_elite=False)

        initial_elite_x = elite_enemy.rect.x
        initial_regular_x = regular_enemy.rect.x

        elite_enemy.update()
        regular_enemy.update()

        elite_movement = elite_enemy.rect.x - initial_elite_x
        regular_movement = regular_enemy.rect.x - initial_regular_x

        # Elite enemies move 1.5x faster, but we need to account for integer conversion
        expected_elite_movement = int(ENEMY_SPEED_X * 1.5)
        expected_regular_movement = ENEMY_SPEED_X

        assert elite_movement == expected_elite_movement
        assert regular_movement == expected_regular_movement

    @patch("random.random")
    def test_elite_enemy_shoots_more_frequently(self, mock_random):
        """Test elite enemy shoots 3x more frequently."""
        elite_enemy = Enemy(100, 100, 0, is_elite=True)
        regular_enemy = Enemy(100, 200, 0, is_elite=False)

        # Test at same random value
        mock_random.return_value = 0.0025  # Between regular and elite threshold

        # Regular enemy shouldn't shoot at this probability
        assert regular_enemy.can_shoot() is False
        # Elite enemy should shoot (3x more likely)
        assert elite_enemy.can_shoot() is True

    @patch("pygame.time.get_ticks")
    def test_elite_enemy_special_attack(self, mock_time):
        """Test elite enemy special triple shot attack."""
        elite_enemy = Enemy(100, 100, 0, is_elite=True)

        # First shot with time=0 should trigger special attack (since last_special_attack=0)
        mock_time.return_value = 5001  # More than 5 seconds from initialization
        bullets = elite_enemy.shoot()
        assert isinstance(bullets, list)
        assert len(bullets) == 3
        assert all(isinstance(b, EliteBullet) for b in bullets)
        assert elite_enemy.last_special_attack == 5001

        # Next shot within 5 seconds should be regular
        mock_time.return_value = 8000  # Less than 5 seconds from last special
        bullet = elite_enemy.shoot()
        assert isinstance(bullet, EliteBullet)
        assert not isinstance(bullet, list)
        assert bullet.speed == int(ENEMY_BULLET_SPEED * 1.5)

        # After 5 seconds, should be special attack again
        mock_time.return_value = 10002  # More than 5 seconds from last special
        bullets = elite_enemy.shoot()
        assert isinstance(bullets, list)
        assert len(bullets) == 3


class TestBullet:
    """Test cases for Bullet entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    def test_player_bullet_initialization(self):
        """Test player bullet is initialized correctly."""
        bullet = Bullet(100, 200, -BULLET_SPEED, "player")
        assert bullet.rect.centerx == 100
        assert bullet.rect.centery == 200
        assert bullet.speed == -BULLET_SPEED
        assert bullet.owner == "player"

    def test_enemy_bullet_initialization(self):
        """Test enemy bullet is initialized correctly."""
        bullet = Bullet(150, 250, ENEMY_BULLET_SPEED, "enemy")
        assert bullet.rect.centerx == 150
        assert bullet.rect.centery == 250
        assert bullet.speed == ENEMY_BULLET_SPEED
        assert bullet.owner == "enemy"

    def test_bullet_movement(self):
        """Test bullet moves correctly."""
        bullet = Bullet(100, 200, -5, "player")
        initial_y = bullet.rect.y
        bullet.update()
        assert bullet.rect.y == initial_y - 5

    def test_bullet_removal_top(self):
        """Test bullet is removed when going off top."""
        # Create bullet with centery that will make it go off screen after update
        # Bullet height is 10, so centery=5 means top=0, bottom=10
        bullet = Bullet(100, 5, -15, "player")  # centery=5, moving up at speed -15
        group = pygame.sprite.Group(bullet)
        bullet.update()  # After update, centery=-10, so bottom will be -5
        assert len(group) == 0  # Bullet should be removed

    def test_bullet_removal_bottom(self):
        """Test bullet is removed when going off bottom."""
        # Create bullet with centery that will make it go off screen after update
        # Bullet height is 10, so centery=595 means top=590, bottom=600
        bullet = Bullet(100, SCREEN_HEIGHT - 5, 20, "enemy")  # centery at bottom edge
        group = pygame.sprite.Group(bullet)
        bullet.update()  # After update, centery=615, so top will be 610 > SCREEN_HEIGHT
        assert len(group) == 0  # Bullet should be removed


class TestTripleShotBullet:
    """Test cases for TripleShotBullet entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    def test_triple_shot_bullet_initialization(self):
        """Test triple shot bullet is initialized correctly."""
        bullet = TripleShotBullet(100, 200, -BULLET_SPEED, "player", 0.2)
        assert bullet.rect.centerx == 100
        assert bullet.rect.centery == 200
        assert bullet.speed == -BULLET_SPEED
        assert bullet.owner == "player"
        assert bullet.x_velocity == 0.2

    def test_triple_shot_bullet_angled_movement(self):
        """Test triple shot bullet moves at an angle."""
        bullet = TripleShotBullet(100, 200, -5, "player", 0.5)
        initial_x = bullet.rect.x
        initial_y = bullet.rect.y
        bullet.update()
        assert bullet.rect.y == initial_y - 5
        assert bullet.rect.x == initial_x + int(0.5 * 5)

    def test_triple_shot_bullet_removal_sides(self):
        """Test triple shot bullet is removed when going off sides."""
        # Test left side
        bullet = TripleShotBullet(5, 200, -5, "player", -5)
        group = pygame.sprite.Group(bullet)
        bullet.update()
        assert len(group) == 0  # Should be removed

        # Test right side
        bullet = TripleShotBullet(SCREEN_WIDTH - 5, 200, -5, "player", 5)
        group = pygame.sprite.Group(bullet)
        bullet.update()
        assert len(group) == 0  # Should be removed


class TestBonus:
    """Test cases for Bonus entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    @patch("random.randint")
    def test_bonus_initialization(self, mock_randint):
        """Test bonus is initialized correctly."""
        mock_randint.return_value = 2
        bonus = Bonus(200, 100)
        assert bonus.rect.centerx == 200
        assert bonus.rect.centery == 100
        assert bonus.speed == BONUS_FALL_SPEED
        assert bonus.value == BONUS_SCORE
        assert bonus.shape_type == 2

    def test_bonus_movement(self):
        """Test bonus falls correctly."""
        bonus = Bonus(200, 100)
        initial_y = bonus.rect.y
        bonus.update()
        assert bonus.rect.y == initial_y + BONUS_FALL_SPEED

    def test_bonus_removal(self):
        """Test bonus is removed when falling off screen."""
        # Create bonus at the very bottom of screen
        # The bonus uses centery, and the condition is rect.top > SCREEN_HEIGHT
        bonus = Bonus(200, SCREEN_HEIGHT - 5)  # centery near bottom
        group = pygame.sprite.Group(bonus)
        # Move bonus off screen - need to move it so rect.top > SCREEN_HEIGHT
        # Since bonus height is 20 (from looking at sprite), rect.top = centery - 10
        # So we need centery > SCREEN_HEIGHT + 10
        for _ in range(20):  # Multiple updates to ensure it goes off screen
            bonus.update()
        assert len(group) == 0  # Bonus should be removed


class TestEliteBullet:
    """Test cases for EliteBullet entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    def test_elite_bullet_initialization(self):
        """Test elite bullet is initialized correctly."""
        bullet = EliteBullet(100, 200, ENEMY_BULLET_SPEED, "enemy", 1)
        assert bullet.rect.centerx == 100
        assert bullet.rect.centery == 200
        assert bullet.speed == ENEMY_BULLET_SPEED
        assert bullet.owner == "enemy"
        assert bullet.x_direction == 1

    def test_elite_bullet_angled_movement(self):
        """Test elite bullet moves at an angle."""
        bullet = EliteBullet(100, 200, 5, "enemy", 1)
        initial_x = bullet.rect.x
        initial_y = bullet.rect.y
        bullet.update()
        assert bullet.rect.y == initial_y + 5
        assert bullet.rect.x == initial_x + 2  # x_direction * 2

    def test_elite_bullet_removal_sides(self):
        """Test elite bullet is removed when going off sides."""
        # Test left side - bullet needs to be at edge and move off
        bullet = EliteBullet(1, 200, 5, "enemy", -3)
        group = pygame.sprite.Group(bullet)
        # Move bullet off screen
        bullet.rect.right = 0  # Force it off the left edge
        bullet.update()
        assert len(group) == 0  # Should be removed

        # Test right side
        bullet = EliteBullet(SCREEN_WIDTH - 1, 200, 5, "enemy", 3)
        group = pygame.sprite.Group(bullet)
        # Move bullet off screen
        bullet.rect.left = SCREEN_WIDTH + 1  # Force it off the right edge
        bullet.update()
        assert len(group) == 0  # Should be removed


class TestExplosion:
    """Test cases for Explosion entity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        yield
        pygame.quit()

    def test_explosion_initialization(self):
        """Test explosion is initialized correctly."""
        with patch.object(
            sprite_cache,
            "get",
            return_value=[pygame.Surface((20, 20)) for _ in range(5)],
        ):
            explosion = Explosion(300, 300)
            assert explosion.rect.centerx == 300
            assert explosion.rect.centery == 300
            assert explosion.current_frame == 0
            assert explosion.animation_speed == 2

    def test_explosion_animation(self):
        """Test explosion animation progression."""
        with patch.object(
            sprite_cache,
            "get",
            return_value=[pygame.Surface((20, 20)) for _ in range(5)],
        ):
            explosion = Explosion(300, 300)
            group = pygame.sprite.Group(explosion)

            # Test animation frames
            for frame in range(5):
                assert explosion.current_frame == frame
                explosion.update()
                explosion.update()  # Two updates per frame (animation_speed = 2)

            # After all frames, explosion should be removed
            assert len(group) == 0


class TestEnemyGroup:
    """Test cases for EnemyGroup management."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        pygame.init()
        self.enemy_group = EnemyGroup()
        yield
        pygame.quit()

    def test_create_formation(self):
        """Test enemy formation creation."""
        self.enemy_group.create_formation(1)
        assert len(self.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS

    def test_create_formation_wave_2(self):
        """Test enemy formation for wave 2 includes elite enemies."""
        # Create formation for wave 2
        self.enemy_group.create_formation(2)
        assert len(self.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS

        # Count elite enemies - should be ~10% of total
        elite_enemies = [e for e in self.enemy_group.enemies if e.is_elite]
        total_enemies = ENEMY_ROWS * ENEMY_COLS
        expected_elite_count = int(total_enemies * 0.1)  # 10% elite enemies

        # Allow for some variation due to randomness
        assert len(elite_enemies) >= expected_elite_count - 1
        assert len(elite_enemies) <= expected_elite_count + 2

    def test_create_formation_increasing_elites(self):
        """Test elite enemy percentage increases with waves."""
        # Wave 2: 10%
        self.enemy_group.create_formation(2)
        wave2_elites = sum(1 for e in self.enemy_group.enemies if e.is_elite)

        # Wave 3: 12%
        self.enemy_group.create_formation(3)
        wave3_elites = sum(1 for e in self.enemy_group.enemies if e.is_elite)

        # Wave 3 should have more elite enemies (allowing for randomness)
        total_enemies = ENEMY_ROWS * ENEMY_COLS
        expected_wave2 = int(total_enemies * 0.1)
        expected_wave3 = int(total_enemies * 0.12)

        # Check ranges due to randomness
        assert wave2_elites >= expected_wave2 - 1
        assert wave3_elites >= expected_wave3 - 1

    def test_create_formation_with_difficulty(self):
        """Test enemy formation with difficulty modifier."""
        self.enemy_group.create_formation(1, 1.5)  # Hard difficulty
        assert len(self.enemy_group.enemies) == ENEMY_ROWS * ENEMY_COLS

    def test_edge_detection_right(self):
        """Test formation detects right edge."""
        self.enemy_group.create_formation(1)
        # Move an enemy to right edge
        enemy = next(iter(self.enemy_group.enemies))
        enemy.rect.right = SCREEN_WIDTH - 5
        enemy.direction = 1

        self.enemy_group.update()

        # All enemies should have reversed direction
        for enemy in self.enemy_group.enemies:
            assert enemy.direction == -1

    def test_edge_detection_left(self):
        """Test formation detects left edge."""
        self.enemy_group.create_formation(1)

        # First make all enemies move left
        for enemy in self.enemy_group.enemies:
            enemy.direction = -1

        # Move an enemy to left edge
        test_enemy = next(iter(self.enemy_group.enemies))
        test_enemy.rect.left = 5

        self.enemy_group.update()

        # All enemies should have reversed direction
        for enemy in self.enemy_group.enemies:
            assert enemy.direction == 1

    def test_freeze_functionality(self):
        """Test enemy freeze functionality."""
        self.enemy_group.create_formation(1)
        current_time = 1000

        with patch("pygame.time.get_ticks", return_value=current_time):
            self.enemy_group.freeze(5000)

        assert self.enemy_group.frozen is True
        assert self.enemy_group.freeze_end_time == current_time + 5000

        # Test enemies don't move when frozen
        enemy = next(iter(self.enemy_group.enemies))
        initial_x = enemy.rect.x
        self.enemy_group.update()
        assert enemy.rect.x == initial_x  # Should not move

        # Test freeze expiration
        with patch("pygame.time.get_ticks", return_value=current_time + 5001):
            self.enemy_group.update()
        assert self.enemy_group.frozen is False

    def test_get_bottom_enemies(self):
        """Test getting bottom enemies for shooting."""
        self.enemy_group.create_formation(1)
        bottom_enemies = self.enemy_group.get_bottom_enemies()

        # Should have one enemy per column
        assert len(bottom_enemies) <= ENEMY_COLS

        # Each should be the lowest in their column
        for bottom_enemy in bottom_enemies:
            for other_enemy in self.enemy_group.enemies:
                if (
                    abs(bottom_enemy.rect.centerx - other_enemy.rect.centerx)
                    < ENEMY_SPACING_X // 2
                    and other_enemy != bottom_enemy
                ):
                    assert bottom_enemy.rect.bottom >= other_enemy.rect.bottom

    def test_is_empty(self):
        """Test empty check."""
        assert self.enemy_group.is_empty() is True
        self.enemy_group.create_formation(1)
        assert self.enemy_group.is_empty() is False

    def test_check_player_collision(self):
        """Test player collision detection."""
        self.enemy_group.create_formation(1)
        player_rect = pygame.Rect(400, 500, 30, 25)

        # Initially no collision
        assert self.enemy_group.check_player_collision(player_rect) is False

        # Move an enemy close to player
        enemy = next(iter(self.enemy_group.enemies))
        enemy.rect.bottom = player_rect.top - 30
        assert self.enemy_group.check_player_collision(player_rect) is True
