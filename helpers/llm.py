import requests
from config.config import (
    OLLAMA_URL,
    MODEL_NAME,
    ROLE_PROMPT,
)

def ask_llm(user_text):
    prompt = f"""
    {ROLE_PROMPT}

    User:
    {user_text}

    Assistant:
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    return response.json()["response"]