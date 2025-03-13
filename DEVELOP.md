# Setup

Ensure dependencies are installed:

```bash
pip install --upgrade pip setuptools
pip install .
```

Setup your environment, it's easiest to add this to a `.env` file in your workspace route.

```bash
export AZURE_OPENAI_API_KEY="<your key>"
export AZURE_OPENAI_ENDPOINT="https://unityinthemountains.openai.azure.com/"
export AZURE_OPENAI_MODEL_NAME="gpt-4o-mini"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
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

Note that conversations are saved and loaded each time you talk with a character. This includes between separate runs. You can delete the history of a conversation, in order to start fresh, by removing the files in `/home/rogardle/projects/unity_in_the_mountain/data/conversations`

## Game Feel

### Confetti Explosion

```bash
python app/confetti_explosion.py
```

Click the mouse button to deliver an explosion of particles

