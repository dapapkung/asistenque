# 🤖 AsistenQue - Voice Assistant

AsistenQue is a Python-based voice assistant that runs locally on macOS. It leverages the power of:
- **Whisper** (OpenAI) for Speech-to-Text (STT)
- **Ollama** for Local Large Language Model (LLM) intelligence
- **ElevenLabs** for high-quality Text-to-Speech (TTS)
- **afplay** (macOS native) for stable audio playback

## 🌟 Features

- **Push-to-Talk**: Press `SPACE` to talk, release to send.
- **VAD (Voice Activity Detection)**: Automatically detects when you stop speaking.
- **Smart Audio Management**: Handles audio device locking/unlocking to prevent hanging (common issue on macOS CoreAudio).
- **Graceful Cleanup**: Aggressive garbage collection and process cleanup to ensure long-running stability.
- **Context Aware**: Remembers conversation history (via Ollama context).

## 🛠 Prerequisites

- macOS (required for `afplay` audio backend)
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running
- [FFmpeg](https://ffmpeg.org/) (required by Whisper)
   ```bash
   brew install ffmpeg
   ```
- ElevenLabs API Key

## 🚀 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/asistenque.git
    cd asistenque
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is missing, you'll need `openai-whisper`, `sounddevice`, `numpy`, `webrtcvad`, `scipy`, `pynput`, `requests`, `python-dotenv`, `elevenlabs`)*

4.  **Setup Environment Variables**
    Create a `.env` file in the root directory:
    ```bash
    cp .env.example .env  # if example exists, otherwise create new
    ```

    **Required `.env` variables:**
    ```ini
    # ElevenLabs (TTS)
    ELEVENLABS_API_KEY=your_api_key_here
    ELEVENLABS_VOICE_ID=your_voice_id_here
    
    # Ollama (LLM)
    OLLAMA_URL=http://localhost:11434/api/generate
    MODEL_NAME=qwen2.5:7b
    
    # System
    DEBUG_MODE=False
    ```
    
    **Optional settings (defaults provided in code):**
    ```ini
    SAMPLE_RATE=44100
    FRAME_DURATION=30
    SILENCE_TIMEOUT=1.5
    VAD_MODE=2
    ROLE_PROMPT="You are a helpful assistant..."
    WHISPER_TRANSCRIBE_PROMPT="A conversation in Indonesian..."
    ```

## 🎮 Usage

1.  **Start Ollama Server**
    Ensure Ollama is running:
    ```bash
    ollama serve
    ```

2.  **Run the Assistant**
    ```bash
    python main.py
    ```

3.  **Interact**
    - The app checks for Accessibility Permissions (needed for keyboard listening). If not granted, it falls back to "Press Enter" mode.
    - **Press & Hold SPACE** (or just press depending on config) to speak.
    - Press **ESC** to exit.

## ⚠️ Troubleshooting

- **Audio Device Error / Hangs**: The app includes aggressive audio device resetting (`sd.stop()`, `sd.default.reset()`) to handle macOS CoreAudio flakiness. If it hangs, try restarting the script.
- **Keyboard Permission**: On macOS, you must grant "Input Monitoring" or "Accessibility" permission to your terminal (iTerm2 / Terminal.app) for global hotkeys to work.

## 📄 License

[MIT](LICENSE)

## 🐳 Docker Support

You can run Asistenque in a Docker container, though a Linux host is recommended for the best hardware compatibility (audio/microphone).

1.  **Build the Image**
    ```bash
    docker build -t asistenque .
    ```

2.  **Run the Container**
    
    *Using `docker run` flags to pass hardware access:*

    **Linux (Recommended):**
    ```bash
    docker run -it \
      --device /dev/snd \
      --env-file .env \
      asistenque
    ```

    **macOS / Windows:**
    > ⚠️ Audio input/output and keyboard monitoring (`pynput`) are difficult to bridge from Docker Desktop to the host. You may need to install PulseAudio servers or similar workarounds, or run the app natively.

    The Dockerfile includes `mpg123` for audio playback fallback if `afplay` (macOS) is not available.
