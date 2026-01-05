import time
import threading
import os
import subprocess
import tempfile

from helpers.elevenlabs_tts import text_to_speech_stream

# Thread-safe audio player
class AudioPlayer:
    def __init__(self):
        self.is_playing = False
        self.play_lock = threading.Lock()
        
    def play_audio_file(self, audio_path):
        """Play audio file menggunakan afplay (macOS) atau mpg123 (Linux/Docker)"""
        try:
            with self.play_lock:
                self.is_playing = True
                
                # Check OS / available tools
                use_afplay = False
                try:
                    # Check if afplay exists
                    subprocess.run(["which", "afplay"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    use_afplay = True
                except:
                    pass
                
                if use_afplay:
                    player_cmd = ["afplay", audio_path]
                    print(f"   🔊 afplay: {audio_path}")
                else:
                    # Fallback to mpg123 (standard on Linux/Docker)
                    # -q = quiet
                    player_cmd = ["mpg123", "-q", audio_path]
                    print(f"   🔊 mpg123: {audio_path}")
                
                # IMPORTANT: Don't capture output, let it play naturally
                result = subprocess.run(
                    player_cmd,
                    timeout=60
                )
                
                self.is_playing = False
                
                if result.returncode == 0:
                    return True
                else:
                    print(f"⚠️  Player exit code: {result.returncode}")
                    return False
                    
        except subprocess.TimeoutExpired:
            print("⚠️  Playback timeout")
            self.is_playing = False
            return False
        except Exception as e:
            print(f"❌ Playback error: {e}")
            self.is_playing = False
            return False
    
    def wait_if_playing(self):
        """Wait jika sedang playing"""
        while self.is_playing:
            time.sleep(0.1)


# Global player instance (reuse across calls)
_audio_player = AudioPlayer()


def text_to_speech_direct(text):
    """
    Direct TTS dengan proper device management.
    Wait longer after download untuk ensure device ready.
    """
    print("🎧 TTS start (direct mode)")
    
    # Wait jika masih ada audio playing
    _audio_player.wait_if_playing()
    
    # Download audio
    print("📥 Downloading...")
    try:
        audio_stream = text_to_speech_stream(text)
        audio_stream.seek(0)
        audio_data = audio_stream.read()
        
        if len(audio_data) < 100:
            print(f"❌ Audio too small: {len(audio_data)} bytes")
            return False
            
        print(f"   ✅ Downloaded: {len(audio_data)} bytes")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False
    
    # Save to temp file
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name
        
        # Verify file
        file_size = os.path.getsize(temp_path)
        print(f"   📁 Saved: {file_size} bytes")
        
        if file_size < 100:
            print("❌ File too small after save")
            return False
        
        # CRITICAL: Wait longer before playing
        print("   ⏳ Waiting for audio system to stabilize...")
        time.sleep(0.8)  # Increased wait time
        
        print(f"▶️  Playing audio...")
        
        # Check OS / available tools
        use_afplay = False
        try:
            subprocess.run(["which", "afplay"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            use_afplay = True
        except:
            pass
            
        if use_afplay:
            player_cmd = ["afplay", temp_path]
        else:
            player_cmd = ["mpg123", "-q", temp_path]
        
        # Play audio
        result = subprocess.run(
            player_cmd,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ TTS complete")
            return True
        else:
            print(f"⚠️  Player failed with code: {result.returncode}")
            
            # Fallback for afplay only
            if use_afplay:
                print("🔄 Trying with explicit default device...")
                result2 = subprocess.run(
                    ["afplay", "-q", "1", temp_path],
                    timeout=60
                )
                
                if result2.returncode == 0:
                    print("✅ TTS complete (fallback)")
                    return True
                else:
                    print(f"❌ afplay fallback also failed: {result2.returncode}")
                    return False
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def text_to_speech(text):
    """
    Main TTS function.
    Gunakan direct mode untuk performa terbaik.
    """
    return text_to_speech_direct(text)


def reset_audio():
    """Minimal audio reset - hanya wait jika sedang playing"""
    _audio_player.wait_if_playing()
    time.sleep(0.2)
    print("✅ Audio ready")
