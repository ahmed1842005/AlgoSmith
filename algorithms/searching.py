def array_index_access(arr):
    """O(1) — direct index access"""
    if not arr:
        return None
    return arr[len(arr) // 2]


def linear_search(arr, target=None):
    """O(n) — scan every element"""
    if target is None:
        target = len(arr) // 2
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1


def binary_search_recursive(arr, low, high, x):

    if high >= low:

        mid = low + (high - low) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] > x:
            return binary_search_recursive(arr, low, mid - 1, x)

        else:
            return binary_search_recursive(arr, mid + 1, high, x)
    else:
        return -1

