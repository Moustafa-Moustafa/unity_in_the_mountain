import pygame
import pygame_gui
from datetime import datetime
import os
import json
from openai import AzureOpenAI


screen = None
font = None
acceptance_prompt = None
in_conversation = False

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
            acceptance_prompt = get_system_message(filename)
        else:
            acceptance_prompt = get_system_message("data/system_prompts/generic_quest_acceptance.txt")

        return history
    else:
        flash_banner("Generating NPC Backstory...", 0)
        prompts = []
        
        filename = f"data/system_prompts/character_{npc_index}.txt"
        if (os.path.exists(filename)):
            prompts.append(get_system_message(filename))
        else:            
            messages = []
            messages.append(get_system_message("data/system_prompts/generic_character_designer_system_prompt.txt"))
            messages.append({
                "role": "user", 
                "content": "Create a backstory for a character. Include their name, appearance, race and personality."
            })
            response = send_message(messages, False)
            backstory = ""
            for chunk in response:
                if chunk.choices:
                    if chunk.choices[0].delta.content:
                        backstory += chunk.choices[0].delta.content
            prompts.append({
                "role": "system", 
                "content": backstory
            })
        
        filename = f"data/system_prompts/character_description_{npc_index}.txt"
        if (os.path.exists(filename)):
            prompts.append(get_system_message(filename))
        else:
            flash_banner("Generating NPC Description...", 0)
            messages = []
            messages.append({
                "role": "system", 
                "content": "You are a character designer for a fantasy RPG."
            })
            messages.append({
                "role": "user", 
                "content": f"Create a description of the character whose backstory is below. Include their name, appearance, race and personality.\n\n{backstory}"
            })
            response = send_message(messages, False)
            description = ""
            for chunk in response:
                if chunk.choices:
                    if chunk.choices[0].delta.content:
                        description += chunk.choices[0].delta.content
            prompts.append({
                "role": "system", 
                "content": description
            })

        filename = f"data/system_prompts/character_quest_knowledge_{npc_index}.txt"
        if (os.path.exists(filename)):
            prompts.append(get_system_message(filename))
        else:
            prompts.append(get_system_message("data/system_prompts/generic_quest_knowledge.txt"))

        filename = f"data/system_prompts/character_quest_acceptance_{npc_index}.txt"
        if (os.path.exists(filename)):
            acceptance_prompt = get_system_message(filename)
            prompts.append(acceptance_prompt)
        else:
            acceptance_prompt = get_system_message("data/system_prompts/generic_quest_acceptance.txt")
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
    global in_conversation
    
    manager, input_box, history_text, response_box, followup_buttons = initialize_gui(screen)
    
    system_status = [get_system_message("data/system_prompts/main_system_prompt.txt")]

    current_messages = load_message_history(npc_index)
    set_suggested_followups(current_messages, followup_buttons)
    history_text.set_text(get_history_html(current_messages))

    user_input = ""
    input_box.focus()

    clock = pygame.time.Clock()

    return_pressed = False
    in_conversation = True
    send_followup = False
    while in_conversation:
        time_delta = clock.tick(30) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_message_history(npc_index, current_messages)
                pygame.quit()
                exit()
                return
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == followup_buttons[0]:
                        input_box.set_text(followup_buttons[0].text)
                        send_followup = True
                    if event.ui_element == followup_buttons[1]:
                        input_box.set_text(followup_buttons[1].text)
                        send_followup = True
                    if event.ui_element == followup_buttons[2]:
                        input_box.set_text(followup_buttons[2].text)
                        send_followup = True
            elif send_followup or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not return_pressed):
                send_followup = False
                user_input = input_box.get_text()
                if (user_input == ""):
                    continue
                
                return_pressed = True
                if user_input.lower() == "bye":
                    in_conversation = False
                
                input_box.set_text(input_box.get_text() + " (said, awaiting response...)")
                update_gui(manager, time_delta)

                current_messages.append({
                                "role": "user",
                                "content": user_input,
                            })
                messages = system_status + current_messages
                response = send_message(messages)

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

                process_response(player, npc, assistant_response)
                set_suggested_followups(current_messages, followup_buttons)

                history_text.set_text(get_history_html(current_messages))
                
                input_box.set_text("")
                input_box.focus()
            elif event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                return_pressed = False

            manager.process_events(event)

        update_gui(manager, time_delta)

    save_message_history(npc_index, current_messages)
    return

