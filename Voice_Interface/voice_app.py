import threading
import queue
import time
import json
from pathlib import Path

# Try importing voice libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

class VoiceInterface:
    def __init__(self):
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
            except:
                self.microphone = None
                print("Warning: No microphone found")
        else:
            self.recognizer = None
            self.microphone = None
        
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Configure voice
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    self.tts_engine.setProperty('voice', voices[0].id)
                self.tts_engine.setProperty('rate', 150)
            except:
                self.tts_engine = None
        else:
            self.tts_engine = None
        
        self.audio_queue = queue.Queue()
        self.listening = False
        self.processing = False
        
        # Calibrate microphone if available
        if self.microphone and self.recognizer:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
            except:
                pass
    
    def start_listening(self):
        """Start continuous voice listening"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("Speech recognition not available. Install with: pip install speechrecognition")
            return
            
        if not self.microphone:
            print("No microphone available")
            return
            
        self.listening = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._process_loop, daemon=True).start()
        
    def stop_listening(self):
        """Stop voice listening"""
        self.listening = False
        
    def _listen_loop(self):
        """Continuous listening loop"""
        while self.listening:
            try:
                print("🎤 Listening...")
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    self.audio_queue.put(audio)
                    
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Listening error: {e}")
                time.sleep(1)
    
    def _process_loop(self):
        """Process audio from queue"""
        while self.listening:
            try:
                audio = self.audio_queue.get(timeout=1)
                threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()
                
            except queue.Empty:
                continue
    
    def _process_audio(self, audio):
        """Process a single audio input"""
        try:
            # Convert speech to text
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            
            # Send to F.A.M.E system
            response = self.send_to_fame(text)
            
            # Speak response
            self.speak(response)
            
        except sr.UnknownValueError:
            self.speak("I didn't understand that. Could you please repeat?")
        except sr.RequestError as e:
            self.speak("Sorry, there was an error with the speech recognition service.")
        except Exception as e:
            print(f"Processing error: {e}")
    
    def send_to_fame(self, text):
        """Send text to F.A.M.E system and get response"""
        if not REQUESTS_AVAILABLE:
            return "Request library not available. Install with: pip install requests"
            
        try:
            # Use LocalAI for response generation
            response = requests.post(
                "http://localhost:8080/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are F.A.M.E 6.0, a living AI system. Respond naturally and helpfully."},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 150
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return "I'm having trouble processing that right now. Please try again."
                
        except requests.exceptions.ConnectionError:
            return "Cannot connect to LocalAI. Please make sure LocalAI is running on localhost:8080"
        except Exception as e:
            return f"System temporarily unavailable: {str(e)}"
    
    def speak(self, text):
        """Convert text to speech"""
        if not self.tts_engine:
            print(f"TTS not available. Would speak: {text}")
            return
            
        try:
            print(f"Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")

# Standalone voice app
if __name__ == "__main__":
    voice_app = VoiceInterface()
    print("🎤 F.A.M.E Voice Interface Started")
    print("Speak to interact with the system...")
    
    try:
        voice_app.start_listening()
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        voice_app.stop_listening()
        print("\n🔇 Voice Interface Stopped")

