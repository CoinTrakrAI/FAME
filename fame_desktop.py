#!/usr/bin/env python3
"""
F.A.M.E 6.0 Desktop Application
Complete GUI with Voice Interface & Docker Integration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import subprocess
import sys
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Try importing optional dependencies
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

def connect_to_docker():
    """Connect to Docker Desktop with proper error handling"""
    if not DOCKER_AVAILABLE or docker is None:
        return None
    
    # Try to get the Docker host from environment variable, otherwise use default for Windows
    docker_host = os.environ.get('DOCKER_HOST', 'npipe:////./pipe/docker_engine')
    
    try:
        # Explicitly create a client with the specified host
        client = docker.DockerClient(base_url=docker_host)
        # Test the connection
        client.ping()
        return client
    except docker.errors.DockerException as e:
        logging.debug(f"Failed to connect to Docker: {e}")
        # Try alternative connection method
        try:
            client = docker.from_env()
            client.ping()
            return client
        except:
            return None
    except Exception as e:
        logging.debug(f"Docker connection error: {e}")
        return None

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

import queue
import time

class FAMEDesktopApp:
    """Main Desktop Application for F.A.M.E 6.0"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("F.A.M.E 6.0 - Living AI System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # System state
        self.system_running = False
        self.voice_enabled = False
        self.localai_running = False
        self.docker_available = DOCKER_AVAILABLE
        
        # Voice components
        if SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
            
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
            except:
                self.tts_engine = None
        else:
            self.tts_engine = None
            
        self.audio_queue = queue.Queue()
        
        # Docker client with proper connection handling
        if self.docker_available:
            self.docker_client = connect_to_docker()
            if self.docker_client:
                self.docker_available = True
                logging.info("✅ Successfully connected to Docker Desktop!")
            else:
                self.docker_available = False
                logging.debug("⚠️ Docker Desktop not available or not running")
        else:
            self.docker_client = None
        
        self.setup_gui()
        self.check_system_status()
        self.check_internet_connectivity()
    
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, 
                             text="🧠 F.A.M.E 6.0 - Living AI System", 
                             font=("Arial", 20, "bold"),
                             fg="#00ff00", bg="#1e1e1e")
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Status panel
        self.setup_status_panel(main_frame)
        
        # Control panel
        self.setup_control_panel(main_frame)
        
        # Chat interface
        self.setup_chat_interface(main_frame)
        
        # System monitor
        self.setup_system_monitor(main_frame)
        
        # Training interface
        self.setup_training_interface(main_frame)
    
    def setup_status_panel(self, parent):
        """Setup system status panel"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status indicators
        self.status_labels = {}
        statuses = [
            ("F.A.M.E System", "Stopped", "red"),
            ("LocalAI", "Stopped", "red"), 
            ("Voice Interface", "Disabled", "red"),
            ("Docker", "Available" if self.docker_available else "Not Available", 
             "green" if self.docker_available else "red"),
            ("Internet", "Checking...", "yellow")
        ]
        
        for i, (name, status, color) in enumerate(statuses):
            tk.Label(status_frame, text=f"{name}:", fg="white", bg="#1e1e1e").grid(row=0, column=i*2, padx=5)
            self.status_labels[name] = tk.Label(status_frame, text=status, fg=color, bg="#1e1e1e", font=("Arial", 10, "bold"))
            self.status_labels[name].grid(row=0, column=i*2+1, padx=5)
    
    def setup_control_panel(self, parent):
        """Setup control buttons"""
        control_frame = ttk.LabelFrame(parent, text="System Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        self.start_btn = tk.Button(control_frame, text="🚀 Start F.A.M.E", 
                                 command=self.start_system, bg="#00aa00", fg="white", font=("Arial", 12))
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="🛑 Stop F.A.M.E", 
                                command=self.stop_system, bg="#aa0000", fg="white", font=("Arial", 12), state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.voice_btn = tk.Button(control_frame, text="🎤 Enable Voice", 
                                 command=self.toggle_voice, bg="#0055aa", fg="white", font=("Arial", 12))
        self.voice_btn.grid(row=0, column=2, padx=5)
        
        self.localai_btn = tk.Button(control_frame, text="🤖 Start LocalAI", 
                                   command=self.toggle_localai, bg="#aa5500", fg="white", font=("Arial", 12))
        self.localai_btn.grid(row=0, column=3, padx=5)
        
        self.train_btn = tk.Button(control_frame, text="🧠 Open Training", 
                                 command=self.open_training_interface, bg="#5500aa", fg="white", font=("Arial", 12))
        self.train_btn.grid(row=0, column=4, padx=5)
    
    def setup_chat_interface(self, parent):
        """Setup chat interface"""
        chat_frame = ttk.LabelFrame(parent, text="Chat Interface", padding="10")
        chat_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=15, width=70, bg="#2d2d2d", fg="#ffffff")
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.chat_display.insert(tk.END, "F.A.M.E 6.0 System Ready\nType or use voice to interact...\n\n")
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        self.chat_input = tk.Entry(chat_frame, width=60, bg="#3d3d3d", fg="#ffffff")
        self.chat_input.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        self.chat_input.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(chat_frame, text="Send", command=self.send_message, bg="#0055aa", fg="white")
        self.send_btn.grid(row=1, column=1, padx=5)
        
        # Voice chat button
        self.voice_chat_btn = tk.Button(chat_frame, text="🎤 Voice Input", 
                                      command=self.start_voice_input, bg="#aa0055", fg="white")
        self.voice_chat_btn.grid(row=2, column=0, columnspan=2, pady=5)
    
    def setup_system_monitor(self, parent):
        """Setup system monitoring panel"""
        monitor_frame = ttk.LabelFrame(parent, text="System Monitor", padding="10")
        monitor_frame.grid(row=3, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Vital signs
        vital_labels = ["Cognitive Activity", "Adaptation Rate", "Goal Achievement", "Health Score"]
        self.vital_bars = {}
        
        for i, label in enumerate(vital_labels):
            tk.Label(monitor_frame, text=label, fg="white", bg="#1e1e1e").grid(row=i, column=0, sticky=tk.W, pady=2)
            self.vital_bars[label] = ttk.Progressbar(monitor_frame, length=150)
            self.vital_bars[label].grid(row=i, column=1, pady=2)
            self.vital_bars[label]['value'] = 50  # Default value
        
        # Memory usage
        tk.Label(monitor_frame, text="Memory Usage", fg="white", bg="#1e1e1e").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.memory_bar = ttk.Progressbar(monitor_frame, length=150)
        self.memory_bar.grid(row=4, column=1, pady=2)
        self.memory_bar['value'] = 30  # Default value
        
        # Active goals
        goals_frame = ttk.Frame(monitor_frame)
        goals_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        tk.Label(goals_frame, text="Active Goals:", fg="white", bg="#1e1e1e", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.goals_list = tk.Listbox(goals_frame, height=4, bg="#2d2d2d", fg="#ffffff")
        self.goals_list.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.goals_list.insert(0, "Learning from interactions")
        self.goals_list.insert(1, "Maintaining system health")
    
    def setup_training_interface(self, parent):
        """Setup training controls"""
        train_frame = ttk.LabelFrame(parent, text="Model Training", padding="10")
        train_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Training controls
        tk.Button(train_frame, text="📊 Start Training Session", 
                 command=self.start_training, bg="#005500", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(train_frame, text="📈 View Training Progress", 
                 command=self.view_training_progress, bg="#000055", fg="white").grid(row=0, column=1, padx=5)
        tk.Button(train_frame, text="🔄 Update Models", 
                 command=self.update_models, bg="#550055", fg="white").grid(row=0, column=2, padx=5)
        
        # Training status
        self.training_status = tk.Label(train_frame, text="Training: Idle", fg="yellow", bg="#1e1e1e")
        self.training_status.grid(row=0, column=3, padx=10)
    
    def check_system_status(self):
        """Check and update system status"""
        # Check if LocalAI is running
        try:
            import requests
            response = requests.get("http://localhost:8080/ready", timeout=2)
            self.localai_running = response.status_code == 200
        except:
            self.localai_running = False
        
        # Recheck Docker connection
        if self.docker_available and not self.docker_client:
            self.docker_client = connect_to_docker()
            self.docker_available = (self.docker_client is not None)
        
        # Update status labels
        if "LocalAI" in self.status_labels:
            self.status_labels["LocalAI"].config(
                text="Running" if self.localai_running else "Stopped",
                fg="green" if self.localai_running else "red"
            )
        
        if "F.A.M.E System" in self.status_labels:
            self.status_labels["F.A.M.E System"].config(
                text="Running" if self.system_running else "Stopped",
                fg="green" if self.system_running else "red"
            )
        
        if "Voice Interface" in self.status_labels:
            self.status_labels["Voice Interface"].config(
                text="Enabled" if self.voice_enabled else "Disabled",
                fg="green" if self.voice_enabled else "red"
            )
        
        if "Docker" in self.status_labels:
            self.status_labels["Docker"].config(
                text="Available" if self.docker_available else "Not Available",
                fg="green" if self.docker_available else "red"
            )
        
        # Update every 5 seconds
        self.root.after(5000, self.check_system_status)
    
    def check_internet_connectivity(self):
        """Check internet connectivity and update status"""
        def _check():
            try:
                import requests
                response = requests.get("https://www.google.com", timeout=3)
                self.internet_connected = response.status_code == 200
            except:
                self.internet_connected = False
            
            # Update UI
            if "Internet" in self.status_labels:
                status_text = "Online - Learning" if self.internet_connected else "Offline"
                self.status_labels["Internet"].config(
                    text=status_text,
                    fg="green" if self.internet_connected else "red"
                )
            
            # Schedule next check
            self.root.after(self.internet_check_interval * 1000, self.check_internet_connectivity)
        
        # Run check in background thread
        threading.Thread(target=_check, daemon=True).start()
    
    def start_system(self):
        """Start the F.A.M.E system"""
        def run_system():
            try:
                # Try to import from parent directory or use mock
                sys.path.insert(0, str(Path(__file__).parent.parent))
                try:
                    from fame_living import FAMELivingSystem
                    
                    # This would need to be properly integrated
                    self.system_running = True
                    self.update_ui_state()
                    self.root.after(0, lambda: self.add_to_chat("🚀 F.A.M.E 6.0 Living System Started"))
                except ImportError:
                    # F.A.M.E system not available, use mock
                    self.system_running = True
                    self.update_ui_state()
                    self.root.after(0, lambda: self.add_to_chat("🚀 F.A.M.E 6.0 System Started (Standalone Mode)"))
                    self.root.after(0, lambda: self.add_to_chat("⚠️ Note: Full F.A.M.E system not found. Running in desktop-only mode."))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("System Error", f"Failed to start F.A.M.E: {str(e)}"))
        
        threading.Thread(target=run_system, daemon=True).start()
        self.add_to_chat("🚀 Starting F.A.M.E 6.0 Living System...")
    
    def stop_system(self):
        """Stop the F.A.M.E system"""
        self.system_running = False
        self.update_ui_state()
        self.add_to_chat("🛑 F.A.M.E System Stopped")
    
    def toggle_voice(self):
        """Toggle voice interface"""
        if not SPEECH_RECOGNITION_AVAILABLE or not TTS_AVAILABLE:
            messagebox.showwarning("Voice Not Available", 
                                  "Speech recognition or TTS libraries not installed.\n"
                                  "Install with: pip install speechrecognition pyttsx3 pyaudio")
            return
            
        self.voice_enabled = not self.voice_enabled
        self.update_ui_state()
        
        if self.voice_enabled:
            self.add_to_chat("🎤 Voice Interface Enabled")
            self.speak("Voice interface enabled. I am ready to listen.")
        else:
            self.add_to_chat("🔇 Voice Interface Disabled")
    
    def toggle_localai(self):
        """Toggle LocalAI Docker container"""
        # Try to reconnect to Docker if needed
        if not self.docker_client:
            self.docker_client = connect_to_docker()
            if not self.docker_client:
                messagebox.showerror(
                    "Docker Error", 
                    "Docker Desktop is not available or not running.\n\n"
                    "Please:\n"
                    "1. Install Docker Desktop from docker.com\n"
                    "2. Start Docker Desktop (whale icon in system tray)\n"
                    "3. Ensure Docker is running\n\n"
                    "You can also set DOCKER_HOST environment variable:\n"
                    "Variable: DOCKER_HOST\n"
                    "Value: npipe:////./pipe/docker_engine\n\n"
                    "See DOCKER_SETUP_GUIDE.md for detailed instructions."
                )
                return
        
        try:
            if self.localai_running:
                # Stop LocalAI
                try:
                    container = self.docker_client.containers.get('local-ai')
                    container.stop()
                    self.add_to_chat("🤖 LocalAI Stopped")
                    self.localai_running = False
                except Exception as e:
                    if hasattr(docker, 'errors') and isinstance(e, docker.errors.NotFound):
                        self.add_to_chat("⚠️ LocalAI container not found")
                    else:
                        self.add_to_chat(f"⚠️ Error stopping LocalAI: {str(e)}")
            else:
                # Start LocalAI using docker-compose or direct run
                compose_file = Path(__file__).parent / "docker-compose.yml"
                if compose_file.exists():
                    try:
                        result = subprocess.run(
                            ["docker-compose", "up", "-d", "localai"],
                            cwd=Path(__file__).parent,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if result.returncode == 0:
                            self.add_to_chat("🤖 LocalAI Starting via Docker Compose...")
                        else:
                            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                            self.add_to_chat(f"⚠️ Docker Compose error: {error_msg}")
                    except subprocess.TimeoutExpired:
                        self.add_to_chat("⚠️ Docker Compose timed out - trying direct docker run...")
                        self._start_localai_direct()
                    except FileNotFoundError:
                        # docker-compose not found, try direct docker run
                        self._start_localai_direct()
                else:
                    self._start_localai_direct()
                
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "refused" in error_msg.lower():
                messagebox.showerror(
                    "Docker Connection Error",
                    f"Cannot connect to Docker.\n\n{error_msg}\n\n"
                    "Please ensure Docker Desktop is running."
                )
            else:
                messagebox.showerror("LocalAI Error", f"Failed to control LocalAI: {error_msg}")
    
    def _start_localai_direct(self):
        """Start LocalAI using direct docker run command"""
        try:
            result = subprocess.run([
                "docker", "run", "-d", "--name", "local-ai", 
                "-p", "8080:8080", "localai/localai:latest-aio-cpu"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.add_to_chat("🤖 LocalAI Starting...")
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                self.add_to_chat(f"⚠️ Docker run error: {error_msg}")
        except subprocess.TimeoutExpired:
            self.add_to_chat("⚠️ Docker run timed out")
        except FileNotFoundError:
            messagebox.showerror("Docker Not Found", "Docker command not found. Please install Docker Desktop.")
    
    def open_training_interface(self):
        """Open the training interface window"""
        training_window = tk.Toplevel(self.root)
        training_window.title("F.A.M.E Training Interface")
        training_window.geometry("800x600")
        training_window.configure(bg='#1e1e1e')
        
        # Try to import training GUI
        try:
            sys.path.insert(0, str(Path(__file__).parent / "Training_Interface"))
            from training_gui import TrainingGUI
            TrainingGUI(training_window)
        except ImportError:
            # Show basic message if training GUI not available
            tk.Label(training_window, text="Training Interface", 
                    font=("Arial", 16), bg="#1e1e1e", fg="white").pack(pady=20)
            tk.Label(training_window, text="Training interface module not found.", 
                    bg="#1e1e1e", fg="yellow").pack()
    
    def send_message(self, event=None):
        """Send message to F.A.M.E system"""
        message = self.chat_input.get()
        if not message.strip():
            return
        
        self.add_to_chat(f"You: {message}")
        self.chat_input.delete(0, tk.END)
        
        # Process message (would integrate with actual F.A.M.E system)
        response = self.process_message(message)
        self.add_to_chat(f"F.A.M.E: {response}")
        
        # Speak response if voice enabled
        if self.voice_enabled and self.tts_engine:
            self.speak(response)
    
    def start_voice_input(self):
        """Start voice input"""
        if not self.voice_enabled:
            messagebox.showwarning("Voice Disabled", "Please enable voice interface first")
            return
        
        if not self.recognizer:
            messagebox.showerror("Voice Error", "Speech recognition not available")
            return
        
        def listen():
            try:
                microphone = sr.Microphone()
                with microphone as source:
                    self.add_to_chat("🎤 Listening...")
                    audio = self.recognizer.listen(source, timeout=10)
                    
                    text = self.recognizer.recognize_google(audio)
                    self.add_to_chat(f"You: {text}")
                    
                    # Process the voice input
                    response = self.process_message(text)
                    self.add_to_chat(f"F.A.M.E: {response}")
                    self.speak(response)
                    
            except sr.WaitTimeoutError:
                self.add_to_chat("⏰ Listening timeout")
            except sr.UnknownValueError:
                self.add_to_chat("❌ Could not understand audio")
            except Exception as e:
                self.add_to_chat(f"❌ Voice input error: {str(e)}")
        
        threading.Thread(target=listen, daemon=True).start()
    
    def speak(self, text):
        """Convert text to speech"""
        if not self.tts_engine:
            return
            
        def _speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
        
        threading.Thread(target=_speak, daemon=True).start()
    
    def process_message(self, message):
        """Enhanced message processing with identity awareness"""
        try:
            # Use unified FAME system
            from fame_unified import get_fame
            
            fame = get_fame()
            response = fame.process_text(message, source='gui')
            
            # Extract response text
            if isinstance(response, dict):
                response_text = response.get('response', 'I didn\'t understand that.')
                
                # Add comprehensive metadata (confidence, sources, intent)
                metadata_parts = []
                
                # Confidence (always show as percentage)
                if 'confidence' in response:
                    conf = response['confidence']
                    conf_pct = f"{conf*100:.1f}%"
                    metadata_parts.append(f"Confidence: {conf_pct}")
                
                # Sources/resources used
                sources_display = []
                if 'sources' in response:
                    sources_display.extend(response['sources'])
                elif 'source' in response:
                    sources_display.append(response['source'])
                
                # Also check routing for modules
                routing = response.get('routing', {})
                if 'selected_modules' in routing:
                    for mod in routing['selected_modules']:
                        if mod not in sources_display:
                            sources_display.append(mod)
                
                # Knowledge base attribution
                if 'knowledge_base_match' in response:
                    kb_match = response['knowledge_base_match']
                    kb_source = f"KB: {kb_match.get('book', 'N/A')}"
                    sources_display.append(kb_source)
                
                if sources_display:
                    sources_str = ", ".join(sources_display[:5])  # Limit to 5 sources
                    metadata_parts.append(f"Sources: {sources_str}")
                
                # Intent
                if 'intent' in response:
                    metadata_parts.append(f"Intent: {response['intent']}")
                
                if metadata_parts:
                    response_text += f"\n\n[{' | '.join(metadata_parts)}]"
                
                return response_text
            else:
                return str(response)
        
        except ImportError:
            # Fallback to old system if unified not available
            logging.warning("Unified FAME system not available, using fallback")
            return self._process_message_fallback(message)
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return f"I encountered an error: {str(e)}. Please try again."
    
    def _process_message_fallback(self, message):
        """Fallback message processing"""
        message_lower = message.lower()
        
        # Check for question-related commands
        try:
            from fame_question_handler import FAMEQuestionHandler
            handler = FAMEQuestionHandler(workspace_path=Path(__file__).parent)
            question_response = handler.process_question_command(message)
            if question_response:
                return question_response
        except ImportError:
            pass
        except Exception as e:
            logging.debug(f"Question handler error: {e}")
        
        # Fallback responses
        responses = {
            "hello": "Hello! I am F.A.M.E 6.0, your living AI system. How can I assist you today?",
            "hi": "Hello! I am F.A.M.E 6.0, your living AI system. How can I assist you today?",
            "how are you": "I am functioning optimally. My vital signs show high cognitive activity and adaptation rates.",
            "what can you do": "I can analyze markets, provide insights, learn from interactions, and adapt to your needs through continuous training."
        }
        
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        return "I understand your message. As a living system, I'm continuously learning from our interactions. Could you elaborate?"
    
    def start_training(self):
        """Start model training"""
        self.training_status.config(text="Training: Running", fg="green")
        self.add_to_chat("🧠 Starting model training session...")
        
        # This would start actual training
        threading.Thread(target=self.run_training, daemon=True).start()
    
    def run_training(self):
        """Run the training process"""
        try:
            # Simulate training progress
            for i in range(10):
                if not self.system_running:
                    break
                time.sleep(2)
                progress = (i + 1) * 10
                self.root.after(0, lambda p=progress: self.add_to_chat(f"📊 Training progress: {p}%"))
            
            if self.system_running:
                self.root.after(0, lambda: self.training_status.config(text="Training: Completed", fg="blue"))
                self.root.after(0, lambda: self.add_to_chat("✅ Training completed successfully!"))
                
        except Exception as e:
            self.root.after(0, lambda: self.training_status.config(text="Training: Failed", fg="red"))
            self.root.after(0, lambda: self.add_to_chat(f"❌ Training failed: {str(e)}"))
    
    def view_training_progress(self):
        """View training progress"""
        messagebox.showinfo("Training Progress", "Training visualization would open here with graphs and metrics.")
    
    def update_models(self):
        """Update AI models"""
        self.add_to_chat("🔄 Updating AI models from LocalAI...")
        # This would trigger model updates
    
    def add_to_chat(self, message):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n{message}")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def update_ui_state(self):
        """Update UI based on system state"""
        if self.system_running:
            self.start_btn.config(state=tk.DISABLED, bg="#555555")
            self.stop_btn.config(state=tk.NORMAL, bg="#aa0000")
        else:
            self.start_btn.config(state=tk.NORMAL, bg="#00aa00")
            self.stop_btn.config(state=tk.DISABLED, bg="#555555")
        
        if self.voice_enabled:
            self.voice_btn.config(text="🔇 Disable Voice", bg="#aa0055")
        else:
            self.voice_btn.config(text="🎤 Enable Voice", bg="#0055aa")

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = FAMEDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

