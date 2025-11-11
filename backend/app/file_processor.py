import ast
import json
from typing import Dict, Any, Set, List

# TODO: process import using *

"""
{
  "modules": [
    {
      "module": "backend/app/test/routing.py",
      "tree": {
        "children": [
          {
            "name": "read_items",
            "type": "handler",
            "lineno": 14,
            "children": [],
            "args": [
              "session",
              "current_user",
              "skip",
              "limit"
            ],
            "calls": [
              {
                "function": "ItemsPublic",
                "module": "backend.app.models",
                "lineno": 41,
                "type": "internal"
              }
            ],
            "http_method": "get",
            "path": "/",
            "decorators": [
              "router.get"
            ]
          },
          {
            "name": "read_item",
            "type": "handler",
            "lineno": 45,
            "children": [],
            "args": [
              "session",
              "current_user",
              "id"
            ],
            "calls": [],
            "http_method": "get",
            "path": "/{id}",
            "decorators": [
              "router.get"
            ]
          },
          {
            "name": "create_item",
            "type": "handler",
            "lineno": 58,
            "children": [],
            "args": [],
            "calls": [
              {
                "function": "model_validate",
                "module": "backend.app.models",
                "lineno": 64,
                "type": "internal"
              }
            ],
            "http_method": "post",
            "path": "/",
            "decorators": [
              "router.post"
            ]
          },
          {
            "name": "update_item",
            "type": "handler",
            "lineno": 72,
            "children": [],
            "args": [],
            "calls": [],
            "http_method": "put",
            "path": "/{id}",
            "decorators": [
              "router.put"
            ]
          },
          {
            "name": "delete_item",
            "type": "handler",
            "lineno": 96,
            "children": [],
            "args": [
              "session",
              "current_user",
              "id"
            ],
            "calls": [
              {
                "function": "Message",
                "module": "backend.app.models",
                "lineno": 109,
                "type": "internal"
              }
            ],
            "http_method": "delete",
            "path": "/{id}",
            "decorators": [
              "router.delete"
            ]
          }
        ]
      }
    },
    {
      "module": "backend/app/test/file_example.py",
      "tree": {
        "children": [
          {
            "name": "local_function",
            "type": "function",
            "lineno": 3,
            "children": [],
            "args": [],
            "calls": []
          },
          {
            "name": "MyClass",
            "type": "class",
            "lineno": 6,
            "children": [
              {
                "name": "__init__",
                "type": "function",
                "lineno": 7,
                "children": [],
                "args": [
                  "self"
                ],
                "calls": [
                  {
                    "function": "create_class",
                    "module": "backend.app.test.file_example_imported",
                    "lineno": 8,
                    "type": "internal"
                  }
                ]
              },
              {
                "name": "outer_method",
                "type": "function",
                "lineno": 10,
                "children": [
                  {
                    "name": "inner_function",
                    "type": "function",
                    "lineno": 11,
                    "children": [],
                    "args": [],
                    "calls": [
                      {
                        "function": "local_function",
                        "module": null,
                        "lineno": 12,
                        "type": "local"
                      }
                    ]
                  }
                ],
                "args": [
                  "self"
                ],
                "calls": []
              }
            ],
            "calls": []
          },
          {
            "name": "global_function",
            "type": "function",
            "lineno": 15,
            "children": [
              {
                "name": "InnerClass",
                "type": "class",
                "lineno": 16,
                "children": [
                  {
                    "name": "inner_method",
                    "type": "function",
                    "lineno": 17,
                    "children": [],
                    "args": [
                      "self"
                    ],
                    "calls": []
                  }
                ],
                "calls": []
              }
            ],
            "args": [],
            "calls": []
          }
        ]
      }
    },
    {
      "module": "backend/app/test/file_example_imported.py",
      "tree": {
        "children": [
          {
            "name": "create_class",
            "type": "function",
            "lineno": 1,
            "children": [],
            "args": [],
            "calls": []
          }
        ]
      }
    },
    {
      "module": "backend/app/models.py",
      "tree": {
        "children": [
          {
            "name": "Service",
            "type": "sql_class",
            "lineno": 8,
            "children": [],
            "calls": [],
            "table_name": "services",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "name",
                "type": "String"
              },
              {
                "name": "type",
                "type": "String"
              },
              {
                "name": "meta",
                "type": "JSON"
              }
            ]
          },
          {
            "name": "File",
            "type": "sql_class",
            "lineno": 15,
            "children": [],
            "calls": [],
            "table_name": "files",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "path",
                "type": "String"
              }
            ]
          },
          {
            "name": "Handler",
            "type": "sql_class",
            "lineno": 20,
            "children": [],
            "calls": [],
            "table_name": "handlers",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "name",
                "type": "String"
              },
              {
                "name": "file_id",
                "type": "Integer"
              },
              {
                "name": "lineno",
                "type": "Integer"
              },
              {
                "name": "meta",
                "type": "JSON"
              },
              {
                "name": "file",
                "type": "unknown"
              }
            ]
          },
          {
            "name": "Endpoint",
            "type": "sql_class",
            "lineno": 29,
            "children": [],
            "calls": [],
            "table_name": "endpoints",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "path",
                "type": "String"
              },
              {
                "name": "method",
                "type": "String"
              },
              {
                "name": "handler_id",
                "type": "Integer"
              },
              {
                "name": "handler",
                "type": "unknown"
              }
            ]
          },
          {
            "name": "CFGNode",
            "type": "sql_class",
            "lineno": 37,
            "children": [],
            "calls": [],
            "table_name": "cfg_nodes",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "handler_id",
                "type": "Integer"
              },
              {
                "name": "label",
                "type": "String"
              },
              {
                "name": "lineno",
                "type": "Integer"
              },
              {
                "name": "meta",
                "type": "JSON"
              },
              {
                "name": "handler",
                "type": "unknown"
              }
            ]
          },
          {
            "name": "CFGEdge",
            "type": "sql_class",
            "lineno": 46,
            "children": [],
            "calls": [],
            "table_name": "cfg_edges",
            "model_fields": [
              {
                "name": "id",
                "type": "Integer"
              },
              {
                "name": "src_id",
                "type": "Integer"
              },
              {
                "name": "dst_id",
                "type": "Integer"
              },
              {
                "name": "label",
                "type": "String"
              }
            ]
          }
        ]
      }
    }
  ]
}
"""

