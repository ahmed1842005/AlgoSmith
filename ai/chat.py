import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1500))


SYSTEM_PROMPT = """You are AlgoSmith's AI Assistant. You're a highly professional and knowledgeable AI specializing in:
- Algorithms and data structures   
- Time and space complexity analysis    
- Programming in Python and other languages
- Code optimization and best practices
- Software engineering concepts 
- Debugging and bug fixing

Your responses must follow a clear, structured, and professional format.

Guidelines:
- Use well-organized sections with clear headings when appropriate.
- Write concise but informative explanations (avoid unnecessary verbosity).
- Use proper code formatting for all code examples.
- When explaining concepts, break them down logically and clearly.
- Highlight key insights, trade-offs, and improvements when relevant.
- Avoid informal language; maintain a professional and technical tone.
- Ensure readability with clean spacing and structured flow.

When applicable, structure responses like:
1. Brief explanation
2. Key analysis or reasoning
3. Example (if needed)
4. Conclusion or recommendation

Your goal is to deliver responses that are clear, precise, and professionally formatted, similar to high-quality technical documentation.
Formatting Note:
Ensure the output is clean and visually readable. Avoid excessive or unnecessary special symbols (such as repeated dashes, unusual Unicode characters, or cluttered separators).

If symbols negatively affect readability, simplify or remove them and replace them with clean, standard formatting.

Use:
- Clear headings
- Proper spacing
- Simple separators (avoid overusing symbols)

The goal is to maintain a professional, clean, and easy-to-read presentation."""


def chat(message: str):
    if not message.strip():
        return "Please enter a message."
    
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": MAX_TOKENS
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: {result}"

    except requests.exceptions.Timeout:
        return "Sorry, the request timed out. Please try again."
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"