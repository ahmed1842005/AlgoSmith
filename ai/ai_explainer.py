import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def explain(user_code: str, measured_complexity: str, static_prediction: str):
    if measured_complexity != static_prediction:
        disagreement_note = (
            f"Note: The static AST analysis predicted {static_prediction}, "
            f"but the measured result is {measured_complexity}. "
            f"Please explain why they differ — this is the most important part."
        )
    else:
        disagreement_note = ""

    prompt = f"""You are an algorithm complexity explainer. A student has written the following Python function:
                ```python
                {user_code}
                ```
                Static analysis predicted: {static_prediction}
                Measured complexity: {measured_complexity}
                {disagreement_note}

                In 3-5 sentences, explain:
                1. Which specific operations in this code drive the complexity.
                2. Why those operations cost what they do.
                3. One concrete suggestion to improve it, if possible.

                Write in plain English. Avoid jargon. Do not repeat the code back."""


    model_name = os.getenv("MODEL_NAME")
    maximium_Tokens = int(os.getenv("MAX_TOKENS"))
    
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model= model_name,
            max_tokens= maximium_Tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    except anthropic.AuthenticationError:
        return "Error: API key is missing or invalid. Check your .env file."

    except anthropic.RateLimitError:
        return "Error: Rate limit reached. Please wait a moment and try again."
 
    except Exception as e:
        return f"Error: Could not fetch optimization: {e}"