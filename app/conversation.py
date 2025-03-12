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
        print(f"No message history found for index {index}. Loading the initial system prompt for that character.")
        filename = f"data/initial_system_prompts/character_{index}.json"
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

    while True:
        print()
        user_input = input("You: ")
        print()
        
        if user_input.lower() == "bye":
            break

        # Append user message to history
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
        for update in response:
            if update.choices:
                assistant_message += update.choices[0].delta.content or ""
                print(update.choices[0].delta.content or "", end="")
        
        # Append assistant message to history
        messages.append({
            "role": "assistant",
            "content": assistant_message,
        })

    # Save the message history
    save_message_history(index, messages)

while True:
    # Select a message history to load
    history_index = input("Enter history index (0-4): ").lower()

    if (history_index == "exit"):
        break
    
    try:
        history_index = int(history_index)
    except ValueError:
        print("Invalid input. Please enter a number between 0 and 4.")
        continue
    
    if (history_index < 0 or history_index > 4):
        print("Invalid index. Please enter a number between 0 and 4.")
        continue

    print()
    talk_to_character(history_index)

client.close()