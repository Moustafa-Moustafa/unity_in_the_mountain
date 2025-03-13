import pygame
import random
from conversation import talk_to_character

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 20, 20
CELL_SIZE = WIDTH // COLS
FPS = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Directions
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Unity in the Mountains")

# Initialize grid
grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

# Initialize Pygame font
pygame.font.init()
font = pygame.font.SysFont(None, 48)

# Load images for player and NPCs
player_image = pygame.image.load('./data/sprites/player.PNG')
player_image = pygame.transform.scale(player_image, (CELL_SIZE, CELL_SIZE))

npc_images = {}
npc_names = ['Aria', 'Brax', 'Luna', 'Kai', 'Zara']
for name in npc_names:
    npc_image = pygame.image.load(f"./data/sprites/{name}.PNG")
    npc_image = pygame.transform.scale(npc_image, (CELL_SIZE, CELL_SIZE))
    npc_images[name] = npc_image

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * CELL_SIZE, y * CELL_SIZE)
        self.x = x
        self.y = y
        self.freeze = False
        self.party = []
        grid[y][x] = self

    def gain_party_member(self, npc):
        npc.following = True
        self.party.append(npc)

        celebration_surface = pygame.Surface((WIDTH, HEIGHT // 2))
        celebration_surface.fill(WHITE)
        text_surface = font.render(f"{npc.label} has joined your party!", True, BLACK)
        celebration_surface.blit(text_surface, (celebration_surface.get_width() // 2 - text_surface.get_width() // 2, celebration_surface.get_height() // 2 - text_surface.get_height() // 2))
        screen.blit(celebration_surface, (0, 0))
        pygame.display.flip()
        pygame.time.wait(3000)


    def move(self, dx, dy):
        if not self.freeze:
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS and grid[new_y][new_x] is None:
                grid[self.y][self.x] = None
                self.x = new_x
                self.y = new_y
                self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                grid[self.y][self.x] = self

# NPC class
class NPC(Player):
    def __init__(self, x, y, speed, label):
        super().__init__(x, y)
        if label in npc_images:
            self.image = npc_images[label]
        else:
            self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
            self.image.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        self.speed = speed
        self.move_counter = 0
        self.label = label
        self.font = pygame.font.SysFont(None, 24)
        self.following = False

    def move_random(self):
        if not self.freeze and not self.following:
            self.move_counter += 1
            if self.move_counter >= self.speed:
                self.move_counter = 0
                dx, dy = random.choice(DIRECTIONS)
                new_x = (self.x + dx)
                new_y = (self.y + dy)
                if 0 <= new_x < COLS and 0 <= new_y < ROWS and grid[new_y][new_x] is None:
                    grid[self.y][self.x] = None
                    self.x = new_x
                    self.y = new_y
                    self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                    grid[self.y][self.x] = self

    def follow_player(self, player):
        if self.following:
            dx = player.x - self.x
            dy = player.y - self.y
            if abs(dx) > 1:
                dx = 1 if dx > 0 else -1
            if abs(dy) > 1:
                dy = 1 if dy > 0 else -1
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS and grid[new_y][new_x] is None:
                grid[self.y][self.x] = None
                self.x = new_x
                self.y = new_y
                self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                grid[self.y][self.x] = self

    def draw(self):
        screen.blit(self.image, self.rect.topleft)
        label_surface = self.font.render(self.label, True, RED)
        screen.blit(label_surface, (self.rect.x + 5, self.rect.y + 5))

# Obstacles
obstacles = [(4, 4), (4, 5), (5, 4), (5, 5), (10, 10), (15, 15)]
for x, y in obstacles:
    grid[y][x] = 'obstacle'

# Create player and NPCs
player = Player(0, 0)
scripted_npcs = [NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), name) for name in npc_names]
generated_npcs = [NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), i) for i in range(3)]
npcs = scripted_npcs + generated_npcs

# Main game loop
running = True
clock = pygame.time.Clock()
following_npcs = 0

while running and len(player.party) <= 5:
    clock.tick(FPS)
    is_talking = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_talking:
                for npc in npcs:
                    if abs(player.x - npc.x) <= 1 and abs(player.y - npc.y) <= 1:
                        npc.freeze = not npc.freeze
                        if npc.freeze:
                            print(f"Conversation started with NPC {npc.label}")
                            is_talking = True
                            talk_to_character(player, npc, npcs.index(npc), screen)
                        break
            elif event.key == pygame.K_UP:
                player.move(0, -1)
            elif event.key == pygame.K_DOWN:
                player.move(0, 1)
            elif event.key == pygame.K_LEFT:
                player.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                player.move(1, 0)
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                is_talking = False

    # Unfreeze NPCs if player moves away
    for npc in npcs:
        if abs(player.x - npc.x) > 1 or abs(player.y - npc.y) > 1:
            npc.freeze = False

    # Move NPCs
    for npc in npcs:
        if npc.following:
            npc.follow_player(player)
        else:
            npc.move_random()

    # Draw everything
    screen.fill(WHITE)
    for x, y in obstacles:
        pygame.draw.rect(screen, BLUE, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    characters = pygame.sprite.Group()
    characters.add(player)
    for npc in npcs:
        characters.add(npc)
    characters.draw(screen)
    pygame.display.flip()

# Display game over banner
screen.fill(WHITE)
if (len(player.party) >= 5):
    game_over_surface = font.render("Game Over\n\nYou have a full party.\nThe adventure is afoot!", True, BLACK)
else:
    game_over_surface = font.render("Game Over\n\nYou didn't gather enough party members.\nMaybe another time.", True, BLACK)
screen.blit(game_over_surface, (WIDTH // 2 - game_over_surface.get_width() // 2, HEIGHT // 2 - game_over_surface.get_height() // 2))
pygame.display.flip()
pygame.time.wait(3000)

pygame.quit()
