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


def binary_search(arr, target=None):
    """O(log n) — requires sorted input"""
    if target is None:
        target = len(arr) // 2
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
