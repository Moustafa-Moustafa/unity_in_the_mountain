import pygame
import random
from player import Player
from settings import DIRECTIONS, CELL_SIZE, COLS, ROWS, RED

class NPC(Player):
    def __init__(self, x, y, speed, label, image, grid, screen, powers=[]):
        if not image:
            image = pygame.Surface((CELL_SIZE, CELL_SIZE))
            image.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        super().__init__(x, y, image, grid, screen, pygame.font.SysFont(None, 24))
        self.freeze = False
        self.speed = speed
        self.move_counter = 0
        self.label = label
        self.following = False
        self.powers = powers

    def move_random(self):
        if not self.freeze and not self.following:
            self.move_counter += 1
            if self.move_counter >= self.speed:
                self.move_counter = 0
                dx, dy = random.choice(DIRECTIONS)
                new_x = (self.x + dx)
                new_y = (self.y + dy)
                if 0 <= new_x < COLS and 0 <= new_y < ROWS and self.grid[new_y][new_x] is None:
                    self.grid[self.y][self.x] = None
                    self.x = new_x
                    self.y = new_y
                    self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                    self.grid[self.y][self.x] = self

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
            if 0 <= new_x < COLS and 0 <= new_y < ROWS and self.grid[new_y][new_x] is None:
                self.grid[self.y][self.x] = None
                self.x = new_x
                self.y = new_y
                self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                self.grid[self.y][self.x] = self

    def draw(self):
        self.screen.blit(self.image, self.rect.topleft)
        label_surface = self.font.render(self.label, True, RED)
        self.screen.blit(label_surface, (self.rect.x + 5, self.rect.y + 5))
