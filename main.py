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
    sprite = pygame.Surface((20, 15), pygame.SRCALPHA)
    # Enemy body
    pygame.draw.rect(sprite, NEON_PINK, (2, 5, 16, 8))
    pygame.draw.rect(sprite, NEON_PURPLE, (0, 7, 20, 4))
    # Eyes
    pygame.draw.circle(sprite, NEON_YELLOW, (6, 9), 2)
    pygame.draw.circle(sprite, NEON_YELLOW, (14, 9), 2)
    # Antennae
    pygame.draw.line(sprite, NEON_GREEN, (5, 5), (3, 0), 2)
    pygame.draw.line(sprite, NEON_GREEN, (15, 5), (17, 0), 2)
    return sprite

def create_bullet_sprite():
    sprite = pygame.Surface((6, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(sprite, NEON_GREEN, (0, 0, 6, 10))
    pygame.draw.ellipse(sprite, NEON_YELLOW, (1, 1, 4, 8))
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

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Space Invaders")
    clock = pygame.time.Clock()
    
    player = Player()
    enemies = []
    score = 0
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
            if enemy.y > HEIGHT:
                enemies.remove(enemy)
        
        # Check collisions
        for bullet in player.bullets[:]:
            for enemy in enemies[:]:
                if (enemy.x < bullet[0] < enemy.x + 20 and 
                    enemy.y < bullet[1] < enemy.y + 15):
                    enemies.remove(enemy)
                    player.bullets.remove(bullet)
                    score += 10
                    break
        
        # Spawn new enemies
        if len(enemies) < 20 and random.randint(1, 60) == 1:
            enemies.append(Enemy(random.randint(0, WIDTH - 20), 0))
        
        # Draw everything
        screen.fill(BLACK)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        
        # Draw score with neon effect
        score_text = font.render(f"Score: {score}", True, NEON_GREEN)
        screen.blit(score_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
