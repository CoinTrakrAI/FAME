#!/usr/bin/env python3
"""
F.A.M.E. - Text-to-Speech Engine
Natural voice responses for FAME
"""

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("[WARNING] pyttsx3 not available. Install with: pip install pyttsx3")

import threading
try:
    import queue
    QUEUE_AVAILABLE = True
except ImportError:
    QUEUE_AVAILABLE = False

import asyncio
from typing import Dict, Any


class TextToSpeechEngine:
    """Advanced TTS with multiple voice options"""
    
    def __init__(self):
        if not PYTTSX3_AVAILABLE:
            self.engine = None
            print("[WARNING] TTS engine not available")
        else:
            try:
                self.engine = pyttsx3.init()
                self._configure_engine()
            except Exception as e:
                print(f"[WARNING] TTS initialization failed: {e}")
                self.engine = None
        
        if QUEUE_AVAILABLE:
            self.speech_queue = queue.Queue()
        else:
            self.speech_queue = None
        
        self.is_speaking = False
    
    def _configure_engine(self):
        """Configure TTS engine"""
        if not self.engine:
            return
        
        try:
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Set voice (try to find a natural sounding voice)
            if len(voices) > 0:
                # Prefer female voices for natural sound
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech properties
            self.engine.setProperty('rate', 180)  # Speed percent
            self.engine.setProperty('volume', 0.8)  # Volume 0-1
        except Exception as e:
            print(f"[WARNING] TTS configuration error: {e}")
    
    async def speak(self, text: str, wait: bool = False):
        """Speak text"""
        if not self.engine:
            print("[WARNING] TTS engine not available")
            return
        
        def _speak():
            try:
                self.engine.say(text)
                if wait:
                    self.engine.runAndWait()
                else:
                    self.engine.startLoop(False)
                    self.engine.iterate()
                    self.engine.endLoop()
            except Exception as e:
                print(f"[ERROR] TTS error: {e}")
        
        # Run in thread to avoid blocking
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        
        if wait:
            thread.join()
    
    def speak_async(self, text: str):
        """Speak text asynchronously (add to queue)"""
        if not self.engine:
            print("[WARNING] TTS engine not available")
            return
        
        if self.speech_queue:
            self.speech_queue.put(text)
            if not self.is_speaking:
                self._start_speech_worker()
        else:
            # Fallback to direct speak
            self.speak(text, wait=False)
    
    def _start_speech_worker(self):
        """Start background speech worker"""
        if not self.engine:
            return
        
        def speech_worker():
            self.is_speaking = True
            while self.speech_queue and not self.speech_queue.empty():
                try:
                    text = self.speech_queue.get()
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[ERROR] Speech worker error: {e}")
            self.is_speaking = False
        
        thread = threading.Thread(target=speech_worker, daemon=True)
        thread.start()
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get current voice configuration"""
        if not self.engine:
            return {"error": "TTS engine not available"}
        
        try:
            return {
                "rate": self.engine.getProperty('rate'),
                "volume": self.engine.getProperty('volume'),
                "voice": self.engine.getProperty('voice'),
                "voices_available": len(self.engine.getProperty('voices'))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def set_voice_property(self, rate: int = None, volume: float = None):
        """Set voice properties"""
        if not self.engine:
            return
        
        try:
            if rate is not None:
                self.engine.setProperty('rate', rate)
            if volume is not None:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
        except Exception as e:
            print(f"[ERROR] Voice property setting error: {e}")


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator interface for text-to-speech"""
    if not PYTTSX3_AVAILABLE:
        return {"error": "TTS not available. Install pyttsx3."}
    
    text = request.get("text", "")
    if not text:
        return {"error": "No text provided"}
    
    async def speak_text():
        engine = TextToSpeechEngine()
        await engine.speak(text, wait=False)
        return {"success": True, "text": text}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(speak_text())
        return result
    finally:
        loop.close()

