
import os
from typing import IO
from io import BytesIO
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
elevenlabs = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)


def text_to_speech_stream(text: str) -> IO[bytes]:
    # Use convert instead of stream for more reliable audio
    # Request 44.1kHz to match standard system rate (avoids CoreAudio switching glitches)
    response = elevenlabs.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )

    # Create a BytesIO object to hold the audio data in memory
    audio_stream = BytesIO()

    # Write each chunk of audio data to the stream
    chunk_count = 0
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)
            chunk_count += 1

    # Get total size
    total_size = audio_stream.tell()
    print(f"   📊 Audio: {chunk_count} chunks, {total_size} bytes")
    
    if total_size < 100:
        print(f"   ⚠️  WARNING: Audio file very small ({total_size} bytes)!")
    
    # Reset stream position to the beginning
    audio_stream.seek(0)

    # Return the stream for further use
    return audio_stream