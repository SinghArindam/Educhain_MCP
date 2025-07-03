import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_response(prompt: str) -> str:
    """
    Get a response from the Gemini API for a given prompt.
    
    Args:
        prompt (str): The input prompt to send to the Gemini API.
    
    Returns:
        str: The response text from the Gemini API.
    """
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return response.text

contents="Explain how AI works in a few words"

response = get_gemini_response(contents)

print(response)
