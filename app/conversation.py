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
    filename = f"message_history_{index}.json"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return []

def save_message_history(index, messages):
    filename = f"message_history_{index}.json"
    if os.path.exists(filename):
        os.rename(filename, f"{filename}.backup")
    with open(filename, "w") as file:
        json.dump(messages, file)

while True:
    system_prompt = input("Enter system prompt (or type 'exit' to quit): ")
    if system_prompt.lower() == "exit":
        break

    # Select a message history to load
    history_index = int(input("Enter history index (0-4): "))
    messages = load_message_history(history_index)

    # Initialize message history with the system prompt
    messages.append({
        "role": "system",
        "content": system_prompt,
    })

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

        for update in response:
            if update.choices:
                assistant_message = update.choices[0].delta.content or ""
                print(assistant_message, end="")
                # Append assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                })

    # Save the message history
    save_message_history(history_index, messages)
    print("Conversation ended. Starting a new one...")

print("Goodbye!")

client.close()