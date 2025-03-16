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
import json
import tkinter as tk
from tkinter import messagebox

obstacles = None
treasure_x = None
treasure_y = None
treasure_image = None
player = None
npcs = None
characters = None

def save_game(filename):
    game_state = {
        'player': player.to_json(),
        'npcs': [npc.to_json() for npc in npcs],
        'obstacles': [obstacle.to_json() for obstacle in obstacles],
        'treasure': {'x': treasure_x, 'y': treasure_y}
    }
    with open(filename, 'w') as f:
        json.dump(game_state, f)

def load_game(filename):
    global player, npcs, obstacles, treasure_x, treasure_y

    with open(filename, 'r') as f:
        game_state = json.load(f)

    player = Player.from_json(game_state['player'])
    npcs = [NPC.from_json(npc_data) for npc_data in game_state['npcs']]
    obstacles = pygame.sprite.Group()
    for obstacle_data in game_state['obstacles']:
        obstacle = Obstacle.from_json(obstacle_data)
        obstacles.add(obstacle)
    treasure_x = game_state['treasure']['x']
    treasure_y = game_state['treasure']['y']

def draw_treasure():
    if ui.grid[treasure_y][treasure_x] is None:  # Only draw the treasure if the obstacle is removed
        ui.screen.blit(treasure_image, (treasure_x * CELL_SIZE, treasure_y * CELL_SIZE))

def initialize():
    pygame.init()
    ui.initialize_ui()

def create_obstacles():
    global obstacles

    obstacle_requirements = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']

    # Create obstacle sprites with random colors
    obstacles = pygame.sprite.Group()
    for i in range(5):
        x = random.randint(0, COLS-1)
        y = random.randint(0, ROWS-1)
        width = random.randint(1, 3)
        height = random.randint(1, 3)
        powers = random.sample([Power(power, sum(random.randint(1, 6) for _ in range(settings.DIFFICULTY))) for power in obstacle_requirements], 2)
        obstacle = Obstacle(x, y, width, height, powers)
        obstacles.add(obstacle)

def create_treasure():
    global treasure_x, treasure_y, treasure_image

    treasure_image = pygame.image.load('./data/sprites/treasure.png')
    treasure_image = pygame.transform.scale(treasure_image, (CELL_SIZE, CELL_SIZE))
    treasure_obstacle = random.choice(obstacles.sprites())
    treasure_x, treasure_y = treasure_obstacle.x, treasure_obstacle.y

def create_player():
    global player
    player = Player(0, 0)

def create_npcs():    
    global npcs

    npcs = []
    num_npcs = settings.NUMBER_OF_NPCS

    authored_files = [f for f in os.listdir(settings.authored_npcs_path) if os.path.isdir(os.path.join(settings.authored_npcs_path, f))]
    num_of_authored_npcs = min(5, len(authored_files))
    random.shuffle(authored_files)
    for character_name in authored_files[:num_of_authored_npcs]:
        npcs.append(NPC(random.randint(0, COLS-1), random.randint(0, ROWS-1), random.randint(2, 5), character_name))

    generated_npcs = os.listdir(settings.generated_npcs_path)
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

def prepare_ui():
    global characters
    
    characters = pygame.sprite.Group()
    characters.add(player)
    for npc in npcs:
        characters.add(npc)

initialize()

if os.path.exists(settings.SAVE_FILENAME):
    def show_start_dialog():
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        result = messagebox.askquestion("Game Start", "Start a new game?", icon='question', type=messagebox.YESNO, default=messagebox.NO, detail="Click 'Yes' to start a new game or 'No' to load the saved game.")
        root.destroy()
        return result

    if show_start_dialog() == 'yes':
        create_obstacles()
        create_treasure()
        create_player()
        create_npcs()
    else:
        load_game(settings.SAVE_FILENAME)
else:
    create_obstacles()
    create_treasure()
    create_player()
    create_npcs()

prepare_ui()

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
                            talk_to_character(player, npc)
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

save_game(settings.SAVE_FILENAME)

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