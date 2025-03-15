import random
import pygame
import settings
import ui

from obstacle import Power

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("./data/sprites/player.png")
        self.image = pygame.transform.scale(self.image, (settings.CELL_SIZE, settings.CELL_SIZE))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * settings.CELL_SIZE, y * settings.CELL_SIZE)
        self.x = x
        self.y = y
        self.width = 1
        self.height = 1
        self.freeze = False
        self.party = []
        ui.grid[y][x] = self
        
        self.meta_data = {
            "name": "Player",
            "statistics": {
                "strength": sum(random.randint(1, 6) for _ in range(3)),
                "intelligence": sum(random.randint(1, 6) for _ in range(3)),
                "agility": sum(random.randint(1, 6) for _ in range(3)),
                "wisdom": sum(random.randint(1, 6) for _ in range(3)),
                "charisma": sum(random.randint(1, 6) for _ in range(3))
            },
            "level": 1,
            "experience": 0,
            "gold": 0,
            "inventory": []
        }

    def gain_party_member(self, npc):
        npc.following = True
        self.party.append(npc)

    def is_next_to(self, object):
        return self.x >= object.x - 1 and self.x <= object.x + object.width  and \
                self.y >= object.y - 1 and self.y <= object.y + object.height 

    def attempt_kill_obstacle(self, obstacle):
        if self.can_pass(obstacle):
            obstacle.kill()

    def get_total_stats(self):
        total_stats = self.meta_data["statistics"].copy()

        for member in self.party:
            stats = member.meta_data["statistics"]
            for stat, value in stats.items():
                if stat in total_stats:
                    total_stats[stat] += value
                else:
                    total_stats[stat] = value

        return total_stats

    def can_pass(self, obstacle):
        total_powers = self.get_total_stats()
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
        if 0 <= new_x < settings.COLS and 0 <= new_y < settings.ROWS and ui.grid[new_y][new_x] is None:
            ui.grid[self.y][self.x] = None
            self.x = new_x
            self.y = new_y
            self.rect.topleft = (self.x * settings.CELL_SIZE, self.y * settings.CELL_SIZE)
            ui.grid[self.y][self.x] = self

if __name__ == "__main__":
    print("Testing Player class...")
    ui.initialize_ui()
    ui.flash_banner("Testing Player...", 1000)
    
    player = Player(5, 5)
    
    print(f"Player position: ({player.x}, {player.y})")
    print(f"Stats: {player.get_total_stats()}")