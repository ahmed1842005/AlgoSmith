from analyzer_static import UltimateRecursionAnalyzer

def get_code_analysis(code_text):
    if not code_text.strip():
        return {"error": "Code is empty"}
        
    analyzer = UltimateRecursionAnalyzer(code_text)
    result = analyzer.analyze()
    
    return result


# from bridge import get_code_analysis
# result = get_code_analysis("def f(n): ...")
# print(result['complexity'])