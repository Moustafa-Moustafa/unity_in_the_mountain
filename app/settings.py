# Game Config
NUMBER_OF_NPCS = 7
DIFFICULTY = 8 # this defines the difficulty of destroying the obstacles, anything beliw 4 is likely too easy, above 12 is likely too hard. Increasing this increases the number of party members that will be needed.
SAVE_FILENAME = "data/save.json"

# Files
authored_npcs_path = './data/characters/authored'
generated_npcs_path = './data/characters/generated'

# UI
WIDTH, HEIGHT = 800, 800
SIDE_WIDTH = 200
ROWS, COLS = 20, 20
CELL_SIZE = WIDTH // COLS
FPS = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Directions
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

# Sprites
available_character_sprites_path = './data/sprites/available_characters'
character_sprites_path = './data/sprites/assigned_characters'
