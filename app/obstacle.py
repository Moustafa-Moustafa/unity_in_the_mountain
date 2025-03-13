import pygame
from settings import CELL_SIZE, BLUE

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, powers, grid):
        super().__init__()
        image = pygame.Surface((width*CELL_SIZE, height*CELL_SIZE))
        image.fill(BLUE)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * CELL_SIZE, y * CELL_SIZE)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.powers = powers
        self.grid = grid
        self.fill_grid(self)

    def kill(self):
        self.fill_grid(None)
        super().kill()

    def fill_grid(self, value):
        for i in range(self.x, self.x + self.width):
            for j in range(self.y, self.y + self.height):
                if 0 <= i < len(self.grid[0]) and 0 <= j < len(self.grid):
                    self.grid[j][i] = value

class Power():
    ## class to represent the power of an NPC. Also the powers needed to bypass the obstacles
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount
        