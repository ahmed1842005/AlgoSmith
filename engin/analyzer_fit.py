import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import pearsonr


# ---------------------------------------------------------------------------
# Models – all take a single scale parameter `a`.
# IMPORTANT: exponential model uses NORMALISED exponent (n / n_ref) to avoid
# overflow when scipy evaluates the model at large n (e.g. n=1000 → 2^1000).
# ---------------------------------------------------------------------------

_N_REF = 20.0   # reference size for exponential normalisation

MODELS = {
    "O(1)":       lambda n, a: np.full_like(n, a, dtype=float),
    "O(log n)":   lambda n, a: a * np.log2(np.maximum(n, 1)),
    "O(n)":       lambda n, a: a * n,
    "O(n log n)": lambda n, a: a * n * np.log2(np.maximum(n, 1)),
    "O(n²)":      lambda n, a: a * n ** 2,
    "O(n³)":      lambda n, a: a * n ** 3,
    # FIX 1: normalise exponent → 2^(n/N_REF) never overflows for n≤1000
    "O(2ⁿ)":      lambda n, a: a * np.power(2.0, n / _N_REF),
}


class PerformanceAnalyzer:
    def __init__(self):
        self.sizes = [50, 100, 200, 400, 700, 1000]

    # ------------------------------------------------------------------
    def fit_and_analyze(self, input_sizes, times):
        if len(input_sizes) < 3:
            return [{"label": "Unknown", "sse": float("inf"),
                     "scale": 0, "confidence": 0}]

        ns = np.array(input_sizes, dtype=float)
        ts = np.array(times,       dtype=float)

        # FIX 2: drop zero / negative times before fitting (timeouts stored as 0)
        valid = ts > 0
        if valid.sum() < 3:
            return [{"label": "Unknown", "sse": float("inf"),
                     "scale": 0, "confidence": 0}]
        ns, ts = ns[valid], ts[valid]

        # FIX 3: normalise times → fitting is scale-independent
        ts_norm = ts / ts.max()

        results = []
        for label, fn in MODELS.items():
            sse, scale, r2 = self._fit_model(fn, ns, ts_norm)
            results.append({"label": label, "sse": sse,
                            "scale": scale, "r2": r2, "confidence": 0})

        results.sort(key=lambda r: r["sse"])
        return self._compute_confidence(results)

    # ------------------------------------------------------------------
    def _fit_model(self, fn, ns, ts):
        try:
            # FIX 4: bound a > 0; use robust p0
            params, _ = curve_fit(
                fn, ns, ts,
                p0=[1e-6],
                bounds=(0, np.inf),
                maxfev=10_000,
            )
            a = params[0]
            predicted = fn(ns, a)

            if not np.all(np.isfinite(predicted)):
                return float("inf"), 0.0, 0.0

            sse = float(np.sum((ts - predicted) ** 2))

            # R² for secondary ranking when SSEs are close
            ss_tot = float(np.sum((ts - ts.mean()) ** 2))
            r2 = 1 - sse / ss_tot if ss_tot > 0 else 0.0

            if np.isfinite(sse) and a >= 0:
                return sse, float(a), r2
            return float("inf"), 0.0, 0.0
        except Exception:
            return float("inf"), 0.0, 0.0

    # ------------------------------------------------------------------
    def _compute_confidence(self, results):
        """
        FIX 5: confidence was computed as (1 - sse/max_sse)*100 which gives
        100% to the WORST model (max SSE) and distorts rankings.

        Correct approach: use relative SSE improvement over the worst finite
        model, then re-base so the BEST model = 100%.
        """
        finite = [r for r in results if r["sse"] != float("inf")]
        if not finite:
            for r in results:
                r["confidence"] = 0
            return results

        best_sse  = finite[0]["sse"]   # smallest SSE (sorted)
        worst_sse = finite[-1]["sse"]  # largest SSE

        for r in results:
            if r["sse"] == float("inf"):
                r["confidence"] = 0
            else:
                if worst_sse == best_sse:
                    # All models fit equally well
                    r["confidence"] = 100
                else:
                    # Score: 100% for best SSE, 0% for worst SSE
                    score = (worst_sse - r["sse"]) / (worst_sse - best_sse)
                    r["confidence"] = round(score * 100)

        return results