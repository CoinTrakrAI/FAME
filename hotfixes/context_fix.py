#!/usr/bin/env python3
"""
Emergency context fix for production system
Immediate fix for context confusion issues
"""

import re
from typing import Optional, Tuple, List
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmergencyContextFix:
    """Immediate fix for context confusion issues"""
    
    def __init__(self, max_context: int = 5):
        self.last_user_query = None
        self.last_ai_response = None
        self.conversation_stack = deque(maxlen=max_context)
        self.logger = logging.getLogger(__name__)
        
    def track_conversation(self, user_input: str, ai_response: str):
        """Track conversation for context"""
        self.last_user_query = user_input
        self.last_ai_response = ai_response
        self.conversation_stack.append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': datetime.now()
        })
    
    def is_affirmative_response(self, user_input: str) -> bool:
        """Check if user input is an affirmative response"""
        affirmative_patterns = [
            r'^yes$', r'^yeah$', r'^yep$', r'^sure$', r'^ok$', r'^okay$',
            r'^please do$', r'^go ahead$', r'^absolutely$', r'^definitely$',
            r'^certainly$', r'^of course$'
        ]
        
        user_clean = user_input.lower().strip()
        
        for pattern in affirmative_patterns:
            if re.match(pattern, user_clean):
                return True
        return False
    
    def get_expected_action(self) -> Optional[str]:
        """Determine what action user expects based on last AI response"""
        if not self.last_ai_response:
            return None
            
        ai_lower = self.last_ai_response.lower()
        
        if any(keyword in ai_lower for keyword in ['executable', 'pyinstaller', 'build script', '.exe', 'build', 'create a build']):
            return 'provide_build_instructions'
        elif any(keyword in ai_lower for keyword in ['code', 'program', 'script', 'function', 'write', 'create']):
            return 'provide_code'
        elif any(keyword in ai_lower for keyword in ['help', 'assist', 'guide']):
            return 'provide_help'
            
        return None
    
    def generate_contextual_response(self, user_input: str) -> Optional[str]:
        """Generate contextual response for affirmative follow-ups"""
        if not self.is_affirmative_response(user_input):
            return None
            
        expected_action = self.get_expected_action()
        
        if expected_action == 'provide_build_instructions':
            return self._get_build_instructions()
        elif expected_action == 'provide_code':
            return self._get_wifi_scanner_code()
        elif expected_action == 'provide_help':
            return "I'd be happy to help! What specific aspect would you like assistance with?"
            
        return None
    
    def _get_build_instructions(self) -> str:
        """Provide build instructions"""
        return """**Complete Build Instructions:**

1. **Save your Python code** as `wifi_scanner.py`

2. **Install PyInstaller**:
```bash
pip install pyinstaller
```

3. **Build executable**:
```bash
pyinstaller --onefile --name="WiFiScanner" wifi_scanner.py
```

4. **Find your .exe** in the `dist/` folder

**Advanced options:**
- Add icon: `--icon=icon.ico`
- Hide console: `--windowed`
- Optimize: `--optimize=2`

Your executable will be ready to use! 🚀"""
    
    def _get_wifi_scanner_code(self) -> str:
        """Provide WiFi scanner code"""
        return """```python
# WiFi Network Scanner - Educational Use Only
import subprocess
import re

def scan_wifi_networks():
    \"\"\"Scan available WiFi networks on Windows\"\"\"
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"], 
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("Available WiFi Networks:")
            profiles = re.findall(r"Profile\\s*:\\s*(.*)", result.stdout)
            for profile in profiles:
                profile = profile.strip()
                if profile:
                    print(f"📶 {profile}")
        else:
            print("Error: Run as Administrator")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_wifi_networks()
```

**Note:** This shows saved network profiles only. Password retrieval requires additional permissions and should only be used on networks you own."""


# Global instance for immediate use
context_fix = EmergencyContextFix()

