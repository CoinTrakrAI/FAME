#!/usr/bin/env python3
"""Test FAME connection"""
import requests

try:
    r = requests.post(
        'http://3.17.56.74:8080/query',
        json={'text':'What is today date?','session_id':'test','source':'test'},
        timeout=5
    )
    print("SUCCESS:", r.status_code)
    print(r.json().get('response','')[:200])
except requests.exceptions.ConnectionError as e:
    print("NOT ACCESSIBLE: Connection refused - Container not running")
except Exception as e:
    print(f"ERROR: {e}")
