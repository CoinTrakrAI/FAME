#!/usr/bin/env python3
"""
FAME Desktop - Main Window
Modern PyQt5 desktop application with voice interface
"""

import sys
import os
import asyncio
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel, QStatusBar, QMenuBar,
        QMenu, QAction, QSystemTrayIcon, QMessageBox, QSplitter, QFrame
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt5.QtGui import QIcon, QFont, QTextCursor, QColor, QPalette
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    # Fallback to Tkinter
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox
        TKINTER_AVAILABLE = True
    except ImportError:
        TKINTER_AVAILABLE = False

logger = logging.getLogger(__name__)


class VoiceThread(QThread if PYQT5_AVAILABLE else threading.Thread):
    """Thread for voice input/output"""
    
    if PYQT5_AVAILABLE:
        voice_input_received = pyqtSignal(str)
        voice_output_started = pyqtSignal()
        voice_output_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        if PYQT5_AVAILABLE:
            super().__init__(parent)
        else:
            threading.Thread.__init__(self)
        self.listening = False
        self.speaking = False
        self.daemon = True
    
    def run(self):
        """Voice input loop"""
        # This would integrate with speech-to-text
        pass
    
    def speak(self, text: str):
        """Text-to-speech"""
        if PYQT5_AVAILABLE:
            self.voice_output_started.emit()
        # This would integrate with text-to-speech
        if PYQT5_AVAILABLE:
            self.voice_output_finished.emit()


