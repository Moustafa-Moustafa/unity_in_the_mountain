import pygame
import random
import settings
import ui

from obstacle import Obstacle, Power
from conversation import talk_to_character
from settings import WIDTH, HEIGHT, ROWS, COLS, CELL_SIZE, FPS, WHITE, BLACK
from player import Player
from npc import NPC
import os

def draw_treasure():
    if ui.grid[treasure_y][treasure_x] is None:  # Only draw the treasure if the obstacle is removed
        ui.screen.blit(treasure_image, (treasure_x * CELL_SIZE, treasure_y * CELL_SIZE))

# Initialize
pygame.init()
ui.initialize_ui()

obstacle_requirements = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']

# Create obstacle sprites with random colors
obstacles = pygame.sprite.Group()
for i in range(5):
    x = random.randint(0, COLS-1)
    y = random.randint(0, ROWS-1)
    width = random.randint(1, 3)
    height = random.randint(1, 3)
    powers = random.sample([Power(power, sum(random.randint(1, 6) for _ in range(3))) for power in obstacle_requirements], 2)
    obstacle = Obstacle(x, y, width, height, powers)
    obstacles.add(obstacle)

treasure_image = pygame.image.load('./data/sprites/treasure.png')
treasure_image = pygame.transform.scale(treasure_image, (CELL_SIZE, CELL_SIZE))
treasure_obstacle = random.choice(obstacles.sprites())
treasure_x, treasure_y = treasure_obstacle.x, treasure_obstacle.y

player = Player(0, 0)

authored_npcs_path = './data/characters/authored'
generated_npcs_path = './data/characters/generated'

npcs = []
num_npcs = settings.NUMBER_OF_NPCS

authored_files = [f for f in os.listdir(authored_npcs_path) if os.path.isdir(os.path.join(authored_npcs_path, f))]
num_of_authored_npcs = min(5, len(authored_files))
random.shuffle(authored_files)
for character_name in authored_files[:num_of_authored_npcs]:
    npcs.append(NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), character_name))

generated_npcs = os.listdir(generated_npcs_path)
while len(npcs) < num_npcs:
    if random.random() < 0.8 and len(generated_npcs) > 0:
        character_name = random.choice(generated_npcs)
        npcs.append(NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), character_name))
        generated_npcs.remove(character_name)
    else:
        x = random.randint(0, COLS-1)
        y = random.randint(0, ROWS-1)
        speed = random.randint(2, 5)
        npcs.append(NPC(x, y, speed))

characters = pygame.sprite.Group()
characters.add(player)
for npc in npcs:
    characters.add(npc)

# Main game loop
running = True
clock = pygame.time.Clock()

while running and len(player.party) <= 5:
    clock.tick(FPS)

    for npc in npcs:
        if player.is_next_to(npc) and not npc.following:
            if random.random() < 0.8:
                npc.freeze = not npc.freeze
            
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
                            talk_to_character(player, npc, npcs.index(npc))
                            break
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                player.move(0, -1)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                player.move(0, 1)
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                player.move(-1, 0)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
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

    # Check if player reached the treasure
    if player.x == treasure_x and player.y == treasure_y:
        running = False
        print("Congratulations! You found the treasure!")

    # Draw everything
    ui.screen.fill(WHITE)
    characters.draw(ui.screen)
    obstacles.draw(ui.screen)
    draw_treasure()
    ui.draw_side_window(player, obstacles, npcs)
    pygame.display.flip()

# Display game over banner
ui.screen.fill(WHITE)
if player.x == treasure_x and player.y == treasure_y:
    game_over_surface = ui.font.render("Congratulations! You found the treasure!", True, BLACK)
else:
    game_over_surface = ui.font.render("Game Over\n\nYou didn't find the treasure.\nMaybe another time.", True, BLACK)
ui.screen.blit(game_over_surface, (WIDTH // 2 - game_over_surface.get_width() // 2, HEIGHT // 2 - game_over_surface.get_height() // 2))
pygame.display.flip()
pygame.time.wait(3000)

pygame.quit()