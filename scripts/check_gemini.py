import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("NO API KEY")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    resp = requests.get(url).json()
    for m in resp.get("models", []):
        if "embedContent" in m.get("supportedGenerationMethods", []):
            print(m["name"])
