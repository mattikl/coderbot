import openai
import click
import pyaudio
import wave
import os
import sys
import logging
from select import select
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    PrerecordedOptions,
    FileSource,
)
from datetime import datetime, timedelta

data_dir = "data"

if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def get_filename(item, ext):
    return os.path.join(data_dir, f"{item}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.{ext}")

config = DeepgramClientOptions(
    verbose=logging.SPAM,
)
deepgram = DeepgramClient("", config)

# Parameters for recording
FORMAT = pyaudio.paInt16  # Audio format
CHANNELS = 1  # Number of audio channels
RATE = 44100  # Bit rate
CHUNK = 1024  # Number of audio samples per frame

def start_recording(filename):
    audio = pyaudio.PyAudio()
    print("Recording Started. Press Enter to stop.")
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    def user_pressed_enter():
        if sys.stdin in select([sys.stdin], [], [], 0)[0]:
            line = input()
            return True
        return False

    # Record until Enter is pressed
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if user_pressed_enter():
            break

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    print("Recording Stopped. Audio saved to " + filename)

def record_audio():
    print("Press Enter to start recording")
    input()
    filename = get_filename("recording", "wav")
    start_recording(filename)
    return filename

client = openai.OpenAI()

def ask_openai(question, chat_log=None):
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=generate_prompt(question, chat_log),
        temperature=0.7,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=["\n"]
    )
    return response.choices[0].text.strip()

def generate_prompt(question, chat_log=None):
    if chat_log == "":
        return f"The following is a conversation with a coder chatbot who interviews the candidate about coding:\n\nCandidate: {question}\nChatbot:"
    return f"{chat_log}\nYou: {question}\nChatbot:"

def play_audio(message):
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=message
    )

    # Ideally you would stream the response into pyaudio, but saving and
    # playing with afplay (preinstalled on macs) is easier for this example
    response.stream_to_file("speech.mp3")
    os.system(f'afplay speech.mp3')

def transcribe(filename):
    try:
        with open(filename, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-2-conversationalai",
            smart_format=True,
            utterances=True,
            punctuate=True,
            language="en-US",
        )

        before = datetime.now()
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        after = datetime.now()

        with open(get_filename("transcription", "log"), "a") as file:
            file.write(response.to_json(indent=4) + "\n")

        result = response['results'].channels[0].alternatives[0]

        difference = after - before
        print(f"Transcription: '{result.transcript}' in {difference.seconds}s")
        return result.transcript

    except Exception as e:
        print(f"Exception: {e}")

@click.command()
@click.option('--keyboard', is_flag=True)
@click.option('--silent', is_flag=True)
def main(keyboard, silent):
    chat_log = ""
    opening_message = "Hi! I'm a coder bot and I'll ask you questions about coding. What languages have you used lately?"
    play_audio(opening_message)
    print("Chatbot: {opening_message}")
    while True:
        if keyboard or silent:
            user_input = input("Candidate: ")
        else:
            filename = record_audio()
            user_input = transcribe(filename)
        bot_response = ask_openai(user_input, chat_log)
        chat_log += f"\nCandidate: {user_input}\nChatbot: {bot_response}"
        if not silent:
            play_audio(bot_response)
        print(chat_log)

if __name__ == "__main__":
    main()
