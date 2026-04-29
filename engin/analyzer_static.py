import ast
import math


class UltimateRecursionAnalyzer:
    def __init__(self, code_str):
        self.code = code_str
        self.func_name = ""
        self.calls = []
        self.a = 0
        self.b = 2
        self.d = 0
        self.is_division = True

    def analyze(self):
        try:
            tree = ast.parse(self.code)
            func_node = next(
                (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)), None
            )
            if not func_node:
                return {"complexity": "No function"}

            self.func_name = func_node.name
            self._collect_calls(func_node)
            self._analyze_arguments()
            self.d = self._get_loop_depth(func_node)

            if self._has_slicing(func_node):
                self.d = max(self.d, 1)

            if self.a > 0:
                return self._solve_recursive()
            else:
                return self._solve_iterative(func_node)

        except Exception as e:
            return {"error": str(e)}

    def _collect_calls(self, node):
        """
        Walk the function body and collect recursive calls with their weights.
        Weight = how many times that call executes per invocation.

        Rules:
          - Call inside for _ in range(K): → weight K
          - Call inside if/elif/else branch where ALL sibling branches have
            at most 1 recursive call → weight 1 (mutual exclusion: only one
            branch runs at runtime, so effective a = max branch depth = 1).
          - Otherwise → weight = number of calls found.
        """
        self._walk_calls(node, multiplier=1)
        self.a = sum(c["weight"] for c in self.calls)

    def _walk_calls(self, node, multiplier):
        """Recursively walk AST; amplify call weight when inside a ranged loop."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                loop_mult = self._loop_multiplier(child)
                self._walk_calls(child, multiplier * loop_mult)
            elif isinstance(child, ast.If):
                # Mutual exclusion: if every branch has ≤1 recursive call
                # only ONE branch runs at runtime → effective a = 1.
                branch_counts = self._calls_per_branch(child)
                if all(c <= 1 for c in branch_counts) and sum(branch_counts) > 1:
                    # Pick ONE representative branch that actually has a call
                    rep_body = self._branch_with_call(child)
                    self._walk_calls_in_body(rep_body, multiplier)
                else:
                    self._walk_calls(child, multiplier)
            elif (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == self.func_name
            ):
                self.calls.append({"node": child, "weight": multiplier})
            else:
                self._walk_calls(child, multiplier)

    def _calls_per_branch(self, if_node):
        """
        Return a list with the recursive-call count for each branch of an
        if/elif/else chain.  Used to detect mutual exclusion.
        """
        counts = []
        # body of the if
        counts.append(self._count_calls_in_stmts(if_node.body))
        # walk elif / else chain
        orelse = if_node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                counts.append(self._count_calls_in_stmts(orelse[0].body))
                orelse = orelse[0].orelse
            else:
                counts.append(self._count_calls_in_stmts(orelse))
                break
        return counts

    def _count_calls_in_stmts(self, stmts):
        """Count recursive calls inside a list of statements (non-recursive into sub-ifs)."""
        count = 0
        for stmt in stmts:
            for node in ast.walk(stmt):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == self.func_name
                ):
                    count += 1
        return count

    def _branch_with_call(self, if_node):
        """Return the body (list of stmts) of the first branch containing a recursive call."""
        # Check if-body
        if self._count_calls_in_stmts(if_node.body) > 0:
            return if_node.body
        # Walk elif/else chain
        orelse = if_node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                if self._count_calls_in_stmts(orelse[0].body) > 0:
                    return orelse[0].body
                orelse = orelse[0].orelse
            else:
                return orelse
        return if_node.body   # fallback

    def _walk_calls_in_body(self, stmts, multiplier):
        """Walk a list of statements for recursive calls."""
        for stmt in stmts:
            self._walk_calls(stmt, multiplier)

    @staticmethod
    def _loop_multiplier(loop_node):
        """Return the constant repeat-count of a for-range loop, else 1."""
        if isinstance(loop_node, ast.For):
            iter_ = loop_node.iter
            if (
                isinstance(iter_, ast.Call)
                and isinstance(iter_.func, ast.Name)
                and iter_.func.id == "range"
                and len(iter_.args) == 1
                and isinstance(iter_.args[0], ast.Constant)
            ):
                return int(iter_.args[0].value)
        return 1

    def _analyze_arguments(self):
        """
        Determine whether the recurrence is divide (n/b) or subtract (n-b).

        ROOT CAUSE of the binary-search bug:
          binary_search(arr, mid+1, hi)  →  mid+1 was counted as Sub by 1
          → analyzer concluded subtraction recurrence → O(2^n)  ✗

        FIX: only treat an argument as a size-reduction signal when its
        left-hand side is a *direct parameter* of the function AND that
        parameter is not a locally-derived variable (like `mid`).
        Index offsets like mid+1 or hi-1 are ignored.
        """
        try:
            tree = ast.parse(self.code)
            func_node = next(
                n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == self.func_name
            )
            param_names = {a.arg for a in func_node.args.args}
        except Exception:
            param_names = set()
            func_node = None

        # Variables assigned inside the function body (derived, not size params)
        derived_names = set()
        if func_node:
            for node in ast.walk(func_node):
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            derived_names.add(t.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    derived_names.add(node.target.id)

        size_params = param_names - derived_names   # e.g. {n, arr, lo, hi} not {mid}

        div_count = 0
        sub_count = 0
        b_div = 2
        b_sub = 1

        for call_info in self.calls:
            call = call_info["node"]
            for arg in call.args:
                if not isinstance(arg, ast.BinOp):
                    continue
                lhs = arg.left
                rhs = arg.right
                # lhs must be a bare name that is a size parameter
                if not isinstance(lhs, ast.Name):
                    continue
                if lhs.id not in size_params:
                    continue           # skip mid+1, mid-1, etc.
                if not isinstance(rhs, ast.Constant):
                    continue

                if isinstance(arg.op, (ast.Div, ast.FloorDiv)):
                    div_count += 1
                    b_div = int(rhs.value)
                elif isinstance(arg.op, ast.Sub) and rhs.value > 0:
                    sub_count += 1
                    b_sub = int(rhs.value)

        # Majority vote; ties → division (correct default for D&C)
        if sub_count > div_count:
            self.is_division = False
            self.b = b_sub
        else:
            self.is_division = True
            self.b = b_div

    def _get_loop_depth(self, node, depth=0):
        """
        FIX: also count ast.ListComp / ast.SetComp / ast.GeneratorExp as
        implicit O(n) loops — e.g. [x for x in arr if x < pivot] iterates
        over arr fully, so it contributes one loop level of work.
        """
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                max_depth = max(
                    max_depth, self._get_loop_depth(child, depth + 1)
                )
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
                # each generator inside the comprehension = one loop level
                gen_depth = depth + len(child.generators)
                max_depth = max(max_depth, gen_depth)
                # still recurse in case element expr has nested comps
                max_depth = max(max_depth, self._get_loop_depth(child, depth))
            else:
                max_depth = max(
                    max_depth, self._get_loop_depth(child, depth)
                )
        return max_depth

    def _has_slicing(self, node):
        return any(
            isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Slice)
            for n in ast.walk(node)
        )

    # ------------------------------------------------------------------
    # Iterative path
    # ------------------------------------------------------------------

    def _solve_iterative(self, node):
        loops = [
            self._get_loop_type(n)
            for n in ast.walk(node)
            if isinstance(n, (ast.For, ast.While))
        ]
        if not loops:
            return {"function": self.func_name, "complexity": "O(1)", "type": "Iterative"}

        n_c = loops.count("n")
        log_c = loops.count("log n")

        # FIX: use actual nesting depth instead of a flat loop count
        depth = self._get_loop_depth(node)

        if log_c and not n_c:
            # pure log loops
            comp = f"O((log n)^{log_c})" if log_c > 1 else "O(log n)"
        elif n_c == 0:
            comp = "O(1)"
        else:
            # FIX: base complexity on nesting depth, not count of "n" loops
            comp = f"O(n^{depth})" if depth > 1 else "O(n)"
            if log_c:
                comp += f" · (log n)^{log_c}"

        return {
            "function": self.func_name,
            "type": "Iterative",
            "loops": loops,
            "loop_depth": depth,
            "complexity": comp,
        }

    def _get_loop_type(self, node):
        for n in ast.walk(node):
            if isinstance(n, ast.AugAssign) and isinstance(
                n.op, (ast.Div, ast.FloorDiv, ast.Mult)
            ):
                return "log n"
        return "n"

    # ------------------------------------------------------------------
    # Recursive path  –  Master Theorem & subtraction recurrences
    # ------------------------------------------------------------------

    @staticmethod
    def _work_str(d):
        """FIX: never emit 'n^1'; use 'n' instead."""
        if d == 0:
            return "1"
        if d == 1:
            return "n"
        return f"n^{d}"

    def _solve_recursive(self):
        work = self._work_str(self.d)

        if self.is_division:
            return self._master_theorem(work)
        else:
            return self._subtraction_recurrence(work)

    def _master_theorem(self, work):
        """
        Master Theorem: T(n) = a·T(n/b) + n^d
        Case 1: log_b(a) > d  →  O(n^log_b(a))       [leaves dominate]
        Case 2: log_b(a) == d →  O(n^d · log n)        [balanced]
        Case 3: log_b(a) < d  →  O(n^d)                [root dominates]

        FIX: compare log_b(a) with d directly (avoids floating-point errors
        from the old  r = a / b^d  approach).
        """
        equation = f"T(n) = {self.a}T(n/{self.b}) + {work}"
        log_b_a = math.log(self.a, self.b)
        eps = 1e-9

        if log_b_a > self.d + eps:
            # Case 1
            exp = round(log_b_a, 3)
            exp_str = str(int(exp)) if exp == int(exp) else str(exp)
            comp = f"O(n^{exp_str})"
            case = 1
            dominant = "Leaves dominate"
        elif abs(log_b_a - self.d) < eps:
            # Case 2
            comp = "O(log n)" if self.d == 0 else f"O({work} log n)"
            case = 2
            dominant = "Balanced"
        else:
            # Case 3
            comp = f"O({work})"
            case = 3
            dominant = "Root dominates"

        return {
            "function": self.func_name,
            "type": "Recursive (divide-and-conquer)",
            "complexity": comp,
            "equation": equation,
            "master_case": case,
            "dominant": dominant,
            "log_b_a": round(log_b_a, 4),
        }

    def _subtraction_recurrence(self, work):
        """
        Subtraction recurrence: T(n) = a·T(n-b) + n^d
        a == 1 → polynomial:   O(n^(d+1))
        a > 1  → exponential:  O(a^(n/b))

        FIX: a==1 with d==0 should give O(n), not O(n^1).
        """
        equation = f"T(n) = {self.a}T(n-{self.b}) + {work}"

        if self.a == 1:
            # FIX: use _work_str on d+1 to get "n" instead of "n^1"
            comp = self._work_str(self.d + 1)
            comp = f"O({comp})"
            dominant = "Linear expansion"
        else:
            # FIX: b==1 means T(n)=aT(n-1)+... → O(a^n), skip the "/1"
            exp_str = f"n/{self.b}" if self.b > 1 else "n"
            comp = f"O({self.a}^({exp_str}))"
            dominant = "Exponential expansion"

        return {
            "function": self.func_name,
            "type": "Recursive (subtraction)",
            "complexity": comp,
            "equation": equation,
            "dominant": dominant,
        }


# ======================================================================
# Quick test-suite
# ======================================================================

def run_tests():
    tests = [
        # (description, code, expected_complexity)
        (
            "Quick Sort – O(n log n)",
            """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left   = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right  = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
