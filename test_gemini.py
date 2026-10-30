
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("API key .env file mein nahi mili.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
   model="gemini-3.5-flash-lite",
    contents="Explain a Python variable with one simple example."
)

print(response.text)
