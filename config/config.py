import os
from typing import Final

def get_env(
    key: str,
    default=None,
    cast=None,
):
    value = os.getenv(key, default)
    if value is None:
        return value
    return cast(value) if cast else value


# ===== Audio & VAD =====
SAMPLE_RATE: Final[int] = get_env("SAMPLE_RATE", 44100, int)
FRAME_DURATION: Final[int] = get_env("FRAME_DURATION", 30, int)  # ms
SILENCE_TIMEOUT: Final[float] = get_env("SILENCE_TIMEOUT", 1.5, float) # seconds
VAD_MODE: Final[int] = get_env("VAD_MODE", 2, int)  # 0–3

# ===== LLM / Ollama =====
OLLAMA_URL: Final[str] = get_env(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)
MODEL_NAME: Final[str] = get_env(
    "MODEL_NAME",
    "qwen2.5:7b",
)

# ===== Prompt =====
ROLE_PROMPT = (
    get_env("ROLE_PROMPT", "")
    .replace("\\n", "\n")
    .strip()
)

WHISPER_TRANSCRIBE_PROMPT = (
    get_env("WHISPER_TRANSCRIBE_PROMPT", "")
    .replace("\\n", "\n")
    .strip()
)