""",
            "O(n log n)",
        ),
        (
            "Merge Sort – O(n log n)",
            """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
""",
            "O(n log n)",
        ),
        (
            "Binary Search – O(log n)",
            """
def binary_search(arr, lo, hi):
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    return binary_search(arr, lo, mid // 2)
""",
            "O(log n)",
        ),
        (
            "Strassen – O(n^2.807)",
            """
def strassen(n):
    if n <= 1:
        return
    for i in range(n):
        for j in range(n):
            pass
    for _ in range(7):
        strassen(n // 2)
""",
            "O(n^2.807)",
        ),
        (
            "Linear recursion – O(n)",
            """
def sum_n(n):
    if n == 0:
        return 0
    return sum_n(n - 1) + 1
""",
            "O(n)",
        ),
        (
            "Fibonacci – O(2^n)",
            """
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 1)
""",
            "O(2^(n))",
        ),
        (
            "Iterative O(1)",
            """
def constant(x):
    return x + 1
""",
            "O(1)",
        ),
        (
            "Iterative O(n)",
            """
def linear(arr):
    for x in arr:
        print(x)
""",
            "O(n)",
        ),
        (
            "Iterative O(n²)",
            """
def bubble(arr):
    for i in range(len(arr)):
        for j in range(len(arr)):
            pass
""",
            "O(n^2)",
        ),
    ]

    print(f"{'Test':<35} {'Got':<20} {'Expected':<20} {'Pass?'}")
    print("-" * 85)
    passed = 0
    for desc, code, expected in tests:
        result = UltimateRecursionAnalyzer(code).analyze()
        got = result.get("complexity", result.get("error", "???"))
        ok = got == expected
        if ok:
            passed += 1
        status = "✓" if ok else "✗"
        print(f"{desc:<35} {got:<20} {expected:<20} {status}")

    print(f"\n{passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    run_tests()