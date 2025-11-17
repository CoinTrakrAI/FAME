#!/usr/bin/env python3
"""
Enhanced Response Generator with Context
Response generator that maintains conversation context
"""

import logging
from typing import Dict, List, Optional, Any

from core.context_aware_router import ContextAwareIntentRouter

logger = logging.getLogger(__name__)


class EnhancedResponseGenerator:
    """Response generator that maintains conversation context"""
    
    def __init__(self, knowledge_base=None, learning_engine=None):
        self.kb = knowledge_base
        self.learner = learning_engine
        self.context_router = ContextAwareIntentRouter()
        self.conversation_context = []
        
    def generate_response(self, user_input: str, context: List[str] = None) -> Dict:
        """Generate response with enhanced context handling"""
        
        # First, check for affirmative follow-ups
        is_affirmative, affirmative_confidence, expected_type = self.context_router.is_affirmative_followup(user_input)
        
        if is_affirmative and affirmative_confidence > 0.7:
            if expected_type == 'build_instructions':
                response = self._generate_build_instructions_response()
                self.context_router.add_to_context(user_input, response['response'], response['intent'])
                return response
            elif expected_type == 'code_generation':
                response = self._generate_code_response()
                self.context_router.add_to_context(user_input, response['response'], response['intent'])
                return response
            elif expected_type == 'affirmative_response':
                response = {
                    'response': "Great! I'm ready to help. What would you like me to do?",
                    'intent': 'affirmative_followup',
                    'confidence': affirmative_confidence,
                    'sources': ['qa_engine'],
                    'should_search': False
                }
                self.context_router.add_to_context(user_input, response['response'], response['intent'])
                return response
        
        # Check for negative follow-ups
        is_negative, negative_confidence = self.context_router.is_negative_followup(user_input)
        if is_negative and negative_confidence > 0.7:
            response = {
                'response': "No problem. Is there anything else I can help you with?",
                'intent': 'negative_followup',
                'confidence': negative_confidence,
                'sources': ['qa_engine'],
                'should_search': False
            }
            self.context_router.add_to_context(user_input, response['response'], response['intent'])
            return response
        
        # Otherwise, return None to continue with normal processing
        return None
    
    def _generate_build_instructions_response(self) -> Dict:
        """Generate build instructions for the current context"""
        build_instructions = """**Complete Build Instructions for Your Program:**

1. **Save your Python code** as a `.py` file (e.g., `wifi_scanner.py`)

2. **Install PyInstaller**:
```bash
pip install pyinstaller
```

3. **Create the executable**:
```bash
pyinstaller --onefile --name="WiFiScanner" --console wifi_scanner.py
```

4. **Find your executable** in the `dist/` folder

**Additional Options:**
- Add an icon: `--icon=your_icon.ico`
- Hide console: `--windowed` (for GUI apps)
- Add data files: `--add-data="file.txt;."`
- Optimize: `--optimize=2`

**Example for WiFi Scanner:**
```bash
pyinstaller --onefile --name="WiFiScanner" --console wifi_scanner.py
```

Would you like me to:
- Generate a complete build script for you?
- Help you create the Python code first?
- Customize the build options for your specific needs?

Just let me know what you'd like to do next!"""
        
        return {
            'response': build_instructions,
            'intent': 'build_instructions',
            'confidence': 0.95,
            'sources': ['universal_developer', 'qa_engine'],
            'should_search': False
        }
    
    def _generate_code_response(self) -> Dict:
        """Generate code based on the current context"""
        wifi_scanner_code = """# WiFi Network Scanner - Educational Purpose Only
import subprocess
import re
import sys

def scan_wifi_networks():
    \"\"\"Scan for available WiFi networks (Windows)\"\"\"
    try:
        # Run netsh command to show WiFi profiles
        result = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("Available WiFi Networks:")
            print("=" * 40)
            
            # Extract profile names
            profiles = re.findall(r"Profile\\s*:\\s*(.*)", result.stdout)
            
            for profile in profiles:
                profile = profile.strip()
                if profile:
                    print(f"📶 {profile}")
                    
        else:
            print("Error: Could not scan WiFi networks")
            print("Make sure you're running as Administrator")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("WiFi Network Scanner - Educational Use Only")
    print("Note: This only shows saved network profiles, not passwords")
    scan_wifi_networks()"""
        
        return {
            'response': f"""Here's a WiFi network scanner for educational purposes:\n\n```python\n{wifi_scanner_code}\n```\n\n**Important Notes:**\n- This only shows saved network profiles, not passwords\n- Password retrieval requires administrative privileges and specific security contexts\n- Use only on networks you own or have explicit permission to test\n\nWould you like me to help you build this into an executable?""",
            'intent': 'code_generation',
            'confidence': 0.9,
            'sources': ['universal_developer', 'universal_hacker'],
            'should_search': False
        }


# Singleton instance
_enhanced_generator: Optional[EnhancedResponseGenerator] = None


def get_enhanced_generator() -> EnhancedResponseGenerator:
    """Get or create enhanced response generator instance"""
    global _enhanced_generator
    if _enhanced_generator is None:
        _enhanced_generator = EnhancedResponseGenerator()
    return _enhanced_generator

