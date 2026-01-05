import time
import signal
import sys
import gc
from concurrent.futures import ThreadPoolExecutor

from helpers.tts import text_to_speech, reset_audio
from helpers.llm import ask_llm
from helpers.stt import speech_to_text, cleanup_audio

# ===== GLOBAL STATE =====
running = True
space_pressed = False
keyboard_listener = None

# Thread pool untuk async operations
_executor = ThreadPoolExecutor(max_workers=2)


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    global running, keyboard_listener, _executor
    print("\n\n🛑 Stopping...")
    running = False
    
    if keyboard_listener:
        try:
            keyboard_listener.stop()
        except:
            pass
    
    # Shutdown thread pool
    _executor.shutdown(wait=False)
    
    cleanup_audio()
    reset_audio()
    
    print("👋 Bye!")
    sys.exit(0)


def check_accessibility():
    """Check keyboard accessibility"""
    try:
        from pynput import keyboard
        test = keyboard.Listener(on_press=lambda k: None)
        test.start()
        test.stop()
        return True
    except:
        return False


def print_banner():
    """Print banner"""
    print("\n" + "=" * 70)
    print("🤖 ASISTENQUE - Voice Assistant")
    print("=" * 70)
    print("⌨️  SPACE = Mulai bicara")
    print("🛑 ESC / Ctrl+C =Keluar")
    print("=" * 70 + "\n")
    
    if not check_accessibility():
        print("⚠️  Keyboard monitoring butuh Accessibility permission")
        print()
        response = input("Lanjut dengan ENTER mode? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
        return False
    
    return True


def on_press(key):
    """Handle key press"""
    global space_pressed, running, keyboard_listener
    
    try:
        from pynput import keyboard as kb
        if key == kb.Key.space:
            space_pressed = True
            return True
        elif key == kb.Key.esc:
            print("\n\n🛑 ESC pressed...")
            running = False
            space_pressed = False
            return False
    except AttributeError:
        pass
    
    return True


def wait_for_space():
    """Wait for space key"""
    global space_pressed, keyboard_listener, running
    
    try:
        from pynput import keyboard
    except ImportError:
        return False
    
    space_pressed = False
    
    print("\n" + "="*70)
    print("⌨️  Tekan SPACE untuk bicara (ESC = keluar)...")
    print("="*70)
    
    keyboard_listener = keyboard.Listener(on_press=on_press, suppress=False)
    keyboard_listener.start()
    
    # Efficient polling
    while not space_pressed and running:
        time.sleep(0.15)
    
    # Stop listener
    try:
        if keyboard_listener.is_alive():
            keyboard_listener.stop()
            keyboard_listener.join(timeout=0.5)
    except:
        pass
    
    keyboard_listener = None
    return space_pressed and running


def wait_for_enter():
    """Fallback: wait for ENTER"""
    print("\n" + "="*70)
    print("⏎  ENTER = bicara, 'exit' = keluar")
    print("="*70)
    
    try:
        resp = input().strip().lower()
        if resp in ['exit', 'quit', 'keluar']:
            return False
        return True
    except (KeyboardInterrupt, EOFError):
        return False


def conversation_cycle(cycle_num):
    """Single conversation cycle with PROPER device management"""
    try:
        print(f"\n{'='*70}")
        print(f"💬 Percakapan #{cycle_num}")
        print(f"{'='*70}")
        
        # === 1. STT ===
        print("\n🎤 [1/3] Listening...")
        text = speech_to_text()
        
        if not text or not text.strip():
            print("⚠️  No audio detected")
            return True
        
        print(f"📝 You: {text}")
        
        # Check exit command
        # if any(w in text.lower() for w in ["berhenti", "keluar", "stop", "exit", "selesai"]):
        #     print("\n👋 Bye!")
        #     return False
        
        # CRITICAL: Extra wait after STT to ensure device fully released
        print("\n⏳ Ensuring audio devices are fully released...")
        time.sleep(2.0)  # Increased from 0.2s
        
        # === 2. LLM ===
        print("\n🧠 [2/3] Thinking...")
        answer = ask_llm(text)
        
        print(f"\n💬 Zeta says:")
        print(f"   {answer}")
        
        # Prepare reply (ambil kalimat pertama untuk TTS)
        reply = answer.strip().split("\n")[0]
        reply = reply.replace(".", "... ")
        
        # CRITICAL: Extra wait before TTS
        print("\n⏳ Preparing audio output...")
        time.sleep(0.5)
        
        # === 3. TTS ===
        print("\n🔊 [3/3] Speaking...")
        tts_success = text_to_speech(reply)
        
        if not tts_success:
            print("⚠️  TTS failed, but continuing...")
        
        # CRITICAL: Aggressive cleanup after cycle
        print("\n🧹 Aggressive cleanup...")
        
        # Force garbage collection TWICE
        gc.collect()
        time.sleep(0.2)
        gc.collect()
        time.sleep(0.2)
        
        # Extra audio cleanup
        cleanup_audio()
        
        print(f"\n✅ Percakapan #{cycle_num} complete!")
        return True
        
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("🔄 Continuing...\n")
        
        try:
            cleanup_audio()
            reset_audio()
            gc.collect()
        except:
            pass
        
        time.sleep(1.0)
        return True


def main_loop():
    """Main loop"""
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    
    has_keyboard = print_banner()
    
    cycle_num = 1
    
    print("✨ AsistenQue ready!\n")
    
    # Initial cleanup
    try:
        cleanup_audio()
        reset_audio()
        time.sleep(0.5)
    except:
        pass
    
    while running:
        try:
            # Wait for trigger
            if has_keyboard:
                triggered = wait_for_space()
            else:
                triggered = wait_for_enter()
            
            if not triggered:
                break
            
            time.sleep(0.3)
            
            # Run conversation cycle
            should_continue = conversation_cycle(cycle_num)
            
            if not should_continue:
                break
            
            cycle_num += 1
            
            # Longer delay between cycles to ensure full cleanup
            print("\n⏳ Cooling down before next cycle...")
            time.sleep(1.5)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Ctrl+C...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔄 Restarting...")
            
            try:
                cleanup_audio()
                reset_audio()
                gc.collect()
            except:
                pass
            
            time.sleep(1.0)
    
    # Final cleanup
    print("\n🧹 Final cleanup...")
    try:
        cleanup_audio()
        reset_audio()
        gc.collect()
        _executor.shutdown(wait=True, cancel_futures=True)
    except:
        pass
    
    print("👋 Thanks!")


if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        try:
            cleanup_audio()
            reset_audio()
            gc.collect()
            _executor.shutdown(wait=False)
        except:
            pass
        sys.exit(1)
