import numpy as np
from scipy.optimize import curve_fit

MODELS = {
    "O(1)":       lambda n, a: np.full_like(n, a, dtype=float),
    "O(log n)":   lambda n, a: a * np.log2(n),
    "O(n)":       lambda n, a: a * n,
    "O(n log n)": lambda n, a: a * n * np.log2(n),
    "O(n²)":      lambda n, a: a * n ** 2,
    "O(n³)":      lambda n, a: a * n ** 3,
    "O(2ⁿ)":      lambda n, a: a * np.power(2.0, n),
}

class PerformanceAnalyzer:
    def __init__(self):
        
        self.sizes = [50, 100, 200, 400, 700, 1000]

    def fit_and_analyze(self, input_sizes, times):
        if len(input_sizes) < 3:
            return [{"label": "Unknown", "sse": float("inf"), "scale": 0, "confidence": 0}]

        ns = np.array(input_sizes, dtype=float)
        ts = np.array(times, dtype=float)
        results = []

        for label, fn in MODELS.items():
            sse, scale = self._fit_model(fn, ns, ts)
            results.append({"label": label, "sse": sse, "scale": scale, "confidence": 0})

        
        results.sort(key=lambda r: r["sse"])
        return self._compute_confidence(results)

    def _fit_model(self, fn, ns, ts):
        try:
            # 
            params, _ = curve_fit(fn, ns, ts, p0=[1.0], maxfev=10000)
            a = params[0]
            predicted = fn(ns, a)
            sse = float(np.sum((ts - predicted) ** 2))
            return (sse, float(a)) if np.isfinite(sse) and a >= 0 else (float("inf"), 0.0)
        except:
            return float("inf"), 0.0

    def _compute_confidence(self, results):
        finite_sses = [r["sse"] for r in results if r["sse"] != float("inf")]
        max_sse = max(finite_sses) if finite_sses else 1.0
        for r in results:
            if r["sse"] == float("inf"):
                r["confidence"] = 0
            else:
                r["confidence"] = round((1 - r["sse"] / max_sse) * 100)
        return results