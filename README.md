# Coderbot

A chatbot that conducts coding interviews.

Used for learning, demo and entertainment purposes. This is a quick exercise for building a chatbot you can talk with, may use macos specific tools.

## Install requirements

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you want to record yourself instead of typing, you also need to install PortAudio (`brew install portaudio`) and allow Terminal to use the microphone (System Settings > Privacy & Security > Microphone).

Deepgram is used for transcription and OpenAI for text completion and text-to-speech. You need register to both and get API keys (and possible pay something to use them). The clients get the API keys when defined like

```bash
export OPENAI_API_KEY=x
export DEEPGRAM_API_KEY=x
```

## Running

```bash
python coderbot.py # records you (press enter to start and stop), the bot speaks
python coderbot.py --keyboard # you're typing
python coderbot.py --silent # all text
```

Recordings and transcriptions are saved under `data/` for later analysis.
