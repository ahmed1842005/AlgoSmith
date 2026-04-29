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
            func_node = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)), None)
            if not func_node: return {"complexity": "No function"}
            
            self.func_name = func_node.name
            self._collect_calls(func_node)
            self._analyze_arguments()
            self.d = self._get_loop_depth(func_node)

            if self._has_slicing(func_node): self.d = max(self.d, 1)

            return self._solve_recursive() if self.a > 0 else self._solve_iterative(func_node)
        except Exception as e:
            return {"error": str(e)}

    def _collect_calls(self, node):
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == self.func_name:
                self.calls.append(n)
        self.a = len(self.calls)

    def _analyze_arguments(self):
        for call in self.calls:
            for arg in call.args:
                if isinstance(arg, ast.BinOp):
                    if isinstance(arg.op, (ast.Div, ast.FloorDiv)):
                        self.is_division = True
                        if isinstance(arg.right, ast.Constant): self.b = arg.right.value
                    elif isinstance(arg.op, ast.Sub):
                        self.is_division = False
                        if isinstance(arg.right, ast.Constant): self.b = arg.right.value

    def _get_loop_depth(self, node, depth=0):
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                max_depth = max(max_depth, self._get_loop_depth(child, depth + 1))
            else:
                max_depth = max(max_depth, self._get_loop_depth(child, depth))
        return max_depth

    def _has_slicing(self, node):
        return any(isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Slice) for n in ast.walk(node))

    def _solve_iterative(self, node):
        loops = [self._get_loop_type(n) for n in ast.walk(node) if isinstance(n, (ast.For, ast.While))]
        if not loops: 
            return {"complexity": "O(1)", "type": "Iterative"}
        
        n_c, log_c = loops.count("n"), loops.count("log n")
        parts = ([f"n^{n_c}" if n_c > 1 else "n"] if n_c else []) + ([f"(log n)^{log_c}" if log_c > 1 else "log n"] if log_c else [])
        return {"function": self.func_name,
                 "type": "Iterative",
                 "loops": loops,
                "complexity": f"O({' '.join(parts)})"}

    def _get_loop_type(self, node):
        for n in ast.walk(node):
            if isinstance(n, ast.AugAssign) and isinstance(n.op, (ast.Div, ast.FloorDiv, ast.Mult)):
                return "log n"
        return "n"

    def _solve_recursive(self):
        work = "1" if self.d == 0 else ("n" if self.d == 1 else f"n^{self.d}")
        if self.is_division:
            equation = f"T(n) = {self.a}T(n/{self.b}) + {work}"
            r = self.a / (self.b ** self.d)
            if r > 1.000000001: 
                log_b_a = math.log(self.a, self.b)
                comp = f"O(n^{round(log_b_a, 4)})"
            elif abs(r - 1) < 1e-9: comp = f"O({work} log n)" if self.d > 0 else "O(log n)"
            else: comp = f"O({work})"
            dom = "Leaves dominate" if r > 1 else ("Root dominates" if r < 1 else "Balanced")
        else:
            equation = f"T(n) = {self.a}T(n-{self.b}) + {work}"
            if self.a == 1: comp = f"O(n^{self.d+1})" if self.d > 0 else "O(n)"
            else: comp = f"O({self.a}^(n/{self.b}))"
            dom = "Exponential expansion"
        
        return {"function": self.func_name,
                 "type": "Recursive",
                   "complexity": comp, 
                   "equation": equation,
                     "dominant": dom}