import ast
import json
from typing import Dict, Any, List, Set

class ProjectAnalyzer:
    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = input_data
        self.project_index = {}
        self.modules_data = {}
        self.module_mapping = self._build_module_mapping()
    
    def _build_module_mapping(self) -> Dict[str, str]:
        mapping = {}
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]
            
            module_name = file_path[:-3].replace('/', '.')
            
            mapping[module_name] = module_name
            
            parts = module_name.split(".")
            if parts:
                short_name = parts[-1]
                mapping[short_name] = module_name
            
            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                mapping[prefix] = module_name
                
        return mapping
    
    def _first_pass(self):
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]
            
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()
            
            tree = ast.parse(source_code)
            
            module_name = file_path[:-3].replace('/', '.')
            
            collector = DeclarationCollector(module_name, self.module_mapping)
            collector.visit(tree)
            
            self.modules_data[module_name] = {
                'declarations': collector.get_declarations(),
                'imports': collector.get_imports(),
                'exports': collector.get_exports(),
                'source_tree': tree,
                'filename': file_path,
                'original_path': file_path
            }
            
            self._update_project_index(module_name, collector.get_declarations())
                
    def analyze(self) -> str:
        self._first_pass() # declarations
        self._second_pass() # calls
        return self._generate_output()
    
    def _update_project_index(self, module_name: str, declarations: Dict[str, Any]):
        for name, decl_info in declarations.items():
            full_name = f"{module_name}.{name}"
            self.project_index[full_name] = {
                'module': module_name,
                'name': name,
                'type': decl_info['type'],
                'lineno': decl_info['lineno']
            }
            # short name for searching
            self.project_index[name] = {
                'module': module_name,
                'name': name,
                'type': decl_info['type'],
                'lineno': decl_info['lineno']
            }
    
    def _second_pass(self):
        for module_name, module_data in self.modules_data.items():
            if module_data['source_tree'] is None:
                continue
                
            analyzer = CallAnalyzer(
                module_name=module_name,
                module_data=module_data,
                project_index=self.project_index,
                modules_data=self.modules_data
            )
            analyzer.visit(module_data['source_tree'])
            
            module_data['tree'] = analyzer.get_tree()
    
    def _generate_output(self) -> str:
        output = {"modules": []}
        
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]
            module_name = file_path[:-3].replace('/', '.') if file_path.endswith('.py') else file_path
            
            module_data = self.modules_data.get(module_name, {})
            
            output_module = {
                "module": file_path,
                "tree": module_data.get('tree', {"children": []})
            }
            output["modules"].append(output_module)
        
        return json.dumps(output, indent=2, ensure_ascii=False)


class DeclarationCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, module_mapping: Dict[str, str]):
        self.module_name = module_name
        self.module_mapping = module_mapping
        self.declarations = {}
        self.imports = {}
        self.exports = set()
        self.found_sql_models = set()
    
    def visit_ClassDef(self, node: ast.ClassDef):
        class_type = "class"
        table_name = None
        model_fields = []
        
        for item in node.body:
            if (isinstance(item, ast.Assign) and 
                len(item.targets) == 1 and 
                isinstance(item.targets[0], ast.Name) and 
                item.targets[0].id == "__tablename__"):
                
                class_type = "sql_class"
                table_name = self._get_string_value(item.value)
                break
        
        if class_type == "sql_class":
            model_fields = self._extract_model_fields(node)
        
        self.declarations[node.name] = {
            'type': class_type,
            'lineno': node.lineno,
            'table_name': table_name,
            'model_fields': model_fields
        }
        self.generic_visit(node)
    
    def _get_string_value(self, node: ast.AST) -> str:
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""
    
    def _extract_model_fields(self, node: ast.ClassDef) -> List[Dict[str, Any]]:
        fields = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                field_info = self._parse_assign_field(item)
                if field_info:
                    fields.append(field_info)
        
        return fields
    
    def _parse_assign_field(self, node: ast.Assign) -> Dict[str, Any]:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None
        
        field_name = node.targets[0].id
        
        if field_name.startswith('__'):
            return None
        
        field_info = {
            "name": field_name,
            "type": "unknown"
        }
        
        if node.value and isinstance(node.value, ast.Call):
            field_type = self._get_column_type(node.value)
            if field_type:
                field_info["type"] = field_type
        
        return field_info
      
    def _get_column_type(self, call: ast.Call) -> str:
        if isinstance(call.func, ast.Name) and call.func.id == "Column":
            if call.args and len(call.args) > 0:
                return self._get_type_name(call.args[0])
        
        return "unknown"
    
    def _get_type_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_chain(node)
        elif isinstance(node, ast.Call):
            return self._get_type_name(node.func)
        return "unknown"
    
    def _get_constant_value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        return None
    
    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _get_type_annotation(self, annotation: ast.AST) -> str:
        # get str annotation
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            return self._get_subscript_type(annotation)
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_chain(annotation)
        return "unknown"
    
    def _get_subscript_type(self, node: ast.Subscript) -> str:
        # process generic types
        base = self._get_type_annotation(node.value)
        if isinstance(node.slice, ast.Tuple):
            slices = [self._get_type_annotation(el) for el in node.slice.elts]
            return f"{base}[{', '.join(slices)}]"
        else:
            slice_type = self._get_type_annotation(node.slice)
            return f"{base}[{slice_type}]"
  
    def visit_FunctionDef(self, node: ast.FunctionDef):
        function_type = "function"
        http_method = None
        path = None
        
        for decorator in node.decorator_list:
            method, decorator_path = self._parse_router_decorator(decorator)
            if method:
                function_type = "handler"
                http_method = method
                path = decorator_path or "/"
                break
        
        self.declarations[node.name] = {
            'type': function_type,
            'lineno': node.lineno,
            'async': False,
            'http_method': http_method,
            'path': path
        }
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        function_type = "function"
        http_method = None
        path = None
        
        for decorator in node.decorator_list:
            method, decorator_path = self._parse_router_decorator(decorator)
            if method:
                function_type = "handler"
                http_method = method
                path = decorator_path or "/"
                break
        
        self.declarations[node.name] = {
            'type': function_type,
            'lineno': node.lineno,
            'async': True,
            'http_method': http_method,
            'path': path
        }
        self.generic_visit(node)
        
    def _parse_router_decorator(self, decorator: ast.AST) -> tuple[str, str]:
        method = None
        path = None
        
        if isinstance(decorator, ast.Attribute):
            if (isinstance(decorator.value, ast.Name) and 
                decorator.value.id == "router"):
                method = decorator.attr
                path = "/"
        
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                if (isinstance(decorator.func.value, ast.Name) and 
                    decorator.func.value.id == "router"):
                    method = decorator.func.attr
                    
                    if decorator.args and len(decorator.args) > 0:
                        path = self._get_string_value(decorator.args[0])
                    else:
                        path = "/"
        
        return method, path
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            # form full path
            full_module_path = self._resolve_full_module_path(alias.name)
            self.imports[alias.name] = full_module_path
            if alias.asname:
                self.imports[alias.asname] = full_module_path
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        source_module = node.module or ""
        # form full path
        full_source_path = self._resolve_full_module_path(source_module)
        
        for alias in node.names:
            if alias.name == "*":
                self.imports["*"] = full_source_path
            else:
                imported_name = alias.asname or alias.name
                self.imports[imported_name] = full_source_path
    
    def _resolve_full_module_path(self, module_name: str) -> str:
        if not module_name:
            return ""
        
        if module_name in self.module_mapping:
            return self.module_mapping[module_name]
        
        short_name = module_name.split(".")[-1] if "." in module_name else module_name
        if short_name in self.module_mapping:
            return self.module_mapping[short_name]
        
        return module_name

    def visit_Assign(self, node: ast.Assign):
        # processing __all__ = [...] for exports
        if (isinstance(node.targets[0], ast.Name) and 
            node.targets[0].id == "__all__" and 
            isinstance(node.value, ast.List)):
            
            for element in node.value.elts:
                if isinstance(element, ast.Str):
                    self.exports.add(element.s)
                elif isinstance(element, ast.Constant) and isinstance(element.value, str):
                    self.exports.add(element.value)
    
    def get_declarations(self) -> Dict[str, Any]:
        return self.declarations
    
    def get_imports(self) -> Dict[str, str]:
        return self.imports
    
    def get_exports(self) -> Set[str]:
        return self.exports

