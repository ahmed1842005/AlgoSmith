def fibonacci(n):
    """O(2^n) — recursive with no memoization. Cap n at 20 in the executor."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
