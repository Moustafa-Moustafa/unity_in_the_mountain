import random
import re
import pygame
import pygame_gui
from datetime import datetime
import llm
import os
import json
import settings
import ui

from npc import NPC

acceptance_prompt = None
in_conversation = False

def load_message_history(npc):
    global acceptance_prompt

    filename = f"data/conversations/{npc.label}.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            history = json.load(file)
            print(f"Loaded conversation history for index {npc.label}.")
        
        return history
    else:
        prompts = []
        
        prompts.append(llm.get_system_message_from_string(npc.backstory))
        prompts.append(llm.get_system_message_from_string(npc.description))
        prompts.append(llm.get_system_message_from_string(npc.knowledge))

        acceptance_prompt = llm.get_system_message_from_file("data/system_prompts/generic_quest_acceptance.txt")
        prompts.append(acceptance_prompt)

        return prompts
        
def save_message_history(npc, messages):
    directory = "data/conversations"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the current conversation history
    filename = f"{directory}/character_{npc.label}.json"
    if os.path.exists(filename):
        timestamped = datetime.now().strftime("%y%m%d_%H%M")
        os.rename(filename, f"{directory}/{timestamped}_character_{npc.label}.json")
    
    with open(filename, "w") as file:
        json.dump(messages, file)

    # Save the entire story
    story_filename = f"data/conversations/story.json"
    if os.path.exists(story_filename):
        with open(story_filename, "r") as file:
            story = json.load(file)
    else:
        story = {}

    scene = {
        "participants": ["player", npc.label],
        "content": []
    }
    if "scenes" not in story:
        story["scenes"] = []
    
    for message in messages:
        if message["role"] != "system":
            entry = {}
            if message["role"] == "user":
                entry["participant"] = "Player"
            else:
                entry["participant"] = npc.label
            entry["dialogue"] = message["content"]
            scene["content"].append(entry)
    
    story["scenes"].append(scene)
    
    with open(story_filename, "w") as file:
        json.dump(story, file)

def talk_to_character(player, npc):
    global in_conversation, history_text
    
    print(f"Starting conversation with {npc.label} the {npc.meta_data['race']} {npc.meta_data['class']}.")

    manager, input_box, history_text, followup_buttons = ui.initialize_conversation_gui(ui.screen)
    
    system_status = [llm.get_system_message_from_file("data/system_prompts/main_system_prompt.txt")]

    current_messages = load_message_history(npc)
    set_suggested_followups(current_messages, followup_buttons)
    update_history_text(current_messages, npc)
    
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
                save_message_history(npc, current_messages)
                pygame.quit()
                exit()
                return
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    for button in followup_buttons:
                        if event.ui_element == button:
                            input_box.set_text(button.text)
                            send_followup = True
            elif send_followup or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not return_pressed):
                send_followup = False
                user_input = input_box.get_text()
                if (user_input == ""):
                    continue
                
                return_pressed = True
                if re.search(r"\bbye\b|\bgoodbye\b|\bbye!$", user_input.lower()):
                    in_conversation = False
                
                input_box.set_text(input_box.get_text() + " (said, awaiting response...)")
                ui.update_gui(manager, time_delta)

                current_messages.append({
                                "role": "user",
                                "content": user_input,
                            })
                messages = system_status + current_messages
                response = llm.send_message(messages)

                if isinstance(response, str):
                    assistant_response = response
                else:
                    assistant_response = ""
                    for chunk in response:
                        if chunk.choices:
                            if chunk.choices[0].delta.content:
                                assistant_response += chunk.choices[0].delta.content
                            ui.update_gui(manager, time_delta)

                current_messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                })

                process_response(player, npc, assistant_response)
                set_suggested_followups(current_messages, followup_buttons)

                update_history_text(current_messages, npc)
                
                input_box.set_text("")
                input_box.focus()
            elif event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
                return_pressed = False

            manager.process_events(event)

        ui.update_gui(manager, time_delta)

    save_message_history(npc, current_messages)
    return

def update_history_text(messages, character):
    global history_text
    
    history_html = ""
    for message in messages:
        if (message["role"] == "system"):
            continue
        elif (message["role"] == "user"):
            history_html += "<p/><p>--------------------------------------------------------------------</p><p/>"
            history_html += f"<p><b>You:</b> {message['content']}</p>"
        elif (message["role"] == "assistant"):
            history_html += f"<p><b>{character.label}:</b> {message['content']}</p>"

    history_text.set_text(history_html)
    if history_text.scroll_bar is not None:
        history_text.scroll_bar.set_scroll_from_start_percentage(1.0)

def defaultQuestions():
    return [
        "Are you aware of any adventure opportunities around here?",
        "Hi there, you look like you might be interested in adventure?",
        "Hi there, who are you?"
    ]

def set_suggested_followups(messages, followup_buttons):
    if not any(message["role"] == "user" for message in messages):
        followup_questions = defaultQuestions()
    else:
        messages.append({
                        "role": "user",
                        "content": "Provide 3 followup messages the player may say next. At least two of the follow ups must be natural follow ons from the previous messages, the third will be related to the players desire to create a party. The suggestions must only use information that has been provided to the player by the assistant in responses. List them one per line with no bullets or numberuing.",
                    })
        response = llm.send_message(messages, False)
        
        if isinstance(response, str):
            followup_questions = defaultQuestions()
        else:
            followup_questions = ""
            for chunk in response:
                if chunk.choices:
                    if chunk.choices[0].delta.content:
                        followup_questions += chunk.choices[0].delta.content
            followup_questions = followup_questions.splitlines()

        messages.pop()  # Remove the followup question prompt, response was never added to the history

    for i in range(len(followup_buttons)):
        if i < len(followup_questions):
            followup_buttons[i].show()
            followup_buttons[i].set_text(followup_questions[i])
        else:
            followup_buttons[i].show()
            followup_buttons[i].set_text("Good Bye.")

def process_response(player, npc, response):
    # Process the response from the assistant
    # This function can be customized to handle different types of responses
    # For example, you could parse the response for specific commands or actions
    # and execute
    # them in the game world.
    global acceptance_prompt, in_conversation

    # Check if the response has an acceptance of the party invitation 
    for line in acceptance_prompt["content"].splitlines():
        if line != "" and line in response:
            print(f"Found acceptance line in response: {line}")
            if player is not None and npc is not None:
                player.gain_party_member(npc)
                ui.flash_banner(f"{npc.label} has joined your party!")
            else:
                ui.flash_banner("An npc has joined your party!")

            in_conversation = False
            break

    # extract meta data
    pattern = r"-+ Meta Data -+\n\n((?:.*?: .*?$)+)"
    match = re.search(pattern, response, re.DOTALL)
    meta_data = {}
    if match:
        meta_data_text = match.group(1)
        key_value_pattern = r"(.*?): (.*?)$"
        key_value_matches = re.finditer(key_value_pattern, meta_data_text, re.MULTILINE)
        for kv_match in key_value_matches:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()
            meta_data[key] = value
        if hasattr(npc, key):
                setattr(npc, key, value)
        if npc is not None:
            npc.meta_data = meta_data

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()
    ui.initialize_ui()

    history_index = None
    while True:
        grid = [[None for _ in range(10)] for _ in range(10)]
        generated_npcs = os.listdir(settings.generated_npcs_path)
        if len(generated_npcs) > 0:
            character_name = random.choice(generated_npcs)
            npc = NPC(5, 5, 3, character_name)
            generated_npcs.remove(character_name)
        else:
            npc = NPC(5, 5, 3)

        # REFACTOR: we should be passing in a player and npc object here
        talk_to_character(None, npc)
    