import pygame
import random
import math

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
BLACK = (0, 0, 0)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 20, 147)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (138, 43, 226)
NEON_YELLOW = (255, 255, 0)

def create_player_sprite():
    sprite = pygame.Surface((30, 25), pygame.SRCALPHA)
    # Ship body
    pygame.draw.polygon(sprite, NEON_CYAN, [(15, 0), (0, 25), (30, 25)])
    pygame.draw.polygon(sprite, NEON_GREEN, [(15, 5), (5, 20), (25, 20)], 2)
    # Cockpit
    pygame.draw.circle(sprite, NEON_YELLOW, (15, 15), 3)
    return sprite

def create_enemy_sprite():
    sprite = pygame.Surface((26, 20), pygame.SRCALPHA)
    # Enemy body (30% larger)
    pygame.draw.rect(sprite, NEON_PINK, (3, 6, 20, 10))
    pygame.draw.rect(sprite, NEON_PURPLE, (0, 9, 26, 5))
    # Eyes
    pygame.draw.circle(sprite, NEON_YELLOW, (8, 12), 3)
    pygame.draw.circle(sprite, NEON_YELLOW, (18, 12), 3)
    # Antennae
    pygame.draw.line(sprite, NEON_GREEN, (6, 6), (4, 0), 2)
    pygame.draw.line(sprite, NEON_GREEN, (20, 6), (22, 0), 2)
    return sprite

def create_bullet_sprite():
    sprite = pygame.Surface((6, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sprite, NEON_GREEN, (0, 0, 6, 10))
    pygame.draw.ellipse(sprite, NEON_YELLOW, (1, 1, 4, 8))
    return sprite

def create_tetris_sprite(shape_type):
    sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
    colors = [NEON_CYAN, NEON_YELLOW, NEON_PURPLE, NEON_PINK, NEON_GREEN]
    color = colors[shape_type]
    
    shapes = [
        [(0,0),(1,0),(0,1),(1,1)],  # O
        [(1,0),(0,1),(1,1),(2,1)],  # T
        [(0,0),(1,0),(2,0),(3,0)],  # I
        [(0,1),(1,1),(1,0),(2,0)],  # S
        [(0,0),(1,0),(1,1),(2,1)]   # Z
    ]
    
    for x, y in shapes[shape_type]:
        pygame.draw.rect(sprite, color, (x*5, y*5, 5, 5))
    return sprite

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 50
        self.speed = 5
        self.bullets = []
        self.sprite = create_player_sprite()
        self.bullet_sprite = create_bullet_sprite()
    
    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 15:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - 15:
            self.x += self.speed
    
    def shoot(self):
        self.bullets.append([self.x + 12, self.y])
    
    def update_bullets(self):
        self.bullets = [[x, y - 7] for x, y in self.bullets if y > 0]
    
    def draw(self, screen):
        screen.blit(self.sprite, (self.x - 15, self.y))
        for bullet in self.bullets:
            screen.blit(self.bullet_sprite, (bullet[0] - 3, bullet[1] - 5))

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.sprite = create_enemy_sprite()
    
    def move(self):
        self.y += self.speed
    
    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class TetrisBonus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.shape_type = random.randint(0, 4)
        self.sprite = create_tetris_sprite(self.shape_type)
    
    def move(self):
        self.y += self.speed
    
    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Space Invaders")
    clock = pygame.time.Clock()
    
    player = Player()
    enemies = []
    bonuses = []
    score = 0
    kills = 0
    font = pygame.font.Font(None, 36)
    
    # Spawn initial enemies
    for row in range(5):
        for col in range(10):
            enemies.append(Enemy(col * 70 + 50, row * 40 + 50))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.shoot()
        
        keys = pygame.key.get_pressed()
        player.move(keys)
        player.update_bullets()
        
        # Move enemies
        for enemy in enemies[:]:
            enemy.move()
            if enemy.y > HEIGHT - 80:  # Remove before reaching player area
                enemies.remove(enemy)
        
        # Move bonuses
        for bonus in bonuses[:]:
            bonus.move()
            if bonus.y > HEIGHT:
                bonuses.remove(bonus)
        
        # Check collisions
        for bullet in player.bullets[:]:
            for enemy in enemies[:]:
                if (enemy.x < bullet[0] < enemy.x + 26 and 
                    enemy.y < bullet[1] < enemy.y + 20):
                    enemies.remove(enemy)
                    player.bullets.remove(bullet)
                    score += 10
                    kills += 1
                    
                    # Spawn tetris bonus at enemy position every 5-7 kills
                    if kills % random.randint(5, 7) == 0:
                        bonuses.append(TetrisBonus(enemy.x, enemy.y))
                    break
        
        # Check bonus collisions
        for bonus in bonuses[:]:
            if (player.x - 15 < bonus.x + 10 < player.x + 15 and 
                player.y < bonus.y + 20 < player.y + 25):
                bonuses.remove(bonus)
                score += 50
        
        # Spawn new enemies
        if len(enemies) < 20 and random.randint(1, 60) == 1:
            enemies.append(Enemy(random.randint(0, WIDTH - 26), 0))
        
        # Draw everything
        screen.fill(BLACK)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for bonus in bonuses:
            bonus.draw(screen)
        
        # Draw score with neon effect
        score_text = font.render(f"Score: {score}", True, NEON_GREEN)
        screen.blit(score_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
