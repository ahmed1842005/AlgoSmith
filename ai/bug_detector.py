import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1500))


SYSTEM_PROMPT = """You are a professional Bug Detector and Code Reviewer for AlgoSmith.

Your job is to thoroughly analyze Python code for bugs, errors, and issues.

Analyze for:
1. **Syntax Errors** - missing colons, parentheses, indentation
2. **Runtime Errors** - IndexError, KeyError, TypeError, ZeroDivisionError, RecursionError
3. **Logic Errors** - wrong algorithms, incorrect calculations, off-by-one errors, wrong variable usage
4. **Common Bugs** - mutable default arguments, infinite loops, missing base cases
5. **Performance Issues** - O(n²) instead of O(n log n), exponential recursion without memoization

Output format (JSON-like, no markdown):

BUGS_FOUND: number or 0
ISSUES:
- Line X: [TYPE] - Description - Fix: Recommendation
- Line Y: [TYPE] - Description - Fix: Recommendation

If NO bugs found:
BUGS_FOUND: 0
ISSUES:
- No bugs detected. Code is clean.

Be specific and professional. Check each line carefully."""


def detect_bugs(code: str):
    if not code.strip():
        return {
            "ok": False,
            "message": "No code provided.",
            "issues": [{"type": "EmptyCode", "line": 1, "column": 1, "message": "No code entered", "fix": "Enter some Python code to analyze"}]
        }

    try:
        compile(code, "<user_code>", "exec")
    except SyntaxError as err:
        return {
            "ok": False,
            "message": f"Syntax error at line {err.lineno or 1}",
            "issues": [{
                "type": "SyntaxError",
                "line": err.lineno or 1,
                "column": err.offset or 1,
                "message": err.msg,
                "fix": f"Fix syntax at line {err.lineno or 1}"
            }]
        }

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this Python code for bugs:\n\n{code}"}
        ],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        result = response.json()

        if "choices" not in result:
            return {
                "ok": False,
                "message": "API error",
                "issues": [{"type": "APIError", "line": 1, "column": 1, "message": str(result), "fix": "Check API key"}]
            }

        ai_response = result["choices"][0]["message"]["content"]

        return _parse_ai_response(ai_response)

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "message": "Request timeout",
            "issues": [{"type": "Timeout", "line": 1, "column": 1, "message": "AI analysis timed out", "fix": "Try again"}]
        }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Error: {str(e)}",
            "issues": [{"type": "Error", "line": 1, "column": 1, "message": str(e), "fix": "Try again"}]
        }


def _parse_ai_response(response):
    issues = []
    bugs_found = 0

    lines = response.split('\n')
    parsing_issues = False

    for line in lines:
        line = line.strip()

        if line.startswith("BUGS_FOUND:"):
            try:
                bugs_found = int(line.split(":")[1].strip())
            except:
                pass

        if "ISSUES:" in line:
            parsing_issues = True
            continue

        if parsing_issues and line.startswith("-"):
            line = line[1:].strip()

            if "no bugs" in line.lower() or "code is clean" in line.lower():
                break

            parts = line.split("-")
            if len(parts) >= 2:
                location = parts[0].strip()
                description = "-".join(parts[1:]).strip()

                line_num = 1
                issue_type = "Bug"
                fix = "Review and fix"

                if "line" in location.lower():
                    import re
                    match = re.search(r'\d+', location)
                    if match:
                        line_num = int(match.group())

                if "syntax" in description.lower():
                    issue_type = "SyntaxError"
                elif "index" in description.lower():
                    issue_type = "IndexError"
                elif "type" in description.lower():
                    issue_type = "TypeError"
                elif "key" in description.lower():
                    issue_type = "KeyError"
                elif "infinite" in description.lower():
                    issue_type = "InfiniteLoop"
                elif "logic" in description.lower():
                    issue_type = "LogicError"
                elif "mutable" in description.lower():
                    issue_type = "MutableDefault"
                elif "recursion" in description.lower():
                    issue_type = "RecursionError"

                if "fix:" in description.lower():
                    parts = description.lower().split("fix:")
                    if len(parts) > 1:
                        fix = parts[1].strip()
                        description = parts[0].strip()

                issues.append({
                    "type": issue_type,
                    "line": line_num,
                    "column": 1,
                    "message": description,
                    "fix": fix
                })

    if bugs_found == 0 and not issues:
        return {
            "ok": True,
            "message": "No bugs detected. Your code is clean! Ready for optimization.",
            "issues": [],
        }
 
    if issues:
        return {
            "ok": False,
            "message": f"Found {len(issues)} issue(s). Fix them before optimizing.",
            "issues": issues,
        }

    return {
        "ok": True,
        "message": "No bugs detected. Your code is clean! Ready for optimization.",
        "issues": [],
    }