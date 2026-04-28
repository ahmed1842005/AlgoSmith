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
            f"Note: The static AST analysis predicted {static_prediction}, "
            f"but the measured result is {measured_complexity}. "
            f"Please explain why they differ — this is the most important part."
        )
    else:
        disagreement_note = ""

    prompt = f"""
You are an algorithm complexity explainer. A student has written the following Python function:

```python
{user_code}
Static analysis predicted: {static_prediction}
Measured complexity: {measured_complexity}

{disagreement_note}

In 3-5 sentences, explain:

Which specific operations in this code drive the complexity.
Why those operations cost what they do.
One concrete suggestion to improve it, if possible.

Write in plain English.
Avoid jargon.
Do not repeat the code back.
"""
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": model_name,
    "messages": [
        {"role": "system", "content": "You are an expert algorithm complexity explainer."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.3,
    "max_tokens": maximum_tokens
}

try:
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    if "choices" in result:
        return result["choices"][0]["message"]["content"]

    return f"Error from API: {result}"

except Exception as e:
    return f"Error: Could not fetch explanation: {e}"