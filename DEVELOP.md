# Setup

Ensure dependencies are installed:

```bash
pip install --upgrade pip setuptools
pip install .
```

Setup your environment:

```bash
export AZURE_OPENAI_API_KEY="<your key>"
export AZURE_OPENAI_ENDPOINT="https://ada-naman.openai.azure.com/"
export AZURE_OPENAI_MODEL_NAME="gpt-4o"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
```

# Running the Main Game

```bash
python app/main.py
```

Use the `WASD` keys to move. When next to an NPC hit `SPACE` to start a conversation.

## Testing Conversations in Isolation

It can be useful to jump straight in to talking to a character. To do this:

```bash
python app/conversation.py
```