class CallAnalyzer(ast.NodeVisitor):
    def __init__(self, module_name: str, module_data: Dict[str, Any], 
                 project_index: Dict[str, Any], modules_data: Dict[str, Any]):
        self.module_name = module_name
        self.module_data = module_data
        self.project_index = project_index
        self.modules_data = modules_data
        
        self.tree = {"children": []}
        self._current_path = [self.tree]
        self._available_names = self._build_available_names()
    
    def _build_available_names(self) -> Dict[str, str]:
        # map of available names
        available = {}
        
        # local declarations
        for name in self.module_data['declarations']:
            available[name] = self.module_name
        
        # imports
        for imported_name, source in self.module_data['imports'].items():
            if imported_name == "*":
                # imports with *
                if source in self.modules_data:
                    source_exports = self.modules_data[source].get('exports', set())
                    source_declarations = self.modules_data[source].get('declarations', {})
                    for export_name in source_exports:
                        if export_name in source_declarations:
                            available[export_name] = source
            else:
                available[imported_name] = source
        
        return available
    
    def _get_current_node(self) -> Dict[str, Any]:
        return self._current_path[-1]
    
    def _add_child(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        current_node = self._get_current_node()
        if "children" not in current_node:
            current_node["children"] = []
        current_node["children"].append(node_data)
        return node_data
    
    def _add_call(self, call_data: Dict[str, Any]):
        current_node = self._get_current_node()
        current_node["calls"].append(call_data)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        class_info = self.module_data['declarations'].get(node.name, {})
        
        class_node = self._add_child({
            "name": node.name,
            "type": class_info.get('type', 'class'),
            "lineno": node.lineno,
            "children": [],
            "calls": []
        })
        
        if class_info.get('type') == 'sql_class':
            if 'table_name' in class_info:
                class_node["table_name"] = class_info['table_name']
            if 'model_fields' in class_info:
                class_node["model_fields"] = class_info['model_fields']
        
        if node.decorator_list:
            class_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        self._current_path.append(class_node)
        self.generic_visit(node)
        self._current_path.pop()
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        func_info = self.module_data['declarations'].get(node.name, {})
        
        function_node = {
            "name": node.name,
            "type": func_info.get('type', 'function'),
            "lineno": node.lineno,
            "children": [],
            "args": self._parse_arguments(node.args),
            "calls": []
        }
        
        if func_info.get('type') == 'handler':
            function_node["http_method"] = func_info.get('http_method')
            function_node["path"] = func_info.get('path')
        
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        self._add_child(function_node)
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        func_info = self.module_data['declarations'].get(node.name, {})
        
        function_node = {
            "name": node.name,
            "type": func_info.get('type', 'function'),
            "lineno": node.lineno,
            "async": True,
            "children": [],
            "args": self._parse_arguments(node.args),
            "calls": []
        }
        
        # Добавляем информацию о handler'е если это handler
        if func_info.get('type') == 'handler':
            function_node["http_method"] = func_info.get('http_method')
            function_node["path"] = func_info.get('path')
        
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
        self._add_child(function_node)
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_Call(self, node: ast.Call):
        call_info = self._analyze_call(node)
        if call_info:
            self._add_call(call_info)
        
        self.generic_visit(node)
    
    def _analyze_call(self, node: ast.Call) -> Dict[str, Any]:
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
            return self._resolve_call(function_name, node.lineno)
            
        elif isinstance(node.func, ast.Attribute):
            return self._analyze_attribute_call(node.func, node.lineno)
        
        return None

    def _resolve_call(self, name: str, lineno: int) -> Dict[str, Any]:
        if name in self._available_names:
            source_module = self._available_names[name]
            
            if source_module in self.modules_data:
                if source_module == self.module_name:
                    return {
                        "function": name,
                        "module": None,
                        "lineno": lineno,
                        "type": "local"
                    }
                else:
                    return {
                        "function": name,
                        "module": source_module,
                        "lineno": lineno,
                        "type": "internal"
                    }
        return None

    def _analyze_attribute_call(self, node: ast.Attribute, lineno: int) -> Dict[str, Any]:
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            base_name = current.id
            function_name = parts[-1] if parts else base_name
            
            if base_name in self._available_names:
                source_module = self._available_names[base_name]
                if source_module in self.modules_data:
                    return {
                        "function": function_name,
                        "module": source_module,
                        "lineno": lineno,
                        "type": "internal"
                    }
            else:
                pass
        
        return None
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            parts = []
            current = decorator
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return "unknown_decorator"
    
    def _parse_arguments(self, args: ast.arguments) -> List[str]:
        arguments = [arg.arg for arg in args.args]
        if args.vararg:
            arguments.append(f"*{args.vararg.arg}")
        if args.kwarg:
            arguments.append(f"**{args.kwarg.arg}")
        return arguments
    
    def get_tree(self) -> Dict[str, Any]:
        return self.tree


if __name__ == "__main__":
    input_data = {
        "modules": [
        {
            "module": "backend/app/test/routing.py",
            "imports": []
        },
        {
            "module": "backend/app/test/file_example.py", 
            "imports": []
        },
        {
            "module": "backend/app/test/file_example_imported.py",
            "imports": []
        },
        {
            "module": "backend/app/models.py",
            "imports": []
        }
      ]
    }
    
    analyzer = ProjectAnalyzer(input_data)
    result = analyzer.analyze()
    print(result)