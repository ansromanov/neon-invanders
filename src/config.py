"""Game configuration and constants."""

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (Neon theme)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 20, 147)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (138, 43, 226)
NEON_YELLOW = (255, 255, 0)
NEON_ORANGE = (255, 165, 0)
NEON_RED = (255, 0, 80)

# Player settings
PLAYER_SPEED = 5
PLAYER_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 250  # milliseconds

# Enemy settings
ENEMY_SPEED_X = 1
ENEMY_SPEED_Y = 20  # Drop distance
ENEMY_SHOOT_CHANCE = 0.001  # Per frame per enemy
ENEMY_BULLET_SPEED = 3
ENEMY_ROWS = 5
ENEMY_COLS = 10
ENEMY_SPACING_X = 70
ENEMY_SPACING_Y = 40
ENEMY_START_Y = 50

# Bullet settings
BULLET_SPEED = 7
BULLET_WIDTH = 6
BULLET_HEIGHT = 10

# Bonus settings
BONUS_FALL_SPEED = 2
BONUS_SCORE = 50
BONUS_SPAWN_CHANCE = 0.2  # Chance when enemy is killed


# Bonus types
class BonusType:
    EXTRA_LIFE = 0  # O-block (cyan) - adds 1 life
    FREEZE_ENEMIES = 1  # T-block (yellow) - stops enemies for 5 seconds
    TRIPLE_SHOT = 2  # I-block (purple) - fire 3 bullets in triangular pattern
    SHIELD = 3  # S-block (pink) - temporary shield
    RAPID_FIRE = 4  # Z-block (green) - faster shooting for 5 seconds


FREEZE_DURATION = 5000  # 5 seconds in milliseconds
RAPID_FIRE_DURATION = 5000  # 5 seconds
SHIELD_DURATION = 3000  # 3 seconds

# Scoring
ENEMY_SCORE = 10
WAVE_CLEAR_BONUS = 100


# Game states
class GameState:
    MENU = "menu"
    SETTINGS = "settings"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    WAVE_CLEAR = "wave_clear"


# Sound settings
SOUND_ENABLED = True
SOUND_VOLUME = 0.7
