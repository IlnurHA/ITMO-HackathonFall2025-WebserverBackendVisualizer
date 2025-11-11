import ast
import json
from typing import Dict, Any, Set

# TODO: what about recursion
# TODO: process import using *

"""
Usage: parsed_file = FileProcessor(input_data).process_files()

Expecting input: dict with parsed file paths, e.g.
{
  "modules": [
    {
      "module": "abc/bar/foo.py",
      "metadata": "?"
    },
    {
      "module": "abc/bar/hoo.py",
      "metadata": "?"
    },
    .....
  ]
}

Expecting output: json, e.g.
{
  "modules": [
    {
      "module": "backend.app.test.file_example",
      "metadata": "?",
      "tree": {
        "children": [
          {
            "name": "MyClass",
            "type": "class",
            "lineno": 3,
            "children": [
              {
                "name": "__init__",
                "type": "function",
                "lineno": 4,
                "children": [],
                "args": [
                  "self"
                ],
                "calls": [
                  {
                    "function": "file_example_imported.create_class",
                    "module": "file_example_imported",
                    "lineno": 5,
                    "type": "internal"
                  }
                ]
              },
              {
                "name": "outer_method",
                "type": "function",
                "lineno": 7,
                "children": [
                  {
                    "name": "inner_function",
                    "type": "function",
                    "lineno": 8,
                    "children": [],
                    "args": [],
                    "calls": [
                      {
                        "function": "local_function",
                        "module": null,
                        "lineno": 9,
                        "type": "local"
                      }
                    ]
                  }
                ],
                "args": [
                  "self"
                ]
              }
            ]
          },
          {
            "name": "global_function",
            "type": "function",
            "lineno": 12,
            "children": [
              {
                "name": "InnerClass",
                "type": "class",
                "lineno": 13,
                "children": [
                  {
                    "name": "inner_method",
                    "type": "function",
                    "lineno": 14,
                    "children": [],
                    "args": [
                      "self"
                    ]
                  }
                ]
              }
            ],
            "args": []
          }
        ]
      }
    },
    {
      "module": "backend.app.test.file_example_imported",
      "metadata": "?",
      "tree": {
        "children": [
          {
            "name": "create_class",
            "type": "function",
            "lineno": 1,
            "children": [],
            "args": []
          }
        ]
      }
    }
  ]
}
"""

input_data = {
    "modules": [
        {
            "module": "backend.app.test.file_example",
            "metadata": "?"
        },
        {
            "module": "backend.app.test.file_example_imported",
            "metadata": "?"
        }
    ]
}

class FileProcessor:
    def __init__(self, processed_modules: Dict[str, Any]):
        self.modules = processed_modules
        
    def process_files(self):
        for module in self.modules["modules"]:
            module_name = module["module"]
            filename = f"{module_name.replace('.', '/')}.py"
            file_tree = self._process_file(filename)
            module["tree"] = file_tree
        return json.dumps(self.modules)
    
    def _process_file(self, filepath: str) -> Dict[str, Any]:
        with open(filepath, 'r', encoding='utf-8') as file:
            source_code = file.read()
        
        tree = ast.parse(source_code)
        visitor = FileVisitor(filepath, self.modules)
        visitor.visit(tree)
        
        result = visitor.get_tree()
        
        return result

class FileVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str, available_modules: Set[str]):
        self.tree = {
            "children": []
        }
        self._current_path = [self.tree]
        self.imports = set()
        self.available_modules = available_modules

    def _get_current_node(self) -> Dict[str, Any]:
        return self._current_path[-1]

    def _add_child(self, node_data: Dict[str, Any]):
        current_node = self._get_current_node()
        if "children" not in current_node:
            current_node["children"] = []
        current_node["children"].append(node_data)
        return node_data

    def _add_call(self, call_data: Dict[str, Any]):
        current_node = self._get_current_node()
        if "calls" not in current_node:
            current_node["calls"] = []
        current_node["calls"].append(call_data)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_node = self._add_child({
            "name": node.name,
            "type": "class",
            "lineno": node.lineno,
            "children": []
        })
        
        # decorators
        if node.decorator_list:
            class_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        self._current_path.append(class_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        function_node = self._add_child({
            "name": node.name,
            "type": "function",
            "lineno": node.lineno,
            "children": []
        })
        
        # decorators
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        # arguments
        function_node["args"] = self._parse_arguments(node.args)
        
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        function_node = self._add_child({
            "name": node.name,
            "type": "function",
            "lineno": node.lineno,
            "async": True,
            "children": []
        })
        
        # decorators
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        # arguments
        function_node["args"] = self._parse_arguments(node.args)
        
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module_name = node.module
        for alias in node.names:
            full_name = f"{module_name}.{alias.name}" if module_name else alias.name
            self.imports.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        call_info = self._analyze_call(node)
        if call_info:
            self._add_call(call_info)
        
        self.generic_visit(node)

    def _analyze_call(self, node: ast.Call) -> Dict[str, Any]:
        if isinstance(node.func, ast.Name):
            # oridinary function call
            function_name = node.func.id
            return self._check_local_call(function_name, node.lineno)
        elif isinstance(node.func, ast.Attribute):
            # function call via modules (e.g. ab.cd.foo())
            return self._check_attribute_call(node.func, node.lineno)
        
        return None

    def _check_local_call(self, function_name: str, lineno: int) -> Dict[str, Any]:
        return {
            "function": function_name,
            "module": None,
            "lineno": lineno,
            "type": "local"
        }

    def _check_attribute_call(self, node: ast.Attribute, lineno: int) -> Dict[str, Any]:
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        parts.reverse()
        
        if isinstance(current, ast.Name):
            base_name = current.id
            full_function_name = ".".join([base_name] + parts)
            
            if base_name in self.imports: # and base_name in self.available_modules
                    return {
                        "function": full_function_name,
                        "module": base_name,
                        "lineno": lineno,
                        "type": "internal"
                    }
        
        return None

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return "unknown_decorator"

    def _parse_arguments(self, args: ast.arguments) -> Dict[str, Any]:
        arguments = [arg.arg for arg in args.args]        
        return arguments

    def get_tree(self) -> Dict[str, Any]:
        return self.tree
