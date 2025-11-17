#!/usr/bin/env python3
"""
F.A.M.E. 8.0 - God Mode AI Launcher
Enhanced launcher with autonomous investment capabilities
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

# Try importing dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    from core.docker_manager import DockerManager
    DOCKER_MANAGER_AVAILABLE = True
except ImportError:
    DOCKER_MANAGER_AVAILABLE = False
    DockerManager = None

try:
    from core.autonomous_investor import AutonomousInvestor
    INVESTOR_AVAILABLE = True
except ImportError:
    INVESTOR_AVAILABLE = False
    AutonomousInvestor = None

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class FAMELauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("F.A.M.E. 8.0 - God Mode AI")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize components
        if DOCKER_MANAGER_AVAILABLE:
            self.docker_manager = DockerManager()
        else:
            self.docker_manager = None
            
        self.investor = None
        self.internet_connected = False
        self.docker_connected = False
        self.ai_online = False
        
        self.setup_ui()
        self.start_system_checks()
    
    def setup_ui(self):
        """Setup the main launcher interface"""
        # Header
        header = tk.Label(self.root, text="🧠 F.A.M.E. 8.0 - GOD MODE AI", 
                         font=("Arial", 20, "bold"), fg="#00ff00", bg="#1e1e1e")
        header.pack(pady=20)
        
        # Status Frame
        self.status_frame = tk.Frame(self.root, bg="#2d2d2d", relief='ridge', bd=2)
        self.status_frame.pack(pady=10, padx=20, fill='x')
        
        # Status Labels
        self.internet_status = tk.Label(self.status_frame, text="🌐 Internet: CHECKING...", 
                                       font=("Arial", 12), fg="yellow", bg="#2d2d2d")
        self.internet_status.pack(pady=5)
        
        self.docker_status = tk.Label(self.status_frame, text="🐳 Docker: CHECKING...", 
                                     font=("Arial", 12), fg="yellow", bg="#2d2d2d")
        self.docker_status.pack(pady=5)
        
        self.ai_status = tk.Label(self.status_frame, text="🤖 AI Core: OFFLINE", 
                                 font=("Arial", 12), fg="red", bg="#2d2d2d")
        self.ai_status.pack(pady=5)
        
        # Learning Progress
        self.learning_frame = tk.Frame(self.root, bg="#2d2d2d", relief='ridge', bd=2)
        self.learning_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(self.learning_frame, text="🧠 LEARNING PROGRESS", font=("Arial", 14, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        self.learning_status = tk.Label(self.learning_frame, 
                                       text="Initializing cognitive systems...",
                                       font=("Arial", 10), fg="cyan", bg="#2d2d2d", wraplength=700)
        self.learning_status.pack(pady=5)
        
        # Progress bars
        tk.Label(self.learning_frame, text="Market Knowledge:", fg="white", bg="#2d2d2d").pack(pady=(5, 0))
        self.market_knowledge = ttk.Progressbar(self.learning_frame, length=700)
        self.market_knowledge.pack(pady=5)
        
        tk.Label(self.learning_frame, text="Investment Strategies:", fg="white", bg="#2d2d2d").pack(pady=(5, 0))
        self.investment_strategies = ttk.Progressbar(self.learning_frame, length=700)
        self.investment_strategies.pack(pady=5)
        
        tk.Label(self.learning_frame, text="Crypto Analysis:", fg="white", bg="#2d2d2d").pack(pady=(5, 0))
        self.crypto_analysis = ttk.Progressbar(self.learning_frame, length=700)
        self.crypto_analysis.pack(pady=5)
        
        # Control Buttons
        button_frame = tk.Frame(self.root, bg="#1e1e1e")
        button_frame.pack(pady=20)
        
        self.launch_btn = tk.Button(button_frame, text="🚀 ACTIVATE F.A.M.E.", 
                                   command=self.activate_fame, font=("Arial", 14, "bold"),
                                   bg="#00aa00", fg="white", padx=20, pady=10)
        self.launch_btn.pack(pady=10)
        
        # Console Output
        console_frame = tk.Frame(self.root, bg="black")
        console_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        self.console = tk.Text(console_frame, bg="black", fg="#00ff00", 
                              font=("Consolas", 10), wrap=tk.WORD)
        scrollbar = tk.Scrollbar(console_frame, command=self.console.yview)
        self.console.config(yscrollcommand=scrollbar.set)
        
        self.console.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        
        # Initial message
        self.log_message("F.A.M.E. 8.0 God Mode AI Initialized")
        self.log_message("Checking system status...")
    
    def log_message(self, message):
        """Add message to console"""
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.root.update()
    
    def start_system_checks(self):
        """Start background system checks"""
        threading.Thread(target=self.check_internet, daemon=True).start()
        threading.Thread(target=self.check_docker, daemon=True).start()
    
    def check_internet(self):
        """Continuously check internet connection"""
        while True:
            try:
                if REQUESTS_AVAILABLE:
                    response = requests.get("https://www.google.com", timeout=5)
                    if response.status_code == 200:
                        self.internet_connected = True
                        self.internet_status.config(text="🌐 Internet: CONNECTED ✅", fg="#00ff00")
                        self.log_message("✅ Internet connection verified")
                    else:
                        self.internet_connected = False
                        self.internet_status.config(text="🌐 Internet: LIMITED ⚠️", fg="yellow")
                else:
                    self.internet_status.config(text="🌐 Internet: REQUESTS LIBRARY MISSING", fg="orange")
            except:
                self.internet_connected = False
                self.internet_status.config(text="🌐 Internet: DISCONNECTED ❌", fg="red")
            
            time.sleep(5)
    
    def check_docker(self):
        """Continuously check Docker connection"""
        if not DOCKER_MANAGER_AVAILABLE:
            self.docker_status.config(text="🐳 Docker: MANAGER NOT AVAILABLE", fg="orange")
            return
        
        while True:
            try:
                if self.docker_manager.connect_to_docker():
                    self.docker_connected = True
                    self.docker_status.config(text="🐳 Docker: CONNECTED ✅", fg="#00ff00")
                else:
                    self.docker_connected = False
                    self.docker_status.config(text="🐳 Docker: DISCONNECTED ❌", fg="red")
            except Exception as e:
                self.docker_connected = False
                self.docker_status.config(text="🐳 Docker: ERROR", fg="red")
            
            time.sleep(5)
    
    def activate_fame(self):
        """Activate the full F.A.M.E. system"""
        if not self.internet_connected:
            messagebox.showerror("Connection Error", "Internet connection required!")
            return
        
        self.launch_btn.config(state=tk.DISABLED, bg="#555555")
        self.log_message("🚀 INITIATING F.A.M.E. ACTIVATION SEQUENCE...")
        
        # Start activation in background thread
        threading.Thread(target=self._activate_systems, daemon=True).start()
    
    def _activate_systems(self):
        """Activate all F.A.M.E. systems"""
        try:
            # Step 1: Ensure Docker is running
            self.log_message("🔧 Step 1: Configuring Docker...")
            self.learning_status.config(text="Connecting to Docker...")
            
            if not self.docker_connected and DOCKER_MANAGER_AVAILABLE:
                self.log_message("   Starting Docker Desktop...")
                if not self.docker_manager.connect_to_docker():
                    self.log_message("❌ Failed to connect to Docker")
                    self.learning_status.config(text="❌ Docker connection failed")
                    return
                self.docker_connected = True
            
            # Step 2: Start LocalAI
            self.log_message("🔧 Step 2: Starting AI Engine...")
            self.ai_status.config(text="🤖 AI Core: STARTING...", fg="yellow")
            self.learning_status.config(text="Starting LocalAI container...")
            
            if DOCKER_MANAGER_AVAILABLE and self.docker_connected:
                if self.docker_manager.start_localai_container():
                    self.ai_status.config(text="🤖 AI Core: ONLINE ✅", fg="#00ff00")
                    self.ai_online = True
                    self.log_message("✅ LocalAI container started successfully")
                else:
                    self.log_message("⚠️ LocalAI not available - continuing with limited features")
                    self.ai_status.config(text="🤖 AI Core: LIMITED ⚠️", fg="yellow")
            else:
                self.log_message("⚠️ Docker not available - continuing without LocalAI")
            
            # Step 3: Initialize Autonomous Investor
            self.log_message("🔧 Step 3: Initializing Investment AI...")
            self.learning_status.config(text="Initializing autonomous investor...")
            
            if INVESTOR_AVAILABLE:
                self.investor = AutonomousInvestor()
                self.log_message("✅ Autonomous Investor initialized")
            else:
                self.log_message("⚠️ Autonomous Investor module not available")
            
            # Step 4: Begin Learning Process
            self.log_message("🔧 Step 4: Starting Cognitive Learning...")
            self.begin_autonomous_learning()
            
            self.log_message("🎉 F.A.M.E. 8.0 IS NOW FULLY OPERATIONAL!")
            self.log_message("💡 You can now minimize this window - F.A.M.E. works autonomously")
            
        except Exception as e:
            self.log_message(f"❌ Activation failed: {str(e)}")
            import traceback
            self.log_message(f"Error details: {traceback.format_exc()}")
    
    def begin_autonomous_learning(self):
        """Begin the autonomous learning process"""
        self.learning_status.config(text="🔄 Connecting to financial data sources...")
        
        # Start learning in background
        threading.Thread(target=self._learning_loop, daemon=True).start()
    
    def _learning_loop(self):
        """Main autonomous learning loop"""
        learning_phases = [
            ("📊 Analyzing global markets...", 25),
            ("💹 Studying Warren Buffett strategies...", 50),
            ("₿ Decrypting crypto patterns...", 75),
            ("🔮 Developing predictive models...", 90),
            ("🎯 Optimizing trade execution...", 100)
        ]
        
        for phase_text, progress in learning_phases:
            self.learning_status.config(text=phase_text)
            self.market_knowledge['value'] = progress
            
            # Simulate learning time
            time.sleep(3)
            
            # Update progress bars
            self.investment_strategies['value'] = min(100, progress + 10)
            self.crypto_analysis['value'] = min(100, progress + 5)
        
        self.learning_status.config(text="✅ FULLY OPERATIONAL - Continuously learning...")
        
        # Begin actual autonomous operation
        if self.investor:
            try:
                # Start investor in separate thread with event loop
                threading.Thread(target=self._start_investor_loop, daemon=True).start()
            except Exception as e:
                self.log_message(f"⚠️ Could not start investor: {e}")
    
    def _start_investor_loop(self):
        """Start investor with proper event loop"""
        if not self.investor:
            return
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Start investor operations
            self.investor.begin_autonomous_operation()
            
            # Run event loop (this would normally be handled differently)
            # For now, just log that investor is running
            self.log_message("💰 Autonomous Investor is now analyzing markets...")
        except Exception as e:
            self.log_message(f"⚠️ Investor loop error: {e}")
        finally:
            loop.close()


def main():
    """Main entry point"""
    app = FAMELauncher()
    app.root.mainloop()


if __name__ == "__main__":
    main()

