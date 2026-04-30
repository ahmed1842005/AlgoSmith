import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("MODEL_NAME")
maximum_tokens = int(os.getenv("MAX_TOKENS"))


def explain(user_code: str, measured_complexity: str, static_prediction: str):

    if measured_complexity != static_prediction:
        disagreement_note = (
            f"Static analysis predicted {static_prediction}, but measured result is {measured_complexity}. "
            f"Explain why they differ."
        )
    else:
        disagreement_note = ""

    prompt = f"""You are an algorithm analysis assistant. Given this Python function:

{user_code}

Static analysis predicted: {static_prediction}
Measured complexity: {measured_complexity}
{disagreement_note}

Write two clearly labeled sections:

COMPLEXITY EXPLANATION
In 3-5 sentences: which operations drive the complexity, why they cost what they do, and one concrete suggestion to improve it.

OPTIMIZATION
If a better time complexity is possible: show the optimized code directly (no markdown, no code fences, just Python). If already optimal: write "This algorithm is already asymptotically optimal."
"""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert algorithm analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": maximum_tokens
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]

        return f"Error from API: {result}"

    except Exception as e:
        return f"Error: Could not fetch explanation: {e}"