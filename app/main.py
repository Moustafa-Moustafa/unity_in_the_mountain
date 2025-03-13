import pygame
import random
from conversation import talk_to_character
from settings import WIDTH, HEIGHT, ROWS, COLS, CELL_SIZE, FPS, WHITE, BLACK, BLUE
from player import Player
from npc import NPC

# Initialize Pygame
pygame.init()

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

# Obstacles
obstacles = [(4, 4), (4, 5), (5, 4), (5, 5), (10, 10), (15, 15)]
for x, y in obstacles:
    grid[y][x] = 'obstacle'

# Create player and NPCs
player = Player(0, 0, player_image, grid, screen, font)
scripted_npcs = [NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), name, npc_images[name], grid, screen) for name in npc_names]
generated_npcs = [NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), str(i), None, grid, screen) for i in range(3)]
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
