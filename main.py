import sys
import os                       
import eel

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'engin'))
sys.path.insert(0, os.path.join(BASE, 'ai'))
sys.path.insert(0, os.path.join(BASE, 'algorithms'))

from bridge_fit import get_performance_report
from bridge_static import get_code_analysis
from ai_explainer import explain 
from optimizer import optimize
from bug_detector import detect_bugs
from chat import chat

@eel.expose
def run_algorithm(algorithm, code, input_data):
    if not code.strip():
        return {"error": "No code provided."}

    
    try:
        static_result     = get_code_analysis(code)
        static_prediction = static_result.get("complexity", "Unknown")
    except Exception:
        static_prediction = "Unknown"

    
    sizes          = None
    times_ms       = []
    confidence     = 0
    ranking        = []

    fit_result = get_performance_report(code)
    if "error" not in fit_result:
        sizes      = fit_result["raw_data"]["sizes"]
        times_ms   = [round(t * 1000, 4) for t in fit_result["raw_data"]["times"]]
        confidence = fit_result["confidence"]
        ranking    = fit_result["ranking"]

    # 3. AI explanation
    try:
        explanation = explain(code, static_prediction, static_prediction)
    except Exception as e:
        explanation = f"AI explanation unavailable: {e}"

    return {
        "measured":    static_prediction,
        "static":      static_prediction,
        "confidence":  confidence,
        "explanation": explanation,
        "sizes":       sizes or [],
        "times":       times_ms,
        "ranking":     ranking,
    }

@eel.expose
def scan_bugs(code):
    if not code.strip():
        return {"ok": False, "message": "No code provided.", "issues": []}
    return detect_bugs(code)

@eel.expose
def get_optimization(code):
    if not code.strip():
        return "No code provided."
    bug_report = detect_bugs(code)
    if not bug_report.get("ok", False):
        return "I can't optimize the code because it has bugs. Please fix the reported issues first."
    
    try:
        return optimize(code)
    except Exception as e:
        return f"Optimizer error: {e}"


@eel.expose
def chat_with_ai(message):
    return chat(message)


def main():
    eel.init("web")
    eel.start("index.html", size=(1400, 850), port=8000)


if __name__ == "__main__":
    main()