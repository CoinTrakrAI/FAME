#!/usr/bin/env python3
"""
Load API keys from local configuration file
Run this before starting FAME to load all API keys
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def load_api_keys():
    """Load API keys from local file"""
    local_keys_file = Path("config/api_keys_local.env")
    
    if local_keys_file.exists():
        load_dotenv(local_keys_file)
        print("✅ API keys loaded from config/api_keys_local.env")
    else:
        # Try .env file
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            print("✅ API keys loaded from .env")
        else:
            print("⚠️ No API keys file found. Using environment variables only.")
    
    # Verify key API keys are loaded
    keys_to_check = {
        "GOOGLE_AI_KEY": os.getenv("GOOGLE_AI_KEY"),
        "SERPAPI_KEY": os.getenv("SERPAPI_KEY"),
        "ALPHA_VANTAGE_API_KEY": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "COINGECKO_API_KEY": os.getenv("COINGECKO_API_KEY"),
        "FINNHUB_API_KEY": os.getenv("FINNHUB_API_KEY"),
        "GITHUB_API_KEY": os.getenv("GITHUB_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY")
    }
    
    loaded = sum(1 for v in keys_to_check.values() if v and not v.startswith("your_"))
    print(f"✅ {loaded}/{len(keys_to_check)} API keys loaded")
    
    return keys_to_check

if __name__ == "__main__":
    load_api_keys()