def set_suggested_followups(messages, followup_buttons):
    messages.append({
                    "role": "user",
                    "content": "Provide 3 followup messages the player may say next. At least two of the follow ups must be natural follow ons from the previous messages, the third will be related to the players desire to create a party. The suggestions must only use information that has been provided to the player by the assistant in responses. List them one per line with no bullets or numberuing.",
                })
    response = send_message(messages, False)
    followup_questions = ""
    for chunk in response:
        if chunk.choices:
            if chunk.choices[0].delta.content:
                followup_questions += chunk.choices[0].delta.content

    messages.pop()  # Remove the followup question prompt, response was never added to the history
    followup_questions = followup_questions.splitlines()
    for i in range(len(followup_buttons)):
        if i < len(followup_questions):
            followup_buttons[i].show()
            followup_buttons[i].set_text(followup_questions[i])
        else:
            followup_buttons[i].hide()
            followup_buttons[i].set_text("")
    
def send_message(messages, is_streaming=True):
    response = client.chat.completions.create(
                    stream=True,
                    messages=messages,
                    max_tokens=4096,
                    temperature=1.0,
                    top_p=1.0,
                    model=deployment,
                )
    
    return response

def process_response(player, npc, response):
    # Process the response from the assistant
    # This function can be customized to handle different types of responses
    # For example, you could parse the response for specific commands or actions
    # and execute
    # them in the game world.
    global acceptance_prompt, in_conversation

    for line in acceptance_prompt["content"].splitlines():
        if line != "" and line in response:
            print(f"Found acceptance line in response: {line}")
            if player is not None and npc is not None:
                player.gain_party_member(npc)
                flash_banner(f"{npc.label} has joined your party!")
            else:
                flash_banner("An npc has joined your party!")

            in_conversation = False
            break

def flash_banner(message, wait_time=3000):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    width, height = screen.get_size()
    font = pygame.font.Font(None, 36)
    celebration_surface = pygame.Surface((width, height // 2))
    celebration_surface.fill(WHITE)
    text_surface = font.render(message, True, BLACK)
    celebration_surface.blit(text_surface, (celebration_surface.get_width() // 2 - text_surface.get_width() // 2, celebration_surface.get_height() // 2 - text_surface.get_height() // 2))
    screen.blit(celebration_surface, (0, 0))
    pygame.display.flip()
    pygame.time.wait(wait_time)

def get_system_message(filename):
    system_prompt = ""
    with open(filename, "r") as file:
        system_prompt = file.read()

    system_status = None
    system_status = {
            "role": "system", 
            "content": system_prompt
        }
    
    return system_status

def update_gui(manager, time_delta):
    manager.update(time_delta)
    screen.fill((255, 255, 255))
    manager.draw_ui(screen)
    pygame.display.flip()

def initialize_gui(gui_screen):
    global screen
    font = pygame.font.Font(None, 36)
    screen = gui_screen
    screen_width, screen_height = screen.get_size()
    margin = 5
    history_box_height = screen_height * 0.5
    response_box_height = screen_height * 0.25
    user_input_height = screen_height * 0.10
    suggested_followup_height = screen_height * 0.05
    
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
    
    response_panel = pygame_gui.elements.ui_panel.UIPanel(
        relative_rect=pygame.Rect((margin, history_box_height), (screen_width - margin * 2, response_box_height)),
        manager=manager
    )
    response_box = pygame_gui.elements.ui_text_box.UITextBox(
        html_text="",
        relative_rect=pygame.Rect((margin, margin), (screen_width - margin * 4, response_box_height - margin * 2)),
        manager=manager,
        container=response_panel
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
        relative_rect=pygame.Rect((margin, screen_height - user_input_height - suggested_followup_height * 3), (screen_width - margin * 2, suggested_followup_height * 3)),
        manager=manager
    )
    followup_buttons = []
    for i in range(3):
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((margin, margin + i * (suggested_followup_height)), (screen_width - margin * 4, suggested_followup_height - margin * 2)),
            text=f"Followup {i + 1}",
            manager=manager,
            container=followup_panel
        )
        button.hide()
        followup_buttons.append(button)
    
    return manager, input_box, history_box, response_box, followup_buttons

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
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    history_index = None
    while True:
        history_index = select_history_index_or_quit()

        # REFACTOR: we should be passing in a player and npc object here
        talk_to_character(None, None, history_index, screen)
    