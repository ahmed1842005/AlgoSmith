import time
import sys
import os
import threading
import random
import inspect

sys.path.insert(0, os.path.dirname(__file__))
from analyzer_fit import PerformanceAnalyzer

TIMEOUT_SECONDS = 1.0
MAX_BENCHMARK_SECONDS = 4.0


def _run_with_timeout(func, args, results, index):
    """Run func(*args), store elapsed time in results[index]. Used for threading."""
    try:
        start = time.perf_counter()
        func(*args)
        results[index] = time.perf_counter() - start
    except Exception:
        results[index] = None


def _generate_input(func, n, case='avg'):
    """
    Generate suitable input based on function signature.
    """
    try:
        params = list(inspect.signature(func).parameters.keys())
    except Exception:
        return (list(range(n)),)

    # Case 1: function takes one parameter
    if len(params) == 1:
        if params[0] == 'n':
            return (n,)
        return (list(range(n)),)

    # Case 2: function takes two parameters
    elif len(params) == 2:
        if 'target' in params[1] or 'index' in params[1]:
            return (list(range(n)), n // 2)

        # assume matrices
        size = max(2, n // 10)
        A = [[random.randint(0, 10) for _ in range(size)] for _ in range(size)]
        B = [[random.randint(0, 10) for _ in range(size)] for _ in range(size)]
        return (A, B)

    # Case 3: 3+ params
    return (list(range(n)),)


def _should_cap_sizes(func):
    """Check if function is exponential (e.g., Fibonacci)."""
    try:
        if 'fibonacci' in func.__name__.lower():
            return True

        params = list(inspect.signature(func).parameters.keys())
        if len(params) == 1 and params[0] == 'n':
            return True
    except:
        pass

    return False


def get_performance_report(code_string):
    try:
        exec_env = {}
        exec(compile(code_string, '<user_code>', 'exec'), exec_env, exec_env)

        func = next((v for v in exec_env.values() if callable(v)), None)

        if not func:
            return {"error": "No callable function found in your code."}

        analyzer = PerformanceAnalyzer()
        sizes = analyzer.sizes

        if _should_cap_sizes(func):
            sizes = [5, 7, 10, 12, 15, 18, 20]

        measured_sizes = []
        times_best = []
        times_avg = []
        times_worst = []

        benchmark_start = time.perf_counter()

        for n in sizes:
            if time.perf_counter() - benchmark_start > MAX_BENCHMARK_SECONDS:
                break

            measured_sizes.append(n)

            # Best case
            result_best = [None]
            args_best = _generate_input(func, n, 'best')
            thread = threading.Thread(target=_run_with_timeout, args=(func, args_best, result_best, 0))
            thread.daemon = True
            thread.start()
            thread.join(timeout=TIMEOUT_SECONDS)
            times_best.append(result_best[0] if result_best[0] is not None else 0.0)

            # Average case
            result_avg = [None]
            args_avg = _generate_input(func, n, 'avg')
            thread = threading.Thread(target=_run_with_timeout, args=(func, args_avg, result_avg, 0))
            thread.daemon = True
            thread.start()
            thread.join(timeout=TIMEOUT_SECONDS)
            times_avg.append(result_avg[0] if result_avg[0] is not None else 0.0)

            # Worst case
            result_worst = [None]
            args_worst = _generate_input(func, n, 'worst')
            thread = threading.Thread(target=_run_with_timeout, args=(func, args_worst, result_worst, 0))
            thread.daemon = True
            thread.start()
            thread.join(timeout=TIMEOUT_SECONDS)
            times_worst.append(result_worst[0] if result_worst[0] is not None else 0.0)

        if all(t == 0.0 for t in times_avg):
            return {"error": "All runs timed out or returned zero. Try a slower algorithm or check your code."}

        analysis_results = analyzer.fit_and_analyze(measured_sizes, times_avg)

        return {
            "detected": analysis_results[0]["label"],
            "confidence": analysis_results[0]["confidence"],
            "ranking": analysis_results,
            "raw_data": {
                "sizes": measured_sizes,
                "times_best": times_best,
                "times_avg": times_avg,
                "times_worst": times_worst
            }
        }

    except SyntaxError as e:
        return {"error": f"Syntax error in your code: {e}"}
    except Exception as e:
        return {"error": str(e)}