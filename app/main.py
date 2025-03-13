import pygame
import random
from obstacle import Obstacle, Power
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

obstacle_powers = ['solve', 'heal', 'invent', 'defend', 'connect']
npc_powers = {
    'Aria': [Power('solve', 5), Power('connect', 3)],
    'Brax': [Power('defend', 5), Power('invent', 1)],
    'Luna': [Power('heal', 5), Power('connect', 2)],
    'Kai': [Power('invent', 5), Power('solve', 3)],
    'Zara': [Power('connect', 5), Power('heal', 1)]
}

# create obstacle sprites with the same color
obstacles = pygame.sprite.Group()
for i in range(5):
    x = random.randint(0, COLS-1)
    y = random.randint(0, ROWS-1)
    width = random.randint(1, 3)
    height = random.randint(1, 3)
    # choose 2 random powers for the obstacle
    powers = [Power(random.choice(obstacle_powers), random.randint(1, 5)) for _ in range(2)]
    powers.append(Power('lead', 1)) # All obstacles need a leader to be passed.
    obstacle = Obstacle(x, y, width, height, powers, grid)
    obstacles.add(obstacle)

# Create player and NPCs
player = Player(0, 0, player_image, grid, screen, font)

scripted_npcs = []
for name in npc_powers.keys():
    image = pygame.image.load(f"./data/sprites/{name}.PNG")
    image = pygame.transform.scale(image, (CELL_SIZE, CELL_SIZE))
    scripted_npcs.append(NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), name, image, grid, screen, npc_powers[name]))

generated_npcs = [NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), str(i), None, grid, screen) for i in range(3)]
npcs = scripted_npcs + generated_npcs

characters = pygame.sprite.Group()
characters.add(player)
for npc in npcs:
    characters.add(npc)

# Main game loop
running = True
clock = pygame.time.Clock()

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
                        if not npc.following:
                            npc.freeze = True
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
            elif event.key == pygame.K_k:
                for obstacle in obstacles:
                    if player.is_next_to(obstacle):
                        player.attempt_kill_obstacle(obstacle)
                        break

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
    characters.draw(screen)
    obstacles.draw(screen)
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
