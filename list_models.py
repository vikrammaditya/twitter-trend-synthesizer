import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY found in .env")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print("Fetching available models via REST API...")
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        models = data.get("models", [])
        print(f"Found {len(models)} models:")
        for m in models:
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                print(f"- {m.get('name')} (displayName: {m.get('displayName')})")
    else:
        print("Failed to fetch models:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
