import pygame
import pygame_gui
from datetime import datetime
import os
import json
from openai import AzureOpenAI

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

def load_message_history(index):
    filename = f"data/conversations/character_{index}.json"
    
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    else:
        print(f"No conversation history found for index {index}. Loading the initial system prompt for that character.")
        filename = f"data/initial_system_prompts/character_{index}.json"
        if (os.path.exists(filename)):
            with open(filename, "r") as file:
                return json.load(file)
        else:
            filename = "data/initial_system_prompts/generic.json"
            with open(filename, "r") as file:
                return json.load(file)

def save_message_history(index, messages):
    directory = "data/conversations"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = f"{directory}/character_{index}.json"
    
    if os.path.exists(filename):
        timestamped = datetime.now().strftime("%y%m%d_%H%M")
        os.rename(filename, f"{directory}/{timestamped}_character_{index}.json")
    
    with open(filename, "w") as file:
        json.dump(messages, file)
        
def talk_to_character(index):
    manager, history_container, input_box, history_text, response_box = initialize_gui()
    
    messages = load_message_history(index)
    history_text.set_text(get_history_html(messages))
    user_input = ""
    input_box.focus()

    clock = pygame.time.Clock()

    return_pressed = False
    while True:
        time_delta = clock.tick(30) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_message_history(index, messages)
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not return_pressed:
                return_pressed = True
                user_input = input_box.get_text()
                if user_input.lower() == "bye":
                    save_message_history(index, messages)
                    return
                
                input_box.set_text("")

                messages.append({
                    "role": "user",
                    "content": user_input,
                })

                response = client.chat.completions.create(
                    stream=True,
                    messages=messages,
                    max_tokens=4096,
                    temperature=1.0,
                    top_p=1.0,
                    model=deployment,
                )

                assistant_message = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            assistant_message += chunk.choices[0].delta.content
                            response_box.set_text(assistant_message)
                        update_gui(manager, time_delta)

                messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                })

                history_text.set_text(get_history_html(messages))
                
                input_box.set_text("")
                input_box.focus()
            elif event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                return_pressed = False

            manager.process_events(event)

        update_gui(manager, time_delta)

def update_gui(manager, time_delta):
    manager.update(time_delta)
    screen.fill((255, 255, 255))
    manager.draw_ui(screen)
    pygame.display.flip()

def initialize_gui():
    manager = pygame_gui.UIManager(
        (800, 600)
    )
    
    history_container = pygame_gui.elements.ui_scrolling_container.UIScrollingContainer(
        relative_rect=pygame.Rect((20, 20), (760, 360)),
        manager=manager
    )
    
    history_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((0, 0), (740, 340)),
        manager=manager,
        container=history_container
    )
    
    response_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((20, 400), (760, 80)),
        manager=manager
    )
    
    response_box = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((10, 10), (740, 60)),
        manager=manager,
        container=response_panel
    )
    
    input_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((20, 500), (760, 80)),
        manager=manager
    )
    
    input_box = pygame_gui.elements.ui_text_entry_line.UITextEntryLine(
        relative_rect=pygame.Rect((10, 10), (740, 30)),
        manager=manager,
        container=input_panel
    )
    
    history_text = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((10, 10), (720, 320)),
        manager=manager,
        container=history_panel
    )
    history_container.set_scrollable_area_dimensions(history_text.rect.size)
    history_container.scrolling_bottom = True
    
    return manager, history_container, input_box, history_text, response_box

def get_history_html(messages):
    history_html = ""
    for message in messages:
        speaker = ""
        if (message["role"] == "system"):
            continue
        elif (message["role"] == "user"):
            speaker = "Player"
        elif (message["role"] == "assistant"):
            speaker = "Character"
        history_html += f"<b>{speaker}:</b> {message['content']}<br>"
    return history_html

def select_history_index_or_quit():
    user_input = ""
    while True:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.close()
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_input.isdigit() and 0 <= int(user_input) <= 9:
                        return int(user_input)
                    else:
                        user_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode

        # Render user input
        input_surface = font.render(f"Which character would you like to talk to (0-9): {user_input}", True, (0, 0, 0))
        screen.blit(input_surface, (20, 300))

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Chat with Character")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    history_index = None
    while True:
        history_index = select_history_index_or_quit()

        talk_to_character(history_index)
    