if PYQT5_AVAILABLE:
    class FAMEDesktopMainWindow(QMainWindow):
        """Main window for FAME Desktop application"""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("FAME - Financial AI Market Engine")
            self.setGeometry(100, 100, 1200, 800)
            
            # Initialize FAME backend
            self.fame_backend = None
            self._init_backend()
            
            # Voice thread
            self.voice_thread = VoiceThread(self)
            if hasattr(self.voice_thread, 'voice_input_received'):
                self.voice_thread.voice_input_received.connect(self.on_voice_input)
            
            # UI Setup
            self._setup_ui()
            self._setup_menu()
            self._setup_status_bar()
            
            # Status timer
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(5000)  # Update every 5 seconds
            
            # Initial status check
            self.update_status()
        
        def _init_backend(self):
            """Initialize FAME backend"""
            try:
                from core.assistant.assistant_api import handle_text_input
                self.fame_backend = handle_text_input
                logger.info("FAME backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FAME backend: {e}")
                QMessageBox.warning(
                    self,
                    "Initialization Error",
                    f"Failed to initialize FAME backend:\n{str(e)}\n\nSome features may not work."
                )
        
        def _setup_ui(self):
            """Setup main UI"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            main_layout = QVBoxLayout(central_widget)
            
            # Title
            title = QLabel("💰 FAME - Financial AI Market Engine")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title.setFont(title_font)
            title.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title)
            
            # Chat area
            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setFont(QFont("Consolas", 10))
            self.chat_display.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #3e3e3e;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            main_layout.addWidget(self.chat_display)
            
            # Input area
            input_layout = QHBoxLayout()
            
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("Ask FAME about stocks, crypto, trading strategies...")
            self.input_field.returnPressed.connect(self.send_message)
            input_layout.addWidget(self.input_field)
            
            # Send button
            self.send_button = QPushButton("Send")
            self.send_button.clicked.connect(self.send_message)
            self.send_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
            input_layout.addWidget(self.send_button)
            
            # Voice button
            self.voice_button = QPushButton("🎤")
            self.voice_button.setToolTip("Voice Input (Hold to speak)")
            self.voice_button.setCheckable(True)
            self.voice_button.pressed.connect(self.start_voice_input)
            self.voice_button.released.connect(self.stop_voice_input)
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:checked {
                    background-color: #dc3545;
                }
            """)
            input_layout.addWidget(self.voice_button)
            
            main_layout.addLayout(input_layout)
            
            # Welcome message
            self.add_to_chat("FAME", "💰 Welcome to FAME - Financial AI Market Engine!\n\n"
                                    "I'm your finance-first AI assistant. I can help you with:\n"
                                    "• Stock prices and analysis (AAPL, TSLA, etc.)\n"
                                    "• Cryptocurrency data (BTC, ETH, XRP, etc.)\n"
                                    "• Trading strategies (day trading, swing trading, etc.)\n"
                                    "• Market analysis and predictions\n"
                                    "• Commodities, ETFs, NFTs, and more\n\n"
                                    "Try asking: 'What's the price of Bitcoin?' or 'Analyze AAPL'")
        
        def _setup_menu(self):
            """Setup menu bar"""
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu('File')
            
            settings_action = QAction('Settings', self)
            settings_action.setShortcut('Ctrl+,')
            settings_action.triggered.connect(self.show_settings)
            file_menu.addAction(settings_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction('Exit', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Tools menu
            tools_menu = menubar.addMenu('Tools')
            
            localai_action = QAction('LocalAI Status', self)
            localai_action.triggered.connect(self.show_localai_status)
            tools_menu.addAction(localai_action)
            
            # Help menu
            help_menu = menubar.addMenu('Help')
            
            about_action = QAction('About', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        
        def _setup_status_bar(self):
            """Setup status bar"""
            self.status_bar = self.statusBar()
            self.status_label = QLabel("Ready")
            self.status_bar.addWidget(self.status_label)
            
            # LocalAI status indicator
            self.localai_status = QLabel("LocalAI: Checking...")
            self.status_bar.addPermanentWidget(self.localai_status)
        
        def add_to_chat(self, sender: str, message: str):
            """Add message to chat display"""
            if sender == "FAME":
                self.chat_display.setTextColor(QColor("#4ec9b0"))
            else:
                self.chat_display.setTextColor(QColor("#d4d4d4"))
            
            self.chat_display.append(f"<b>{sender}:</b> {message}")
            self.chat_display.moveCursor(QTextCursor.End)
        
        def send_message(self):
            """Send message to FAME"""
            text = self.input_field.text().strip()
            if not text:
                return
            
            # Add user message to chat
            self.add_to_chat("You", text)
            self.input_field.clear()
            
            # Disable input while processing
            self.input_field.setEnabled(False)
            self.send_button.setEnabled(False)
            self.status_label.setText("Processing...")
            
            # Process in background thread
            thread = threading.Thread(target=self._process_message, args=(text,))
            thread.daemon = True
            thread.start()
        
        def _process_message(self, text: str):
            """Process message in background thread"""
            try:
                if self.fame_backend:
                    response = self.fame_backend(text)
                    reply = response.get('reply', 'I apologize, but I encountered an error.')
                else:
                    reply = "FAME backend is not initialized. Please check the logs."
                
                # Update UI in main thread
                if PYQT5_AVAILABLE:
                    self.chat_display.append(f"<b>FAME:</b> {reply}")
                    self.chat_display.moveCursor(QTextCursor.End)
                else:
                    # Would use tkinter update
                    pass
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_msg = f"Error: {str(e)}"
                if PYQT5_AVAILABLE:
                    self.chat_display.append(f"<b>Error:</b> {error_msg}")
                    self.chat_display.moveCursor(QTextCursor.End)
            finally:
                # Re-enable input
                if PYQT5_AVAILABLE:
                    self.input_field.setEnabled(True)
                    self.send_button.setEnabled(True)
                    self.status_label.setText("Ready")
        
        def start_voice_input(self):
            """Start voice input"""
            self.voice_button.setChecked(True)
            self.status_label.setText("Listening...")
            # Start voice thread
            if not self.voice_thread.isRunning():
                self.voice_thread.listening = True
                self.voice_thread.start()
        
        def stop_voice_input(self):
            """Stop voice input"""
            self.voice_button.setChecked(False)
            self.voice_thread.listening = False
            self.status_label.setText("Ready")
        
        def on_voice_input(self, text: str):
            """Handle voice input received"""
            self.input_field.setText(text)
            self.send_message()
        
        def update_status(self):
            """Update status bar"""
            try:
                from core.localai_manager import get_localai_manager
                manager = get_localai_manager()
                status = manager.get_status()
                
                if status['api_healthy']:
                    self.localai_status.setText("LocalAI: ✅ Online")
                    self.localai_status.setStyleSheet("color: green;")
                elif status['container_running']:
                    self.localai_status.setText("LocalAI: ⚠️ Starting...")
                    self.localai_status.setStyleSheet("color: orange;")
                else:
                    self.localai_status.setText("LocalAI: ❌ Offline")
                    self.localai_status.setStyleSheet("color: red;")
            except Exception as e:
                logger.debug(f"Status update error: {e}")
                self.localai_status.setText("LocalAI: Unknown")
        
        def show_settings(self):
            """Show settings dialog"""
            QMessageBox.information(
                self,
                "Settings",
                "Settings dialog will be implemented here.\n\n"
                "Configure:\n"
                "- API Keys\n"
                "- LocalAI Endpoint\n"
                "- Voice Settings\n"
                "- Theme"
            )
        
        def show_localai_status(self):
            """Show LocalAI status dialog"""
            try:
                from core.localai_manager import get_localai_manager
                manager = get_localai_manager()
                status = manager.get_status()
                
                message = f"""
LocalAI Status:

Docker Available: {'Yes' if status['docker_available'] else 'No'}
Docker Running: {'Yes' if status['docker_running'] else 'No'}
Container Running: {'Yes' if status['container_running'] else 'No'}
API Healthy: {'Yes' if status['api_healthy'] else 'No'}
Endpoint: {status['endpoint']}

{status['message']}
                """
                
                QMessageBox.information(self, "LocalAI Status", message.strip())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not get LocalAI status: {str(e)}")
        
        def show_about(self):
            """Show about dialog"""
            QMessageBox.about(
                self,
                "About FAME",
                """
                <h2>FAME - Financial AI Market Engine</h2>
                <p>Version 6.0 - Living System</p>
                <p>Finance-first AI assistant for trading and market analysis.</p>
                <p><b>Features:</b></p>
                <ul>
                    <li>Real-time stock and crypto prices</li>
                    <li>Comprehensive market analysis</li>
                    <li>Trading strategy guidance</li>
                    <li>Voice interface</li>
                    <li>Local AI inference (LocalAI)</li>
                    <li>Self-learning and adaptive system</li>
                </ul>
                """
            )
        
        def closeEvent(self, event):
            """Handle window close event"""
            reply = QMessageBox.question(
                self,
                'Exit FAME',
                'Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


else:
    # Tkinter fallback
    class FAMEDesktopMainWindow:
        """Tkinter version of main window"""
        
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("FAME - Financial AI Market Engine")
            self.root.geometry("1200x800")
            
            # Initialize backend
            self.fame_backend = None
            self._init_backend()
            
            self._setup_ui()
        
        def _init_backend(self):
            try:
                from core.assistant.assistant_api import handle_text_input
                self.fame_backend = handle_text_input
            except Exception as e:
                logger.error(f"Backend init error: {e}")
        
        def _setup_ui(self):
            # Title
            title = tk.Label(
                self.root,
                text="💰 FAME - Financial AI Market Engine",
                font=("Arial", 16, "bold")
            )
            title.pack(pady=10)
            
            # Chat display
            self.chat_display = scrolledtext.ScrolledText(
                self.root,
                wrap=tk.WORD,
                font=("Consolas", 10),
                bg="#1e1e1e",
                fg="#d4d4d4",
                insertbackground="#d4d4d4"
            )
            self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Input frame
            input_frame = tk.Frame(self.root)
            input_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.input_field = tk.Entry(input_frame, font=("Arial", 11))
            self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.input_field.bind("<Return>", lambda e: self.send_message())
            
            self.send_button = tk.Button(
                input_frame,
                text="Send",
                command=self.send_message,
                bg="#0078d4",
                fg="white",
                font=("Arial", 10, "bold")
            )
            self.send_button.pack(side=tk.LEFT, padx=5)
            
            self.voice_button = tk.Button(
                input_frame,
                text="🎤",
                command=self.toggle_voice,
                bg="#28a745",
                fg="white",
                font=("Arial", 12)
            )
            self.voice_button.pack(side=tk.LEFT, padx=5)
            
            # Welcome message
            self.add_to_chat("FAME", "💰 Welcome to FAME!\n\nI'm your finance-first AI assistant.")
        
        def add_to_chat(self, sender: str, message: str):
            self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
            self.chat_display.see(tk.END)
        
        def send_message(self):
            text = self.input_field.get().strip()
            if not text:
                return
            
            self.add_to_chat("You", text)
            self.input_field.delete(0, tk.END)
            
            # Process message
            if self.fame_backend:
                try:
                    response = self.fame_backend(text)
                    reply = response.get('reply', 'Error processing message.')
                    self.add_to_chat("FAME", reply)
                except Exception as e:
                    self.add_to_chat("Error", str(e))
        
        def toggle_voice(self):
            messagebox.showinfo("Voice", "Voice interface will be implemented here")
        
        def run(self):
            self.root.mainloop()


def main():
    """Main entry point for desktop application"""
    if PYQT5_AVAILABLE:
        app = QApplication(sys.argv)
        app.setApplicationName("FAME Desktop")
        
        window = FAMEDesktopMainWindow()
        window.show()
        
        sys.exit(app.exec_())
    elif TKINTER_AVAILABLE:
        window = FAMEDesktopMainWindow()
        window.run()
    else:
        print("ERROR: Neither PyQt5 nor Tkinter is available!")
        print("Please install PyQt5: pip install PyQt5")
        print("Or use Tkinter (usually comes with Python)")
        sys.exit(1)


if __name__ == "__main__":
    main()

