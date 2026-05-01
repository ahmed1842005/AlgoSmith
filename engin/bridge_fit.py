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
        times = []

        benchmark_start = time.perf_counter()

        for n in sizes:
            if time.perf_counter() - benchmark_start > MAX_BENCHMARK_SECONDS:
                break

            measured_sizes.append(n)

            # Run 3 times for smaller sizes (better accuracy), 1 time for larger sizes (speed)
            run_count = 3 if n < 200 else 1
            run_times = []
            
            for _ in range(run_count):
                result = [None]
                args = _generate_input(func, n, 'avg')
                thread = threading.Thread(target=_run_with_timeout, args=(func, args, result, 0))
                thread.daemon = True
                thread.start()
                thread.join(timeout=TIMEOUT_SECONDS)
                run_time = result[0] if result[0] is not None else 0.0
                run_times.append(run_time)
            
            # Take minimum time across runs
            min_time = min(run_times) if run_times else 0.0
            times.append(min_time)

        if all(t == 0.0 for t in times):
            return {"error": "All runs timed out or returned zero. Try a slower algorithm or check your code."}

        analysis_results = analyzer.fit_and_analyze(measured_sizes, times)

        return {
            "detected": analysis_results[0]["label"],
            "confidence": analysis_results[0]["confidence"],
            "ranking": analysis_results,
            "raw_data": {
                "sizes": measured_sizes,
                "times": times
            }
        }

    except SyntaxError as e:
        return {"error": f"Syntax error in your code: {e}"}
    except Exception as e:
        return {"error": str(e)}