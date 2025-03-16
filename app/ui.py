
import pygame
import pygame_gui
import settings
import ui

screen = None
font = None
grid = None

def initialize_ui():
    global screen, font, grid
    
    grid = [[None for _ in range(settings.COLS)] for _ in range(settings.ROWS)]

    screen = pygame.display.set_mode((settings.WIDTH + settings.SIDE_WIDTH, settings.HEIGHT))
    pygame.display.set_caption("Unity in the Mountains")

    pygame.font.init()
    font = pygame.font.SysFont(None, 24)

def flash_banner(message, wait_time=3000):
    width, height = ui.screen.get_size()
    font = pygame.font.Font(None, 36)
    celebration_surface = pygame.Surface((width, height // 2))
    celebration_surface.fill(settings.WHITE)
    text_surface = font.render(message, True, settings.BLACK)
    celebration_surface.blit(text_surface, (celebration_surface.get_width() // 2 - text_surface.get_width() // 2, celebration_surface.get_height() // 2 - text_surface.get_height() // 2))
    ui.screen.blit(celebration_surface, (0, 0))
    pygame.display.flip()
    pygame.time.wait(wait_time)

def update_gui(manager = None, time_delta = 0):
    screen.fill((255, 255, 255))

    if manager is not None:
        manager.update(time_delta)
        manager.draw_ui(screen)
    pygame.display.flip()

def draw_side_window(player, obstacles, npcs):
    side_window = pygame.Surface((settings.SIDE_WIDTH, settings.HEIGHT))
    side_window.fill(settings.WHITE)

    # Display total stats of the party
    y_offset = 10
    side_window.blit(ui.font.render("Party Statistics:", True, settings.BLACK), (10, y_offset))
    y_offset += 40
    total_stats = player.get_total_stats()
    for stat, value in total_stats.items():
        side_window.blit(ui.font.render(f"{stat}: {value}", True, settings.BLACK), (10, y_offset))
        y_offset += 30

    # Display stats of nearby NPCs that are not following the player
    y_offset += 20
    side_window.blit(ui.font.render("Nearby NPCs:", True, settings.BLACK), (10, y_offset))
    y_offset += 40
    for npc in npcs:
        if player.is_next_to(npc) and not npc.following:
            side_window.blit(ui.font.render(f"NPC {npc.label}:", True, settings.BLACK), (10, y_offset))
            y_offset += 30
            for stat in npc.meta_data["statistics"]:
                value = npc.meta_data["statistics"][stat]
                color = (0, 255, 0) if total_stats.get(stat, 0)/len(npcs) <= value else (255, 0, 0)
                side_window.blit(ui.font.render(f"{stat}: {value}", True, color), (10, y_offset))
                y_offset += 30

    # Display stats of nearby obstacles
    y_offset += 20
    side_window.blit(ui.font.render("Nearby Obstacles:", True, settings.BLACK), (10, y_offset))
    y_offset += 40
    for obstacle in obstacles:
        if player.is_next_to(obstacle):
            side_window.blit(ui.font.render(f"Obstacle at ({obstacle.x}, {obstacle.y}):", True, settings.BLACK), (10, y_offset))
            y_offset += 30
            for stat in obstacle.powers:
                color = (0, 255, 0) if total_stats.get(stat.name, 0) >= stat.amount else (255, 0, 0)
                side_window.blit(ui.font.render(f"{stat.name}: {stat.amount}", True, color), (10, y_offset))
                y_offset += 30
            y_offset += 20

    ui.screen.blit(side_window, (settings.WIDTH, 0))

def initialize_conversation_gui(screen):
    screen_width, screen_height = screen.get_size()
    margin = 5
    number_of_followup_buttons = 4
    history_box_height = screen_height * 0.74
    user_input_height = screen_height * 0.08
    suggested_followup_button_height = (screen_height - (history_box_height + user_input_height)) / number_of_followup_buttons
    
    manager = pygame_gui.UIManager(
        (screen_width, screen_height)
    )
    
    history_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 2, history_box_height)),
        manager=manager
    )
    history_box = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 4, history_box_height - margin * 2)),
        manager=manager,
        container=history_panel
    )

    input_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((0, screen_height - user_input_height), (screen_width - margin * 2, user_input_height)),
        manager=manager
    )
    input_box = pygame_gui.elements.ui_text_entry_line.UITextEntryLine(
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 4, user_input_height - margin * 2)),
        manager=manager,
        container=input_panel
    )

    followup_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((margin, screen_height - user_input_height - suggested_followup_button_height * number_of_followup_buttons), (screen_width - margin * 2, suggested_followup_button_height * number_of_followup_buttons)),
        manager=manager
    )
    followup_buttons = []
    for i in range(number_of_followup_buttons):
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((margin, (margin / 2) + (i * suggested_followup_button_height)), (screen_width - margin * 4, suggested_followup_button_height - (margin / 2))),
            text=f"Followup {i + 1}",
            manager=manager,
            container=followup_panel
        )
        button.hide()
        followup_buttons.append(button)
    
    return manager, input_box, history_box, followup_buttons
