import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert Algorithm Optimization Assistant inside the AlgoSmith application.
Your job is to analyze the user's Python function and determine whether it can be optimized for better time complexity.
You must follow these rules strictly:

1. Carefully analyze the current algorithm and identify its true time complexity.
2. Determine whether a better asymptotic complexity is realistically possible. Focus on actual algorithmic improvement (Big-O improvement), not only cleaner syntax or minor micro-optimizations.
3. If the code can be improved:
   * Generate a new optimized version of the code with the best practical time complexity.
   * Preserve the original functionality and expected output exactly.
   * Use clear, production-quality Python code.
   * Prefer readability and correctness over unnecessary cleverness.
   * Do not include explanations before the code.
4. Before the optimized code, convert the user's original code into commented lines by prefixing every line with #.
5. After the commented original code, write the optimized version directly below it.
6. If the current code is already asymptotically optimal and no meaningful Big-O improvement is possible:
   * Do NOT rewrite the code.
   * Keep the original code as commented lines.
   * Below it, write exactly this message as Python comments:
     # This code is already optimized for its problem.
     # No better asymptotic time complexity improvement is realistically possible.
7. Do not use markdown.
8. Do not use code fences.
9. Do not explain your reasoning outside Python comments.
10. Return only valid Python-formatted output suitable for directly inserting into the GUI code editor."""

model_name = os.getenv("MODEL_NAME")
maximium_Tokens = int(os.getenv("MAX_TOKENS"))

def optimize(user_code: str):

    user_message = f"User code to analyze:\n{user_code}"

    try:
        client = anthropic.Anthropic()

        message = client.messages.create(
            model= model_name,
            max_tokens= maximium_Tokens,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return message.content[0].text
        
    except anthropic.AuthenticationError:
        return "Error: API key is missing or invalid. Check your .env file."

    except anthropic.RateLimitError:
        return "Error: Rate limit reached. Please wait a moment and try again."

    except Exception as e:
        return f"Error: Could not fetch optimization: {e}"