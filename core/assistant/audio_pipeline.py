#!/usr/bin/env python3
"""
F.A.M.E. Assistant - Audio Pipeline
STT/TTS + wake-word detection
"""

import os
import threading
import queue
import subprocess
import time
import tempfile
import pathlib
from typing import Optional, Callable

# Choose STT backend: "whisper", "vosk", "google", "speech_recognition"
STT_BACKEND = os.getenv("FAME_STT_BACKEND", "speech_recognition")
TTS_BACKEND = os.getenv("FAME_TTS_BACKEND", "pyttsx3")  # or "polly", "gcloud"

# Wake words
DEFAULT_WAKEWORDS = ("hey fame", "ok fame", "jarvis", "fame", "activate")


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Convert raw audio bytes into text. This is a small wrapper: pick your backend.
    - whisper: call openai/whisper local or via API
    - vosk: local ASR for offline usage
    - google: cloud speech-to-text (requires credentials)
    - speech_recognition: uses Google Speech Recognition (default)
    """
    if STT_BACKEND == "whisper":
        try:
            # prefer whisper local CLI if installed
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(audio_bytes)
            tmp.flush()
            tmp.close()
            
            # call whisper CLI (needs to be installed) — fast for short audio
            out = subprocess.check_output(
                ["whisper", tmp.name, "--model", "small", "--language", "en", "--task", "transcribe"],
                stderr=subprocess.DEVNULL
            )
            
            # whisper CLI prints transcript to stdout file named <tmp>.txt — read it
            txtfile = pathlib.Path(tmp.name).with_suffix(".txt")
            if txtfile.exists():
                text = txtfile.read_text(encoding="utf-8")
                os.unlink(tmp.name)
                if txtfile.exists():
                    os.unlink(txtfile)
                return text.strip()
            return ""
        except Exception:
            return ""
    
    elif STT_BACKEND == "vosk":
        # Placeholder — wire up Vosk Model
        try:
            import vosk
            import json
            # Initialize model (you'd load this once)
            # model = vosk.Model("path/to/model")
            # rec = vosk.KaldiRecognizer(model, 16000)
            # rec.AcceptWaveform(audio_bytes)
            # result = json.loads(rec.Result())
            # return result.get("text", "")
            return "<vosk-transcript>"
        except ImportError:
            return ""
    
    elif STT_BACKEND == "speech_recognition":
        # Use speech_recognition library (default)
        try:
            import speech_recognition as sr
            import io
            r = sr.Recognizer()
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            return text
        except Exception as e:
            print(f"[STT] Error: {e}")
            return ""
    
    else:
        # Placeholder for cloud STT (Google Cloud, AWS Transcribe, etc.)
        return "<cloud-stt-transcript>"


def transcribe_microphone(timeout: float = 5.0, phrase_time_limit: float = 10.0) -> str:
    """
    Transcribe from microphone using speech_recognition (default)
    """
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        
        with sr.Microphone() as source:
            print("[STT] Listening...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        
        try:
            text = r.recognize_google(audio)
            print(f"[STT] Heard: {text}")
            return text
        except sr.UnknownValueError:
            print("[STT] Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"[STT] Error: {e}")
            return ""
    except Exception as e:
        print(f"[STT] Microphone error: {e}")
        return ""


def speak_text(text: str):
    """Synthesize and play text. Default uses pyttsx3 for offline TTS."""
    if TTS_BACKEND == "pyttsx3":
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Error: {e}")
            print(f"[TTS fallback] {text}")
    elif TTS_BACKEND == "polly":
        # AWS Polly integration
        try:
            import boto3
            polly = boto3.client('polly')
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Joanna'
            )
            # Play audio (requires pyaudio or similar)
            print(f"[TTS] {text}")
        except Exception:
            print(f"[TTS fallback] {text}")
    else:
        print(f"[TTS fallback] {text}")


def detect_wakeword_from_text(transcript: str, wakewords: tuple = None) -> bool:
    """
    Minimal wakeword detector from text transcript.
    In production, use Porcupine or Snowboy for audio-level wake-word detection.
    """
    if not transcript:
        return False
    
    if wakewords is None:
        wakewords = DEFAULT_WAKEWORDS
    
    t = transcript.lower()
    return any(w in t for w in wakewords)


def detect_wakeword_from_audio(audio_bytes: bytes, wakewords: tuple = None) -> bool:
    """
    Audio-level wake-word detection (placeholder).
    For production, integrate Porcupine (Picovoice) or Snowboy.
    """
    # Transcribe and check text
    transcript = transcribe_audio_bytes(audio_bytes)
    return detect_wakeword_from_text(transcript, wakewords)

