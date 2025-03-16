import json
import llm
import os
import pygame
import random
from player import Player
import settings
import ui

class NPC(Player):
    def __init__(self, x, y, speed, label = None, image = None, powers=[]):
        self.freeze = False
        self.speed = speed
        self.move_counter = 0
        self.label = label
        self.following = False
        self.meta_data = {} 
        
        super().__init__(x, y)

        self.configure_llm_prompts()
        if not image:
            self.configure_sprite()
        else:
            self.image = image
        
    def to_json(self):
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'speed': self.speed,
            'label': self.label,
            'meta_data': self.meta_data,
            'backstory': self.backstory,
            'description': self.description,
            'knowledge': self.knowledge
        })

    def from_json(json_str):
        data = json.loads(json_str)
        npc = NPC(data['x'], data['y'], data['speed'], data['label'])
        npc.meta_data = data['meta_data']
        npc.backstory = data['backstory']
        npc.description = data['description']
        npc.knowledge = data['knowledge']
        return npc

    def configure_sprite(self):
        available_sprites = os.listdir(settings.available_character_sprites_path)
        if available_sprites:
            selected_sprite = random.choice(available_sprites)
            source_path = os.path.join(settings.available_character_sprites_path, selected_sprite)
            destination_path = os.path.join(settings.character_sprites_path, self.label + ".png")
            os.makedirs(settings.character_sprites_path, exist_ok=True)
            os.rename(source_path, destination_path)
            self.image = pygame.image.load(destination_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (settings.CELL_SIZE, settings.CELL_SIZE))
        else:
            self.image = pygame.Surface((settings.CELL_SIZE, settings.CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), (settings.CELL_SIZE // 2, settings.CELL_SIZE // 2), settings.CELL_SIZE // 2)
            initials = ''.join([word[0] for word in self.label.split() if word[0].isalpha()]).upper()
            font = pygame.font.Font(None, 36)
            text_surface = font.render(initials, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(settings.CELL_SIZE // 2, settings.CELL_SIZE // 2))
            self.image.blit(text_surface, text_rect)
            pygame.image.save(self.image, os.path.join(settings.character_sprites_path, f"{self.label}.png"))
        
    def load_data(self, type):
        filename = f"data/characters/authored/{self.label}/{self.label}_character_{type}.txt"
        if (os.path.exists(filename)):
            with open(filename, "r") as file:
                return file.read()
        
        filename = f"data/characters/generated/{self.label}/{self.label}_character_{type}.txt"
        if (os.path.exists(filename)):
            with open(filename, "r") as file:
                return file.read()
            
        return None

    def save_data(self, type, data):
        filename = f"data/characters/authored/{self.label}/{self.label}_character_{type}.txt"
        if (os.path.exists(filename)):
            with open(filename, "w") as file:
                file.write(data)
                return
        
        filename = f"data/characters/generated/{self.label}/{self.label}_character_{type}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as file:
            file.write(data)

    def configure_llm_prompts(self):
        # Meta Data
        data = None
        if (self.label is not None):
            data = self.load_data("meta_data")
    
        if data is None or len(data) == 0:
            ui.flash_banner("Generating NPC Meta Data...", 0)
            messages = []
            messages.append(llm.get_system_message_from_file("data/system_prompts/generic_character_system_prompt.txt"))
            messages.append({
                "role": "user", 
                "content": "Generate a character. Be creative, avoiding too many generic details."
            })
            response = llm.send_message(messages, False)

            if isinstance(response, str):
                data = None
            else:
                data = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            data += chunk.choices[0].delta.content
        
        if data is not None:
            self.meta_data = json.loads(data)
            self.label = self.meta_data["name"]
            self.save_data("meta_data", json.dumps(self.meta_data))

        # Backstory
        self.backstory = self.load_data("backstory")
        if self.backstory is None:            
            ui.flash_banner(f"Generating Backstory for {self.label} the {self.meta_data['race']}, {self.meta_data['class']}...", 0)
            messages = []
            messages.append(llm.get_system_message_from_file("data/system_prompts/generic_character_designer_system_prompt.txt"))
            messages.append({
                "role": "user", 
                "content": f"Create a backstory for a character that describes the character expressed in this JSON formatted file {json.dumps(self.meta_data)}."
            })
            response = llm.send_message(messages, False)

            if isinstance(response, str):
                self.backstory = None
            else:
                self.backstory = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            self.backstory += chunk.choices[0].delta.content

            self.save_data("backstory", self.backstory)

        # description
        self.description = self.load_data("description")
        if self.description is None:
            ui.flash_banner(f"Generating NPC Description for {self.label} the {self.meta_data['race']}, {self.meta_data['class']}...", 0)
            messages = []
            messages.append(llm.get_system_message_from_file("data/system_prompts/generic_character_artist_system_prompt.txt"))
            messages.append({
                "role": "user", 
                "content": f"Create a description of the character whose JSON meta data and backstory is provided below.\n\n{json.dumps(self.meta_data)}\n\n{self.backstory}"
            })
            response = llm.send_message(messages, False)

            if isinstance(response, str):
                self.description = ""
            else:
                self.description = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            self.description += chunk.choices[0].delta.content
            self.save_data("description", self.description)

        # Knowledge
        self.knowledge = self.load_data("knowledge")
        if self.knowledge is None:
            ui.flash_banner(f"Generating NPC Knowledge for {self.label} the {self.meta_data['race']}, {self.meta_data['class']}...", 0)
            messages = []
            messages.append(llm.get_system_message_from_file("data/system_prompts/lore.txt"))
            messages.append({
                "role": "user", 
                "content": f"Create a knowledgebase for the character whose backstory is provided below.\n\n{self.backstory}"
            })
            response = llm.send_message(messages, False)
                
            if isinstance(response, str):
                self.knowledge = ""
            else:
                self.knowledge = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            self.knowledge += chunk.choices[0].delta.content
            
            self.save_data("knowledge", self.knowledge)

    def move_random(self):
        if not self.freeze and not self.following:
            self.move_counter += 1
            if self.move_counter >= self.speed:
                self.move_counter = 0
                dx, dy = random.choice(settings.DIRECTIONS)
                new_x = (self.x + dx)
                new_y = (self.y + dy)
                if 0 <= new_x < settings.COLS and 0 <= new_y < settings.ROWS and ui.grid[new_y][new_x] is None:
                    ui.grid[self.y][self.x] = None
                    self.x = new_x
                    self.y = new_y
                    self.rect.topleft = (self.x * settings.CELL_SIZE, self.y * settings.CELL_SIZE)
                    ui.grid[self.y][self.x] = self

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
            if 0 <= new_x < settings.COLS and 0 <= new_y < settings.ROWS and ui.grid[new_y][new_x] is None:
                ui.grid[self.y][self.x] = None
                self.x = new_x
                self.y = new_y
                self.rect.topleft = (self.x * settings.CELL_SIZE, self.y * settings.CELL_SIZE)
                ui.grid[self.y][self.x] = self

    def draw(self):
        self.screen.blit(self.image, self.rect.topleft)
        label_surface = ui.font.render(self.label, True, settings.RED)
        self.screen.blit(label_surface, (self.rect.x + 5, self.rect.y + 5))

if __name__ == "__main__":
    print("Testing NPC generation...")
    
    ui.initialize_ui()
    ui.flash_banner("Generating NPC...", 1000)

    npc = NPC(5, 5, 10, "Test NPC", None, ui.grid)
    ui.flash_banner("NPC generated, see console for details", 3000)

    print(npc.label)
    
    print("\n\nBackstory\n==========")
    print(npc.backstory)

    print("\n\nDesription\n==========")
    print(npc.description)

    print("\n\nKnowledge\n==========")
    print(npc.knowledge)

    print()
    