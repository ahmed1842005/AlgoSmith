from bridge_static import get_code_analysis

test_code = """
def merge_sort(arr, n):
    if n <= 1:
        return arr
    left  = merge_sort(arr, n // 2)
    right = merge_sort(arr, n // 2)
    for i in range(n):
        pass
    return arr
"""

if __name__ == "__main__":
    report = get_code_analysis(test_code)
    print("--- Analysis Report ---")
    for key, value in report.items():
        print(f"{key.capitalize():<12}: {value}")