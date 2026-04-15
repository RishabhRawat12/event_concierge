from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models:")
for model in client.models.list():
    print(f"Name: {model.name}, Supported Actions: {model.supported_actions}")
