import ast  # noqa: D100
import json
from typing import Any


class CFGNode:
    """Represents a node in the Control Flow Graph."""

    def __init__(  # noqa: D107
        self,
        id_: int,
        label: str,
        ast_node: ast.AST | None = None,
    ) -> "CFGNode":
        self.id = id_
        self.label = label
        self.ast_node = ast_node
        self.successors: list[int] = []
        self.predecessors: list[int] = []

    def to_dict(self) -> dict[str, Any]:  # noqa: D102
        return {
            "id": self.id,
            "label": self.label,
            "successors": self.successors,
            "predecessors": self.predecessors,
            "ast_type": type(self.ast_node).__name__ if self.ast_node else None,
        }


class CFGVisitor(ast.NodeVisitor):
    """AST visitor that builds a Control Flow Graph."""

    def __init__(self, target_function: str | None = None) -> "CFGVisitor":  # noqa: D107
        self.nodes: list[CFGNode] = []
        self.current_node: CFGNode | None = None
        self.node_counter = 0
        self.entry_node: CFGNode | None = None
        self.exit_node: CFGNode | None = None

        self.target_function = target_function
        self.in_target_function = False
        self.function_cfg: dict[str, Any] | None = None

    def _create_node(self, label: str, ast_node: ast.AST | None = None) -> CFGNode:
        """Create a new CFG node."""  # noqa: DOC201
        node = CFGNode(self.node_counter, label, ast_node)
        self.nodes.append(node)
        self.node_counter += 1
        return node

    def _connect_nodes(self, from_node: CFGNode, to_node: CFGNode) -> None:  # noqa: PLR6301
        """Create an edge between two nodes."""
        if to_node.id not in from_node.successors:
            from_node.successors.append(to_node.id)
        if from_node.id not in to_node.predecessors:
            to_node.predecessors.append(from_node.id)

    def visit_Module(self, node: ast.Module):  # noqa: ANN201, D102
        if self.target_function:
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.FunctionDef)
                    and stmt.name == self.target_function
                ):
                    self.visit_FunctionDef(stmt)
                    break
            else:
                # Function not found
                self.function_cfg = {
                    "error": f"Function '{self.target_function}' not found",
                }
            return

        # Create entry node for the module
        entry_node = self._create_node("Module Entry")
        self.entry_node = entry_node
        self.current_node = entry_node

        # Visit all statements in the module
        for stmt in node.body:
            self.visit(stmt)

        # Create exit node
        exit_node = self._create_node("Module Exit")
        self.exit_node = exit_node
        if self.current_node:
            self._connect_nodes(self.current_node, exit_node)

    def visit_FunctionDef(self, node: ast.FunctionDef):  # noqa: ANN201, D102
        # Check if this is our target function
        if self.target_function and node.name != self.target_function:
            return None

        self.in_target_function = True

        # Create function entry node
        func_entry = self._create_node(f"Function Entry: {node.name}", node)
        self.entry_node = func_entry
        self.current_node = func_entry

        # Create parameters node
        params_text = ", ".join(arg.arg for arg in node.args.args)
        params_node = self._create_node(f"Parameters: {params_text}")
        self._connect_nodes(self.current_node, params_node)
        self.current_node = params_node

        # Visit function body
        for stmt in node.body:
            self.visit(stmt)

        # Create function exit
        func_exit = self._create_node("Function Exit")
        self.exit_node = func_exit
        if self.current_node:
            self._connect_nodes(self.current_node, func_exit)

        self.in_target_function = False
        return func_exit

    def visit_If(self, node: ast.If):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        # Create if node
        if_node = self._create_node("If condition", node.test)
        if self.current_node:
            self._connect_nodes(self.current_node, if_node)

        # Save current node for merging
        merge_node = self._create_node("If merge")

        # Process true branch
        self.current_node = if_node
        true_entry = self._create_node("If true branch")
        self._connect_nodes(if_node, true_entry)
        self.current_node = true_entry

        for stmt in node.body:
            self.visit(stmt)

        if self.current_node:
            self._connect_nodes(self.current_node, merge_node)

        # Process false branch (if exists)
        if node.orelse:
            self.current_node = if_node
            false_entry = self._create_node("If false branch")
            self._connect_nodes(if_node, false_entry)
            self.current_node = false_entry

            for stmt in node.orelse:
                self.visit(stmt)

            if self.current_node:
                self._connect_nodes(self.current_node, merge_node)
        else:
            # No else branch, connect if node directly to merge
            self._connect_nodes(if_node, merge_node)

        self.current_node = merge_node
        return merge_node

    def visit_While(self, node: ast.While):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        # Create while header node
        while_header = self._create_node("While header", node.test)
        if self.current_node:
            self._connect_nodes(self.current_node, while_header)

        # Create merge node for after the loop
        after_loop = self._create_node("After while")

        # Process loop body
        self.current_node = while_header
        body_entry = self._create_node("While body")
        self._connect_nodes(while_header, body_entry)
        self.current_node = body_entry

        for stmt in node.body:
            self.visit(stmt)

        # Connect back to header (loop)
        if self.current_node:
            self._connect_nodes(self.current_node, while_header)

        # Connect header to after loop (break condition)
        self._connect_nodes(while_header, after_loop)

        self.current_node = after_loop
        return after_loop

    def visit_For(self, node: ast.For):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        # Create for header node
        for_header = self._create_node("For header", node)
        if self.current_node:
            self._connect_nodes(self.current_node, for_header)

        # Create merge node for after the loop
        after_loop = self._create_node("After for")

        # Process loop body
        self.current_node = for_header
        body_entry = self._create_node("For body")
        self._connect_nodes(for_header, body_entry)
        self.current_node = body_entry

        for stmt in node.body:
            self.visit(stmt)

        # Connect back to header (loop)
        if self.current_node:
            self._connect_nodes(self.current_node, for_header)

        # Connect header to after loop (break condition)
        self._connect_nodes(for_header, after_loop)

        self.current_node = after_loop
        return after_loop

    def visit_Break(self, node: ast.Break):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        # Break will be handled by the loop constructs
        break_node = self._create_node("Break", node)
        if self.current_node:
            self._connect_nodes(self.current_node, break_node)
        # The actual connection to after-loop happens in visit_While/visit_For
        return break_node

    def visit_Continue(self, node: ast.Continue):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        # Continue will be handled by the loop constructs
        continue_node = self._create_node("Continue", node)
        if self.current_node:
            self._connect_nodes(self.current_node, continue_node)
        # The actual connection back to loop header happens in visit_While/visit_For
        return continue_node

    def visit_Return(self, node: ast.Return):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        return_node = self._create_node("Return", node)
        if self.current_node:
            self._connect_nodes(self.current_node, return_node)
        # Return ends the current flow
        self.current_node = None
        return return_node

    def visit_Expr(self, node: ast.Expr):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        expr_node = self._create_node("Expression", node)
        if self.current_node:
            self._connect_nodes(self.current_node, expr_node)
        self.current_node = expr_node
        return expr_node

    def visit_Assign(self, node: ast.Assign):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        assign_node = self._create_node("Assignment", node)
        if self.current_node:
            self._connect_nodes(self.current_node, assign_node)
        self.current_node = assign_node
        return assign_node

    def visit_AugAssign(self, node: ast.AugAssign):  # noqa: ANN201, D102
        if not self.in_target_function and self.target_function:
            return None

        aug_assign_node = self._create_node("Augmented Assignment", node)
        if self.current_node:
            self._connect_nodes(self.current_node, aug_assign_node)
        self.current_node = aug_assign_node
        return aug_assign_node

    def generic_visit(self, node: ast.AST):  # noqa: ANN201
        """Handle all other node types."""  # noqa: DOC201
        if not self.in_target_function and self.target_function:
            return None

        node_label = type(node).__name__
        new_node = self._create_node(node_label, node)
        if self.current_node:
            self._connect_nodes(self.current_node, new_node)
        self.current_node = new_node
        super().generic_visit(node)
        return new_node

    def to_json(self) -> str:
        """Convert CFG to JSON format."""  # noqa: DOC201
        if self.function_cfg:
            return json.dumps(self.function_cfg, indent=2)

        cfg_dict = {
            "entry_node_id": self.entry_node.id if self.entry_node else None,
            "exit_node_id": self.exit_node.id if self.exit_node else None,
            "nodes": [node.to_dict() for node in self.nodes],
        }

        # Add function-specific metadata if targeting a function
        if self.target_function:
            cfg_dict["function_name"] = self.target_function
            cfg_dict["type"] = "function_cfg"
        else:
            cfg_dict["type"] = "module_cfg"

        return json.dumps(cfg_dict, indent=2)

    def build_cfg(self, code: str) -> str:
        """Build CFG from Python code and return as JSON."""  # noqa: DOC201
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.to_json()
        except SyntaxError as e:
            return json.dumps({"error": f"Syntax error: {e}"})


