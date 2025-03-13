import pygame
from obstacle import Power
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
        self.powers = [Power(name='lead', amount=1)]
        grid[y][x] = self

    def gain_party_member(self, npc):
        npc.following = True
        self.party.append(npc)

    def is_next_to(self, obstacle):
        return self.x >= obstacle.x - 1 and self.x <= obstacle.x + obstacle.width + 1 and \
                self.y >= obstacle.y - 1 and self.y <= obstacle.y + obstacle.height + 1

    def attempt_kill_obstacle(self, obstacle):
        if self.can_pass(obstacle):
            obstacle.kill()

    def can_pass(self, obstacle):
        # calculate the collective powers and amount of the party
        total_powers = {}
        for member in [self] + self.party:
            for power in member.powers:
                if power.name not in total_powers:
                    total_powers[power.name] = 0
                total_powers[power.name] += power.amount

        obstacle_powers = ', '.join([f"{power.name}: {power.amount}" for power in obstacle.powers])
        print(f"Obstacle at ({obstacle.x}, {obstacle.y}) needs powers: {obstacle_powers}")
        print(f"total_powers: {total_powers}")
        for power in obstacle.powers:
            if power.name not in total_powers or total_powers[power.name] < power.amount:
                return False
        return True


    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS and self.grid[new_y][new_x] is None:
            self.grid[self.y][self.x] = None
            self.x = new_x
            self.y = new_y
            self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
            self.grid[self.y][self.x] = self
