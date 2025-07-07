"""Unit tests for game entities."""

import unittest
import pygame
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entities import Player, Enemy, Bullet, Bonus, Explosion, EnemyGroup
from config import *


class TestPlayer(unittest.TestCase):
    """Test cases for Player entity."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.player = Player(400, 500)

    def test_player_initialization(self):
        """Test player is initialized correctly."""
        self.assertEqual(self.player.rect.centerx, 400)
        self.assertEqual(self.player.rect.centery, 500)
        self.assertEqual(self.player.speed, PLAYER_SPEED)
        self.assertEqual(self.player.lives, PLAYER_LIVES)
        self.assertEqual(self.player.score, 0)

    def test_player_movement_left(self):
        """Test player moves left correctly."""
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x - PLAYER_SPEED)

    def test_player_movement_right(self):
        """Test player moves right correctly."""
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x + PLAYER_SPEED)

    def test_player_boundary_left(self):
        """Test player can't move past left boundary."""
        self.player.rect.left = 5
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x - PLAYER_SPEED)

        self.player.rect.left = 0
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x)  # Should not move

    def test_player_boundary_right(self):
        """Test player can't move past right boundary."""
        self.player.rect.right = SCREEN_WIDTH - 5
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x + PLAYER_SPEED)

        self.player.rect.right = SCREEN_WIDTH
        initial_x = self.player.rect.x
        self.player.update(keys)
        self.assertEqual(self.player.rect.x, initial_x)  # Should not move

    def test_player_can_shoot(self):
        """Test player shooting cooldown."""
        current_time = 1000
        self.assertTrue(self.player.can_shoot(current_time))

        # Shoot and check cooldown
        bullet = self.player.shoot(current_time)
        self.assertIsInstance(bullet, Bullet)
        self.assertFalse(self.player.can_shoot(current_time + 100))
        self.assertTrue(self.player.can_shoot(current_time + PLAYER_SHOOT_COOLDOWN + 1))

    def test_player_hit(self):
        """Test player loses life when hit."""
        initial_lives = self.player.lives
        self.player.hit()
        self.assertEqual(self.player.lives, initial_lives - 1)

    def test_player_is_alive(self):
        """Test player alive status."""
        self.assertTrue(self.player.is_alive())
        self.player.lives = 1
        self.assertTrue(self.player.is_alive())
        self.player.lives = 0
        self.assertFalse(self.player.is_alive())


class TestEnemy(unittest.TestCase):
    """Test cases for Enemy entity."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.enemy = Enemy(100, 100, 0)

    def test_enemy_initialization(self):
        """Test enemy is initialized correctly."""
        self.assertEqual(self.enemy.rect.x, 100)
        self.assertEqual(self.enemy.rect.y, 100)
        self.assertEqual(self.enemy.row, 0)
        self.assertEqual(self.enemy.direction, 1)
        self.assertEqual(self.enemy.drop_distance, 0)

    def test_enemy_horizontal_movement(self):
        """Test enemy moves horizontally."""
        initial_x = self.enemy.rect.x
        self.enemy.update()
        self.assertEqual(self.enemy.rect.x, initial_x + ENEMY_SPEED_X)

    def test_enemy_reverse_direction(self):
        """Test enemy reverses direction and drops."""
        self.enemy.reverse_direction()
        self.assertEqual(self.enemy.direction, -1)
        self.assertEqual(self.enemy.drop_distance, ENEMY_SPEED_Y)

    def test_enemy_drop_movement(self):
        """Test enemy drops down when required."""
        initial_y = self.enemy.rect.y
        self.enemy.drop_distance = 10
        self.enemy.update()
        self.assertEqual(self.enemy.rect.y, initial_y + 2)
        self.assertEqual(self.enemy.drop_distance, 8)

    @patch("random.random")
    def test_enemy_can_shoot(self, mock_random):
        """Test enemy shooting probability."""
        mock_random.return_value = 0.0001
        self.assertTrue(self.enemy.can_shoot())

        mock_random.return_value = 0.01
        self.assertFalse(self.enemy.can_shoot())

    def test_enemy_shoot(self):
        """Test enemy creates bullet."""
        bullet = self.enemy.shoot()
        self.assertIsInstance(bullet, Bullet)
        self.assertEqual(bullet.rect.centerx, self.enemy.rect.centerx)
        self.assertEqual(bullet.rect.centery, self.enemy.rect.bottom)
        self.assertEqual(bullet.speed, ENEMY_BULLET_SPEED)
        self.assertEqual(bullet.owner, "enemy")


class TestBullet(unittest.TestCase):
    """Test cases for Bullet entity."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()

    def test_player_bullet_initialization(self):
        """Test player bullet is initialized correctly."""
        bullet = Bullet(100, 200, -BULLET_SPEED, "player")
        self.assertEqual(bullet.rect.centerx, 100)
        self.assertEqual(bullet.rect.centery, 200)
        self.assertEqual(bullet.speed, -BULLET_SPEED)
        self.assertEqual(bullet.owner, "player")

    def test_enemy_bullet_initialization(self):
        """Test enemy bullet is initialized correctly."""
        bullet = Bullet(150, 250, ENEMY_BULLET_SPEED, "enemy")
        self.assertEqual(bullet.rect.centerx, 150)
        self.assertEqual(bullet.rect.centery, 250)
        self.assertEqual(bullet.speed, ENEMY_BULLET_SPEED)
        self.assertEqual(bullet.owner, "enemy")

    def test_bullet_movement(self):
        """Test bullet moves correctly."""
        bullet = Bullet(100, 200, -5, "player")
        initial_y = bullet.rect.y
        bullet.update()
        self.assertEqual(bullet.rect.y, initial_y - 5)

    def test_bullet_removal_top(self):
        """Test bullet is removed when going off top."""
        # Create bullet with centery that will make it go off screen after update
        # Bullet height is 10, so centery=5 means top=0, bottom=10
        bullet = Bullet(100, 5, -15, "player")  # centery=5, moving up at speed -15
        group = pygame.sprite.Group(bullet)
        bullet.update()  # After update, centery=-10, so bottom will be -5
        self.assertEqual(len(group), 0)  # Bullet should be removed

    def test_bullet_removal_bottom(self):
        """Test bullet is removed when going off bottom."""
        # Create bullet with centery that will make it go off screen after update
        # Bullet height is 10, so centery=595 means top=590, bottom=600
        bullet = Bullet(100, SCREEN_HEIGHT - 5, 20, "enemy")  # centery at bottom edge
        group = pygame.sprite.Group(bullet)
        bullet.update()  # After update, centery=615, so top will be 610 > SCREEN_HEIGHT
        self.assertEqual(len(group), 0)  # Bullet should be removed


