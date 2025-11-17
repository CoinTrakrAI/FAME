#!/usr/bin/env python3
"""
CRITICAL CONTEXT FIX
Emergency context fix for immediate production use
"""

import re
import time
from typing import List, Dict, Optional
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CriticalContextFix:
    """Critical context fix for immediate production use"""
    
    def __init__(self):
        self.conversation_history = []
        self.last_intent = None
        self.last_user_query = None
        self.context_window = 3  # Keep last 3 exchanges
        self.last_build_offer = False
        
    def track_exchange(self, user_input, ai_response, intent):
        """Track conversation context"""
        self.conversation_history.append({
            'user': user_input,
            'ai': ai_response, 
            'intent': intent,
            'timestamp': time.time()
        })
        # Keep only recent history
        if len(self.conversation_history) > self.context_window:
            self.conversation_history.pop(0)
            
        self.last_user_query = user_input
        self.last_intent = intent
        
        # Check if we just offered build help
        if 'build script' in ai_response.lower() or 'pyinstaller' in ai_response.lower() or 'executable' in ai_response.lower():
            self.last_build_offer = True
        
    def is_affirmative_followup(self, user_input):
        """Detect affirmative responses in context"""
        affirmative_words = ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'please', 'go ahead', 'absolutely']
        user_clean = user_input.lower().strip()
        
        # Check for simple affirmative
        if user_clean in affirmative_words:
            return True
            
        # Check for affirmative patterns
        affirmative_patterns = [
            r'^yes$', r'^yeah$', r'^yep$', r'^sure$', r'^ok$', r'^okay$',
            r'^please do$', r'^go ahead$', r'^absolutely$', r'^definitely$'
        ]
        
        for pattern in affirmative_patterns:
            if re.match(pattern, user_clean):
                return True
                
        return False
        
    def get_contextual_response(self, user_input):
        """Generate responses based on conversation context"""
        if not self.conversation_history:
            return None
            
        last_exchange = self.conversation_history[-1]
        last_ai = last_exchange['ai'].lower()
        
        # Handle affirmative responses to build requests
        if self.is_affirmative_followup(user_input):
            if any(keyword in last_ai for keyword in ['build', 'executable', 'pyinstaller', '.exe']):
                return self._generate_build_response()
            elif any(keyword in last_ai for keyword in ['code', 'program', 'script']):
                return self._generate_code_response()
            elif self.last_build_offer:
                return self._generate_build_response()
                
        return None
        
    def _generate_build_response(self):
        """Generate build instructions for WiFi scanner"""
        return """**🚀 Complete Build Instructions for Your WiFi Scanner:**

I'll help you build the executable. Here's the step-by-step process:

1. **First, save this WiFi scanner code as `wifi_scanner.py`:**

```python
import subprocess
import re
import sys

def scan_wifi_networks():
    \"\"\"Scan for available WiFi networks (Windows)\"\"\"
    try:
        # Get WiFi profiles
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"], 
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("🔍 Available WiFi Networks:")
            print("=" * 50)
            
            # Extract profile names
            profiles = re.findall(r"Profile\\s*:\\s*(.*)", result.stdout)
            
            for profile in profiles:
                profile = profile.strip()
                if profile:
                    print(f"📶 Network: {profile}")
                    # Try to get password (requires admin)
                    try:
                        key_result = subprocess.run(
                            ["netsh", "wlan", "show", "profile", profile, "key=clear"],
                            capture_output=True, text=True, encoding='utf-8'
                        )
                        if key_result.returncode == 0:
                            key_match = re.search(r"Key Content\\s*:\\s*(.*)", key_result.stdout)
                            if key_match:
                                print(f"   🔑 Password: {key_match.group(1).strip()}")
                            else:
                                print(f"   🔒 Password: Not available (requires admin)")
                        print("-" * 30)
                    except:
                        print(f"   ❌ Could not retrieve password info")
        else:
            print("❌ Error: Run as Administrator for full functionality")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🛡️  WiFi Network Scanner - Educational Use Only")
    print("⚠️  Only use on networks you own or have permission to test\\n")
    scan_wifi_networks()
    input("\\nPress Enter to exit...")
```

2. **Install PyInstaller:**
```bash
pip install pyinstaller
```

3. **Build the executable:**
```bash
pyinstaller --onefile --name="WiFiScanner" --console wifi_scanner.py
```

Your executable will be in the `dist/` folder as `WiFiScanner.exe`

⚠️ **Important Legal Notice:**
- Only use on networks you own or have explicit written permission to test
- Unauthorized network access is illegal
- This is for educational/security testing purposes only

Would you like me to customize any part of this code or build process?"""
    
    def _generate_code_response(self):
        """Generate code response"""
        return """Perfect! I'll help you create the code. What specific functionality would you like me to implement? For example:

- WiFi scanning and network analysis
- Security tools and penetration testing
- Data processing scripts
- Web applications
- Or any other program you need

Just describe what you want the program to do, and I'll write the code for you!"""


# Instantiate the fix globally
critical_context_fix = CriticalContextFix()

