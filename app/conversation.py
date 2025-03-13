import pygame
import pygame_gui
from datetime import datetime
import os
import json
from openai import AzureOpenAI


screen = None
font = None
acceptance_prompt = None

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

def load_message_history(npc_index):
    global acceptance_prompt

    filename = f"data/conversations/character_{npc_index}.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            history = json.load(file)
        print(f"Loaded conversation history for index {npc_index}.")
        
        filename = f"data/system_prompts/character_quest_acceptance_{npc_index}.txt"
        if (os.path.exists(filename)):
            acceptance_prompt = get_prompt(filename)
        else:
            acceptance_prompt = get_prompt("data/system_prompts/generic_quest_acceptance.txt")

        return history
    else:
        print(f"No conversation history found for index {npc_index}. Loading the initial system prompts for that character.")
        prompts = []
        
        filename = f"data/system_prompts/character_{npc_index}.txt"
        if (os.path.exists(filename)):
            prompts.append(get_prompt(filename))
        else:
            prompts.append(get_prompt("data/system_prompts/generic_character.txt"))
        
        filename = f"data/system_prompts/character_quest_knowledge_{npc_index}.txt"
        if (os.path.exists(filename)):
            prompts.append(get_prompt(filename))
        else:
            prompts.append(get_prompt("data/system_prompts/generic_character_quest_knowledge.txt"))

        filename = f"data/system_prompts/character_quest_acceptance_{npc_index}.txt"
        if (os.path.exists(filename)):
            acceptance_prompt = get_prompt(filename)
            prompts.append(acceptance_prompt)
        else:
            acceptance_prompt = get_prompt("data/system_prompts/generic_quest_acceptance.txt")
            prompts.append(acceptance_prompt)

        return prompts
        
def save_message_history(npc_index, messages):
    directory = "data/conversations"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = f"{directory}/character_{npc_index}.json"
    
    if os.path.exists(filename):
        timestamped = datetime.now().strftime("%y%m%d_%H%M")
        os.rename(filename, f"{directory}/{timestamped}_character_{npc_index}.json")
    
    with open(filename, "w") as file:
        json.dump(messages, file)

#REFACTOR: npc and npc_index are duplication. We should only be passing in one of them and looking the other up        
def talk_to_character(player, npc, npc_index, screen):
    manager, input_box, history_text, response_box = initialize_gui(screen)
    
    system_status = [get_prompt("data/system_prompts/main_system_prompt.txt")]

    current_messages = load_message_history(npc_index)
    history_text.set_text(get_history_html(current_messages))

    user_input = ""
    input_box.focus()

    clock = pygame.time.Clock()

    return_pressed = False
    while True:
        time_delta = clock.tick(30) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_message_history(npc_index, current_messages)
                pygame.quit()
                exit()
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not return_pressed:
                user_input = input_box.get_text()
                if (user_input == ""):
                    continue
                
                return_pressed = True
                if user_input.lower() == "bye":
                    save_message_history(npc_index, current_messages)
                    return
                
                input_box.set_text("")

                current_messages.append({
                    "role": "user",
                    "content": user_input,
                })

                messages = system_status + current_messages
                
                response = client.chat.completions.create(
                    stream=True,
                    messages=system_status + current_messages,
                    max_tokens=4096,
                    temperature=1.0,
                    top_p=1.0,
                    model=deployment,
                )

                assistant_response = ""
                for chunk in response:
                    if chunk.choices:
                        if chunk.choices[0].delta.content:
                            assistant_response += chunk.choices[0].delta.content
                            response_box.set_text(assistant_response)
                        update_gui(manager, time_delta)

                current_messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                })

                process_response(npc, assistant_response)

                history_text.set_text(get_history_html(current_messages))
                
                input_box.set_text("")
                input_box.focus()
            elif event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                return_pressed = False

            manager.process_events(event)

        update_gui(manager, time_delta)

def process_response(npc, response):
    # Process the response from the assistant
    # This function can be customized to handle different types of responses
    # For example, you could parse the response for specific commands or actions
    # and execute
    # them in the game world.
    global acceptance_prompt

    for line in acceptance_prompt["content"].splitlines():
        if line != "" and line in response:
            print(f"Found acceptance line in response: {line}")
            npc.following = True
            break

def get_prompt(filename):
    system_prompt = ""
    with open(filename, "r") as file:
        system_prompt = file.read()

    system_status = None
    system_status = {
            "role": "system", 
            "content": system_prompt
        }
    0
    return system_status

def update_gui(manager, time_delta):
    manager.update(time_delta)
    screen.fill((255, 255, 255))
    manager.draw_ui(screen)
    pygame.display.flip()

def initialize_gui(gui_screen):
    global screen
    screen = gui_screen
    screen_width, screen_height = screen.get_size()
    margin = 5
    user_input_height = 50
    response_box_height = (screen_height - user_input_height - (margin * 3)) // 2
    
    manager = pygame_gui.UIManager(
        (screen_width, screen_height)
    )
    
    input_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((0, screen_height - user_input_height), (screen_width, user_input_height)),
        manager=manager
    )
    input_box = pygame_gui.elements.ui_text_entry_line.UITextEntryLine(
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 2, user_input_height - margin * 2)),
        manager=manager,
        container=input_panel
    )
    
    history_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 2, response_box_height)),
        manager=manager
    )
    history_box = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 4, response_box_height - margin * 2)),
        manager=manager,
        container=history_panel
    )
    
    response_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((margin, response_box_height + margin * 2), (screen_width - margin * 2, response_box_height)),
        manager=manager
    )
    response_box = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 4, response_box_height - margin * 2)),
        manager=manager,
        container=response_panel
    )
    
    return manager, input_box, history_box, response_box

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
        history_html += f"<p><b>{speaker}:</b> {message['content']}</p>"
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
    pygame.init()
    pygame.display.set_caption("Chat with Character")
    screen = pygame.display.set_mode((800, 600))
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    history_index = None
    while True:
        history_index = select_history_index_or_quit()

        # REFACTOR: we should be passing in a player and npc object here
        talk_to_character(None, None, history_index, screen)
    