class TestBonus(unittest.TestCase):
    """Test cases for Bonus entity."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()

    @patch("random.randint")
    def test_bonus_initialization(self, mock_randint):
        """Test bonus is initialized correctly."""
        mock_randint.return_value = 2
        bonus = Bonus(200, 100)
        self.assertEqual(bonus.rect.centerx, 200)
        self.assertEqual(bonus.rect.centery, 100)
        self.assertEqual(bonus.speed, BONUS_FALL_SPEED)
        self.assertEqual(bonus.value, BONUS_SCORE)
        self.assertEqual(bonus.shape_type, 2)

    def test_bonus_movement(self):
        """Test bonus falls correctly."""
        bonus = Bonus(200, 100)
        initial_y = bonus.rect.y
        bonus.update()
        self.assertEqual(bonus.rect.y, initial_y + BONUS_FALL_SPEED)

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
        self.assertEqual(len(group), 0)  # Bonus should be removed


class TestEnemyGroup(unittest.TestCase):
    """Test cases for EnemyGroup management."""

    def setUp(self):
        """Set up test fixtures."""
        pygame.init()
        self.enemy_group = EnemyGroup()

    def test_create_formation(self):
        """Test enemy formation creation."""
        self.enemy_group.create_formation(1)
        self.assertEqual(len(self.enemy_group.enemies), ENEMY_ROWS * ENEMY_COLS)

    def test_create_formation_wave_2(self):
        """Test enemy formation for wave 2."""
        self.enemy_group.create_formation(2)
        self.assertEqual(len(self.enemy_group.enemies), ENEMY_ROWS * ENEMY_COLS)

    def test_edge_detection_right(self):
        """Test formation detects right edge."""
        self.enemy_group.create_formation(1)
        # Move an enemy to right edge
        enemy = list(self.enemy_group.enemies)[0]
        enemy.rect.right = SCREEN_WIDTH - 5
        enemy.direction = 1

        self.enemy_group.update()

        # All enemies should have reversed direction
        for enemy in self.enemy_group.enemies:
            self.assertEqual(enemy.direction, -1)

    def test_edge_detection_left(self):
        """Test formation detects left edge."""
        self.enemy_group.create_formation(1)

        # First make all enemies move left
        for enemy in self.enemy_group.enemies:
            enemy.direction = -1

        # Move an enemy to left edge
        test_enemy = list(self.enemy_group.enemies)[0]
        test_enemy.rect.left = 5

        self.enemy_group.update()

        # All enemies should have reversed direction
        for enemy in self.enemy_group.enemies:
            self.assertEqual(enemy.direction, 1)

    def test_get_bottom_enemies(self):
        """Test getting bottom enemies for shooting."""
        self.enemy_group.create_formation(1)
        bottom_enemies = self.enemy_group.get_bottom_enemies()

        # Should have one enemy per column
        self.assertLessEqual(len(bottom_enemies), ENEMY_COLS)

        # Each should be the lowest in their column
        for bottom_enemy in bottom_enemies:
            for other_enemy in self.enemy_group.enemies:
                if (
                    abs(bottom_enemy.rect.centerx - other_enemy.rect.centerx)
                    < ENEMY_SPACING_X // 2
                    and other_enemy != bottom_enemy
                ):
                    self.assertGreaterEqual(
                        bottom_enemy.rect.bottom, other_enemy.rect.bottom
                    )

    def test_is_empty(self):
        """Test empty check."""
        self.assertTrue(self.enemy_group.is_empty())
        self.enemy_group.create_formation(1)
        self.assertFalse(self.enemy_group.is_empty())

    def test_check_player_collision(self):
        """Test player collision detection."""
        self.enemy_group.create_formation(1)
        player_rect = pygame.Rect(400, 500, 30, 25)

        # Initially no collision
        self.assertFalse(self.enemy_group.check_player_collision(player_rect))

        # Move an enemy close to player
        enemy = list(self.enemy_group.enemies)[0]
        enemy.rect.bottom = player_rect.top - 30
        self.assertTrue(self.enemy_group.check_player_collision(player_rect))


if __name__ == "__main__":
    unittest.main()
