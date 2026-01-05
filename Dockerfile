# Base image Python 3.10
FROM python:3.10-slim

# Set environment variables
# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# portaudio19-dev: for sounddevice/pyaudio
# libasound2-dev: ALSA sound library
# ffmpeg: for whisper audio processing
# mpg123: for playing mp3 files (TTS output)
# gcc: for compiling some python packages
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    ffmpeg \
    mpg123 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user (optional but good practice, though for audio access root is often easier in Docker)
# For simplicity with hardware, we'll run as root by default, but users can override

# Command to run the application
CMD ["python", "main.py"]
