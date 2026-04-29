import time
from analyzer_fit import PerformanceAnalyzer
from drow import plot_complexity_graph 

def get_performance_report(code_string, show_graph=False):
    try:
        local_env = {}
        exec(code_string, {}, local_env)
        func = next((v for v in local_env.values() if callable(v)), None)
        
        if not func:
            return {"error function not founded"}

        analyzer = PerformanceAnalyzer()
        sizes = analyzer.sizes
        times = []

        for n in sizes:
            test_data = list(range(n)) 
            start = time.perf_counter()
            try:
                func(test_data)
            except:
                func(n)
            times.append(time.perf_counter() - start)

        analysis_results = analyzer.fit_and_analyze(sizes, times)
        
        report = {
            "detected": analysis_results[0]["label"],
            "confidence": analysis_results[0]["confidence"],
            "ranking": analysis_results,
            "raw_data": {"sizes": sizes, "times": times}
        }

        
        if show_graph:
            plot_complexity_graph(report)

        return report
    except Exception as e:
        return {"error": str(e)}