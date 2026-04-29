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

    # 1. Static analysis
    try:
        static_result = get_code_analysis(code)
        static_prediction = static_result.get("complexity", "Unknown")
    except Exception:
        static_prediction = "Unknown"

    # 2. Execution + curve fitting
    fit_result = get_performance_report(code)
    if "error" in fit_result:
        return {"error": fit_result["error"]}

    measured_complexity = fit_result["detected"]
    confidence          = fit_result["confidence"]
    sizes               = fit_result["raw_data"]["sizes"]
    times_best_ms       = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_best"]]
    times_avg_ms        = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_avg"]]
    times_worst_ms      = [round(t * 1000, 4) for t in fit_result["raw_data"]["times_worst"]]

    # 3. AI explanation (combined explanation + optimization)
    try:
        explanation = explain(code, measured_complexity, static_prediction)
    except Exception as e:
        explanation = f"AI explanation unavailable: {e}"

    return {
        "measured":     measured_complexity,
        "static":       static_prediction,
        "confidence":   confidence,
        "explanation":  explanation,
        "sizes":        sizes,
        "times_best":   times_best_ms,
        "times_avg":    times_avg_ms,
        "times_worst":  times_worst_ms,
        "ranking":      fit_result["ranking"],
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
    eel.start("index.html", size=(1400, 850), port=8000)


if __name__ == "__main__":
    main()
