import pygame
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
    messages = load_message_history(index)
    user_input = ""

    while True:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_input.lower() == "bye":
                        save_message_history(index, messages)
                        return
                    # Append user message to history
                    messages.append({
                        "role": "Player",
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
                    for update in response:
                        if update.choices:
                            assistant_message += update.choices[0].delta.content or ""
                            user_input = ""
                    
                    # Append assistant message to history
                    messages.append({
                        "role": "NPC",
                        "content": assistant_message,
                    })
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode

        # Render user input
        input_surface = font.render(f"You: {user_input}", True, (0, 0, 0))
        screen.blit(input_surface, (20, 550))

        # Render conversation history
        y_offset = 20
        for message in messages:
            message_surface = font.render(f"{message['role']}: {message['content']}", True, (0, 0, 0))
            screen.blit(message_surface, (20, y_offset))
            y_offset += 40

        pygame.display.flip()
        clock.tick(30)

    # Save the message history
    save_message_history(index, messages)

def select_history_index():
    user_input = ""
    while True:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
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

    while True:
        history_index = select_history_index()
        if history_index is None:
            break
        talk_to_character(history_index)

    client.close()