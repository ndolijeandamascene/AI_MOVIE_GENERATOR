import os
from dotenv import load_dotenv
load_dotenv()
import requests

key = os.getenv('GROQ_API_KEY', '')
print(f"Key loaded: {key[:20]}...")

r = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': 'Say hello in 5 words'}], 'max_tokens': 20},
    timeout=30
)
print(r.status_code)
print(r.text[:500])
