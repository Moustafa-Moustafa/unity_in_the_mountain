import pygame
from settings import CELL_SIZE, COLS, ROWS, WIDTH, HEIGHT, WHITE, BLACK

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image, grid, screen, font):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * CELL_SIZE, y * CELL_SIZE)
        self.x = x
        self.y = y
        self.freeze = False
        self.party = []
        self.grid = grid
        self.screen = screen
        self.font = font
        grid[y][x] = self

    def gain_party_member(self, npc):
        npc.following = True
        self.party.append(npc)

        celebration_surface = pygame.Surface((WIDTH, HEIGHT // 2))
        celebration_surface.fill(WHITE)
        text_surface = self.font.render(f"{npc.label} has joined your party!", True, BLACK)
        celebration_surface.blit(text_surface, (celebration_surface.get_width() // 2 - text_surface.get_width() // 2, celebration_surface.get_height() // 2 - text_surface.get_height() // 2))
        self.screen.blit(celebration_surface, (0, 0))
        pygame.display.flip()
        pygame.time.wait(3000)

    def move(self, dx, dy):
        if not self.freeze:
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x < COLS and 0 <= new_y < ROWS and self.grid[new_y][new_x] is None:
                self.grid[self.y][self.x] = None
                self.x = new_x
                self.y = new_y
                self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
                self.grid[self.y][self.x] = self
