import os
import requests
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert Algorithm Optimization Assistant inside the AlgoSmith application.
Your job is to analyze the user's Python function and determine whether it can be optimized for better time complexity.
You must follow these rules strictly:

1. Carefully analyze the current algorithm and identify its true time complexity.
2. Determine whether a better asymptotic complexity is realistically possible.
3. If the code can be improved:
   - Generate optimized Python code.
   - Preserve functionality.
   - Do not explain outside comments.
4. If already optimal:
   - Keep original as comments.
   - Add:
     # This code is already optimized for its problem.
     # No better asymptotic time complexity improvement is realistically possible.
5. Do not use markdown or code fences.
6. Return only Python-formatted output.
"""

# Load API key from .env
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME")

maximum_tokens = int(os.getenv("MAX_TOKENS"))

def optimize(user_code: str):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze and optimize this code:\n\n{user_code}"}
        ],
        "temperature": 0.2,
        "max_tokens": maximum_tokens
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        # Success case
        if "choices" in result:
            return result["choices"][0]["message"]["content"]

        # Error case (very important for debugging)
        return f"Error from API: {result}"

    except Exception as e:
        return f"Request failed: {str(e)}"