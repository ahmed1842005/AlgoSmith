import time
import sys
import os
import threading
import random
import inspect

sys.path.insert(0, os.path.dirname(__file__))
from analyzer_fit import PerformanceAnalyzer

TIMEOUT_SECONDS = 5

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
    Inspect function signature and generate appropriate input for size n.
    case can be 'best', 'avg', or 'worst' for array-based functions.
    Rules:
    - 1 param → pass list(range(n))
    - 2 params where second is likely 'target' or 'index' → pass (list(range(n)), n//2)
    - 2 params where both look like matrices (A, B) → pass two n//10 x n//10 matrices
    - param named 'n' alone → pass integer n
    """
    try:
        params = list(inspect.signature(func).parameters.keys())
    except Exception:
        return (list(range(n)),)

    if len(params) == 0:
        return ()
    if len(params) == 1:
        p = params[0]
        if p == 'n':
            return (n,)
        # Array case - apply case variant
        if case == 'best':
            return (list(range(n)),)  # Already sorted
        elif case == 'worst':
            return (list(range(n, 0, -1)),)  # Reverse sorted
        else:  # avg
            arr = list(range(n))
            random.shuffle(arr)
            return (arr,)
    if len(params) == 2:
        p1, p2 = params
        # matrix case
        if p1 in ('A', 'matrix_a') and p2 in ('B', 'matrix_b'):
            size = max(2, n // 10)
            mat = [[i + j for j in range(size)] for i in range(size)]
            return (mat, mat)
        # search case: arr + target or index
        if p2 in ('target', 'key', 'index', 'val', 'value', 'x'):
            if case == 'best':
                return (list(range(n)), n // 2)
            elif case == 'worst':
                return (list(range(n, 0, -1)), -1)
            else:
                arr = list(range(n))
                random.shuffle(arr)
                return (arr, n // 2)
        return (list(range(n)), list(range(n)))
    # 3+ params — just pass the array to the first
    return (list(range(n)),)


def _should_cap_sizes(func):
    """Check if function is exponential (e.g., Fibonacci) and needs smaller input sizes."""
    try:
        if 'fibonacci' in func.__name__.lower():
            return True
        params = list(inspect.signature(func).parameters.keys())
        # Single param named 'n' suggests pure mathematical function (exponential)
        if len(params) == 1 and params[0] == 'n':
            return True
    except:
        pass
    return False


def get_performance_report(code_string):
    """
    Execute user code safely, measure timing across input sizes with threading timeout,
    run curve fitting, return full report dict.
    Measures best, avg, and worst case times for array-based functions.
    """
    try:
        local_env = {}
        exec(compile(code_string, '<user_code>', 'exec'), {}, local_env)
        func = next((v for v in local_env.values() if callable(v)), None)

        if not func:
            return {"error": "No callable function found in your code."}

        analyzer = PerformanceAnalyzer()
        sizes = analyzer.sizes
        
        # Cap sizes for exponential functions like Fibonacci
        if _should_cap_sizes(func):
            sizes = [5, 7, 10, 12, 15, 18, 20]
        
        times_best = []
        times_avg = []
        times_worst = []

        for n in sizes:
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

        # Guard against all-zero times (very strict - only fail if literally everything is zero)
        if all(t == 0.0 for t in times_avg):
            return {"error": "All runs timed out or returned zero. Try a slower algorithm or check your code."}

        analysis_results = analyzer.fit_and_analyze(sizes, times_avg)

        return {
            "detected":   analysis_results[0]["label"],
            "confidence": analysis_results[0]["confidence"],
            "ranking":    analysis_results,
            "raw_data":   {
                "sizes": sizes,
                "times_best": times_best,
                "times_avg": times_avg,
                "times_worst": times_worst
            }
        }

    except SyntaxError as e:
        return {"error": f"Syntax error in your code: {e}"}
    except Exception as e:
        return {"error": str(e)}