def generate_cfg_from_code(code: str, function_name: str | None = None) -> str:
    """Convenience function to generate CFG JSON from code string."""  # noqa: D401, DOC201
    visitor = CFGVisitor(target_function=function_name)
    return visitor.build_cfg(code)


def generate_cfg_from_file(filename: str, function_name: str | None = None) -> str:
    """Generate CFG JSON from a Python file."""  # noqa: DOC201
    with open(filename, encoding="utf-8") as f:  # noqa: FURB101, PTH123
        code = f.read()
    return generate_cfg_from_code(code, function_name=function_name)


def get_functions_in_file(filename: str) -> list[str]:
    """Get list of all function names in a Python file."""  # noqa: DOC201
    with open(filename, encoding="utf-8") as f:  # noqa: FURB101, PTH123
        code = f.read()

    try:
        tree = ast.parse(code)
        return [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]
    except SyntaxError:
        return []


# Example usage and test
if __name__ == "__main__":
    # Example Python code
    example_code = '''
def factorial(n):
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    else:
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

def fibonacci(n):
    """Calculate nth fibonacci number"""
    if n <= 1:
        return n
    else:
        a, b = 0, 1
        for i in range(2, n + 1):
            a, b = b, a + b
        return b

def is_even(num):
    """Check if number is even"""
    return num % 2 == 0

x = 5
print(factorial(x))
print(fibonacci(x))
'''

    print("=== Full Module CFG ===")
    full_cfg = generate_cfg_from_code(example_code)
    full_data = json.loads(full_cfg)
    print(f"Full CFG has {len(full_data['nodes'])} nodes")

    print("\n=== Factorial Function CFG ===")
    factorial_cfg = generate_cfg_from_code(example_code, "factorial")
    factorial_data = json.loads(factorial_cfg)
    print(f"Factorial CFG has {len(factorial_data['nodes'])} nodes")
    print(factorial_cfg)

    print("\n=== Fibonacci Function CFG ===")
    fibonacci_cfg = generate_cfg_from_code(example_code, "fibonacci")
    fibonacci_data = json.loads(fibonacci_cfg)
    print(f"Fibonacci CFG has {len(fibonacci_data['nodes'])} nodes")

    print("\n=== Non-existent Function ===")
    not_found_cfg = generate_cfg_from_code(example_code, "nonexistent")
    print(not_found_cfg)

    # Example of getting all functions in code
    print("\n=== All Functions in Code ===")
    functions = get_functions_in_file(__file__)  # This file itself
    print(f"Functions in this file: {functions}")
