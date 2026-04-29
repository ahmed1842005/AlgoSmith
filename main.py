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
    times_best_ms  = []
    times_avg_ms   = []
    times_worst_ms = []
    confidence     = 0
    ranking        = []

    fit_result = get_performance_report(code)
    if "error" not in fit_result:
        sizes          = fit_result["raw_data"]["sizes"]
        times_best_ms  = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_best"]]
        times_avg_ms   = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_avg"]]
        times_worst_ms = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_worst"]]
        confidence     = fit_result["confidence"]
        ranking        = fit_result["ranking"]

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
        "times_best":  times_best_ms,
        "times_avg":   times_avg_ms,
        "times_worst": times_worst_ms,
        "ranking":     ranking,
    }


@eel.expose
def get_optimization(code):
    if not code.strip():
        return "No code provided."
    try:
        return optimize(code)
    except Exception as e:
        return f"Optimizer error: {e}"


def main():
    eel.init("web")
    eel.start("index.html", size=(1400, 850), port=8000, mode='edge')


if __name__ == "__main__":
    main()