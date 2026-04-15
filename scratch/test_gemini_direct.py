from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents="Say Hello"
    )
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
