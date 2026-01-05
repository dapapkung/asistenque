import warnings
import os
import gc
import threading
import time

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
if DEBUG_MODE == "false":
    warnings.filterwarnings("ignore")

import whisper
import sounddevice as sd
import numpy as np
import webrtcvad
import queue
from scipy.io.wavfile import write
import tempfile

from config.config import (
    SAMPLE_RATE,
    FRAME_DURATION,
    SILENCE_TIMEOUT,
    VAD_MODE,
    WHISPER_TRANSCRIBE_PROMPT,
)

# ===== GLOBAL STATE =====
# Load model ONCE (shared memory)
_whisper_model = whisper.load_model(WHISPER_MODEL, device="cpu")
print("✅ Whisper loaded!")

# Thread-safe recorder
_recorder_lock = threading.Lock()


class AudioRecorder:
    """Thread-safe audio recorder dengan VAD"""
    
    def __init__(self):
        self.vad = webrtcvad.Vad(VAD_MODE)
        self.audio_queue = queue.Queue()
        self.stream = None
        
    def audio_callback(self, indata, frames, time_info, status):
        """Callback untuk audio stream"""
        if status:
            print(f"⚠️  Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def find_input_device(self):
        """Cari input device yang tersedia"""
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev.get("max_input_channels", 0) > 0:
                    return i
            return None
        except:
            return None
    
    def record_until_silence(self):
        """Record audio sampai terdeteksi silence"""
        try:
            # Clear queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except:
                    break
            
            # CRITICAL: Stop ALL audio first
            print("🔄 Stopping all audio devices...")
            sd.stop()
            sd.default.reset()
            time.sleep(0.3)  # Longer wait for macOS
            
            # Find input device
            input_device = self.find_input_device()
            if input_device is not None:
                print(f"🎤 Using input device {input_device}")
            
            # Create stream with explicit device
            self.stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=int(SAMPLE_RATE * FRAME_DURATION / 1000),
                dtype="int16",
                channels=1,
                callback=self.audio_callback,
                device=input_device
            )
            
            frames = []
            silence_frames = 0
            max_silence_frames = int(SILENCE_TIMEOUT * 1000 / FRAME_DURATION)
            speech_detected = False
            
            print("🎙️  Mulai bicara...")
            
            with self.stream:
                while True:
                    try:
                        frame = self.audio_queue.get(timeout=5.0)
                    except queue.Empty:
                        break
                    
                    frames.append(frame)
                    
                    # VAD check
                    try:
                        is_speech = self.vad.is_speech(frame, SAMPLE_RATE)
                        if is_speech:
                            silence_frames = 0
                            speech_detected = True
                        else:
                            silence_frames += 1
                    except:
                        silence_frames += 1
                    
                    # Check silence timeout
                    if speech_detected and silence_frames > max_silence_frames:
                        print("🔇 Silence detected")
                        break
                    
                    # Max recording limit (30s)
                    if len(frames) > (30 * 1000 / FRAME_DURATION):
                        print("⏱️  Max time reached")
                        break
            
            if not frames:
                return None
            
            # Convert to numpy array
            audio_data = b"".join(frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            return audio_np
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
        finally:
            # CRITICAL: Complete cleanup
            print("🔄 Cleaning up audio devices...")
            self.stream = None
            
            # Full stop and reset
            sd.stop()
            time.sleep(0.2)
            sd.default.reset()
            time.sleep(0.3)  # Extra wait for macOS
            
            print("✅ Audio devices released")


# Global recorder instance (reuse)
_recorder = AudioRecorder()


def record_audio():
    """Record audio menggunakan thread-safe recorder"""
    with _recorder_lock:
        return _recorder.record_until_silence()


def speech_to_text():
    """Convert speech to text menggunakan Whisper"""
    
    # Record audio
    audio_np = record_audio()
    
    if audio_np is None or len(audio_np) == 0:
        print("⚠️  No audio recorded")
        return ""
    
    # Save to temp file untuk Whisper
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            write(f.name, SAMPLE_RATE, audio_np)
            temp_path = f.name
        
        # Whisper transcribe
        
        prompt = (
            WHISPER_TRANSCRIBE_PROMPT
        )
        
        print("🧠 Transcribing...") 
        
        result = _whisper_model.transcribe(
            temp_path,
            language="id",
            initial_prompt=prompt,
            task="transcribe",
            temperature=0.0,
            best_of=3,
            beam_size=3,
            condition_on_previous_text=False,
            word_timestamps=False,
            fp16=False,
        )
        
        return result["text"]
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        # CRITICAL: Full audio cleanup after Whisper
        print("🔄 Final audio cleanup after STT...")
        sd.stop()
        time.sleep(0.2)
        sd.default.reset()
        time.sleep(0.5)  # Extra wait for device release
        
        # Free memory aggressively
        print("🧹 Freeing memory...")
        gc.collect()
        time.sleep(0.2)
        
        print("✅ STT complete, devices ready for TTS")


def cleanup_audio():
    """Cleanup audio resources"""
    try:
        sd.stop()
        time.sleep(0.2)
        sd.default.reset()
        time.sleep(0.3)
        gc.collect()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
