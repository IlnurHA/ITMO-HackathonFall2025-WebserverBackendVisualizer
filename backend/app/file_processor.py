import ast
import json
from typing import Dict, Any, Set, List

# TODO: process import using *
# TODO: check __tablename__ in class (DB)
# TODO: process handlers

"""
{
  "modules": [
    {
      "module": "abc/bar/foo.py",
    },
    {
      "module": "abc/bar/hoo.py",
    },
    .....
  ]
}

Expecting output: json, e.g.
{
  "modules": [
    {
      "module": "backend.app.test.file_example",
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
      "module": "backend.app.test.file_example_imported",
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
      "module": "backend.app.test.models",
      "tree": {
        "children": [
          {
            "name": "UserBase",
            "type": "sql_class",
            "lineno": 8,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "email",
                "type": "EmailStr",
                "field_attrs": {
                  "unique": true,
                  "index": true,
                  "max_length": 255
                }
              },
              {
                "name": "is_active",
                "type": "bool"
              },
              {
                "name": "is_superuser",
                "type": "bool"
              },
              {
                "name": "full_name",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              }
            ]
          },
          {
            "name": "UserCreate",
            "type": "sql_class",
            "lineno": 16,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "password",
                "type": "str",
                "field_attrs": {
                  "min_length": 8,
                  "max_length": 128
                }
              }
            ]
          },
          {
            "name": "UserRegister",
            "type": "sql_class",
            "lineno": 20,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "email",
                "type": "EmailStr",
                "field_attrs": {
                  "max_length": 255
                }
              },
              {
                "name": "password",
                "type": "str",
                "field_attrs": {
                  "min_length": 8,
                  "max_length": 128
                }
              },
              {
                "name": "full_name",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              }
            ]
          },
          {
            "name": "UserUpdate",
            "type": "sql_class",
            "lineno": 27,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "email",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              },
              {
                "name": "password",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "min_length": 8,
                  "max_length": 128
                }
              }
            ]
          },
          {
            "name": "UserUpdateMe",
            "type": "sql_class",
            "lineno": 32,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "full_name",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              },
              {
                "name": "email",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              }
            ]
          },
          {
            "name": "UpdatePassword",
            "type": "sql_class",
            "lineno": 37,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "current_password",
                "type": "str",
                "field_attrs": {
                  "min_length": 8,
                  "max_length": 128
                }
              },
              {
                "name": "new_password",
                "type": "str",
                "field_attrs": {
                  "min_length": 8,
                  "max_length": 128
                }
              }
            ]
          },
          {
            "name": "User",
            "type": "sql_class",
            "lineno": 43,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "id",
                "type": "uuid.UUID",
                "field_attrs": {
                  "default_factory": null,
                  "primary_key": true
                }
              },
              {
                "name": "hashed_password",
                "type": "str"
              },
              {
                "name": "items",
                "type": "list[unknown]"
              }
            ]
          },
          {
            "name": "UserPublic",
            "type": "sql_class",
            "lineno": 50,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "id",
                "type": "uuid.UUID"
              }
            ]
          },
          {
            "name": "UsersPublic",
            "type": "sql_class",
            "lineno": 54,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "data",
                "type": "list[UserPublic]"
              },
              {
                "name": "count",
                "type": "int"
              }
            ]
          },
          {
            "name": "ItemBase",
            "type": "sql_class",
            "lineno": 60,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "title",
                "type": "str",
                "field_attrs": {
                  "min_length": 1,
                  "max_length": 255
                }
              },
              {
                "name": "description",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "max_length": 255
                }
              }
            ]
          },
          {
            "name": "ItemCreate",
            "type": "sql_class",
            "lineno": 66,
            "children": [],
            "calls": [],
            "model_fields": []
          },
          {
            "name": "ItemUpdate",
            "type": "sql_class",
            "lineno": 71,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "title",
                "type": "unknown",
                "field_attrs": {
                  "default": null,
                  "min_length": 1,
                  "max_length": 255
                }
              }
            ]
          },
          {
            "name": "Item",
            "type": "sql_class",
            "lineno": 76,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "id",
                "type": "uuid.UUID",
                "field_attrs": {
                  "default_factory": null,
                  "primary_key": true
                }
              },
              {
                "name": "owner_id",
                "type": "uuid.UUID",
                "field_attrs": {
                  "foreign_key": "user.id",
                  "nullable": false,
                  "ondelete": "CASCADE"
                }
              },
              {
                "name": "owner",
                "type": "unknown"
              }
            ]
          },
          {
            "name": "ItemPublic",
            "type": "sql_class",
            "lineno": 85,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "id",
                "type": "uuid.UUID"
              },
              {
                "name": "owner_id",
                "type": "uuid.UUID"
              }
            ]
          },
          {
            "name": "ItemsPublic",
            "type": "sql_class",
            "lineno": 90,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "data",
                "type": "list[ItemPublic]"
              },
              {
                "name": "count",
                "type": "int"
              }
            ]
          },
          {
            "name": "Message",
            "type": "sql_class",
            "lineno": 96,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "message",
                "type": "str"
              }
            ]
          },
          {
            "name": "Token",
            "type": "sql_class",
            "lineno": 101,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "access_token",
                "type": "str"
              },
              {
                "name": "token_type",
                "type": "str"
              }
            ]
          },
          {
            "name": "TokenPayload",
            "type": "sql_class",
            "lineno": 107,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "sub",
                "type": "unknown"
              }
            ]
          },
          {
            "name": "NewPassword",
            "type": "sql_class",
            "lineno": 111,
            "children": [],
            "calls": [],
            "model_fields": [
              {
                "name": "token",
                "type": "str"
              },
              {
                "name": "new_password",
                "type": "str",
                "field_attrs": {
                  "min_length": 8,
                  "max_length": 128
                }
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
            full_path = module_info["module"]
            # add full path
            mapping[full_path] = full_path
            # add short path
            parts = full_path.split(".")
            if parts:
                short_name = parts[-1]
                mapping[short_name] = full_path
            # add prefixes
            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                mapping[prefix] = full_path
        return mapping
    
    def _first_pass(self):
        for module_info in self.input_data["modules"]:
            module_name = module_info["module"]
            filename = f"{module_name.replace('.', '/')}.py"
            
            with open(filename, 'r', encoding='utf-8') as file:
                source_code = file.read()
            
            tree = ast.parse(source_code)
            collector = DeclarationCollector(module_name, self.module_mapping)
            collector.visit(tree)
            
            self.modules_data[module_name] = {
                'declarations': collector.get_declarations(),
                'imports': collector.get_imports(),
                'exports': collector.get_exports(),
                'source_tree': tree,
                'filename': filename
            }
            
            # global index
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
            module_name = module_info["module"]
            module_data = self.modules_data.get(module_name, {})
            
            output_module = {
                "module": module_name,
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
        model_fields = []
        
        is_sql_model = False
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name == "SQLModel" or base_name in self.found_sql_models:
                class_type = "sql_class"
                is_sql_model = True
                self.found_sql_models.add(node.name)
                break
        
        for keyword in node.keywords:
            if keyword.arg == 'table' and self._get_keyword_value(keyword) is True:
                class_type = "sql_class"
                is_sql_model = True
                self.found_sql_models.add(node.name)
                break
        
        if is_sql_model:
            model_fields = self._extract_model_fields(node)
        
        self.declarations[node.name] = {
            'type': class_type,  # "class" или "sql_class"
            'lineno': node.lineno,
            'model_fields': model_fields  # поля для SQL-классов
        }
        self.generic_visit(node)
    
    def _extract_model_fields(self, node: ast.ClassDef) -> List[Dict[str, Any]]:
        fields = []
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                field_info = self._parse_ann_assign_field(item)
                if field_info:
                    fields.append(field_info)
            elif isinstance(item, ast.Assign):
                field_info = self._parse_assign_field(item)
                if field_info:
                    fields.append(field_info)
        
        return fields
    
    def _parse_ann_assign_field(self, node: ast.AnnAssign) -> Dict[str, Any]:
        if not isinstance(node.target, ast.Name):
            return None
        
        field_name = node.target.id
        field_type = self._get_type_annotation(node.annotation)
        
        field_info = {
            "name": field_name,
            "type": field_type
        }
        
        if node.value:
            field_attrs = self._analyze_field_value(node.value)
            if field_attrs:
                field_info["field_attrs"] = field_attrs
        
        return field_info

    def _parse_assign_field(self, node: ast.Assign) -> Dict[str, Any]:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None
        
        field_name = node.targets[0].id
        
        field_info = {
            "name": field_name,
            "type": "unknown"
        }
        
        if node.value:
            field_attrs = self._analyze_field_value(node.value)
            if field_attrs:
                field_info["field_attrs"] = field_attrs
        
        return field_info

    def _analyze_field_value(self, value: ast.AST) -> Dict[str, Any]:
        if not isinstance(value, ast.Call):
            return {}
        
        if isinstance(value.func, ast.Name) and value.func.id == "Field":
            field_attrs = {}
            
            for arg in value.args:
                if isinstance(arg, ast.Constant):
                    field_attrs["default"] = arg.value
            
            for keyword in value.keywords:
                if keyword.arg:
                    field_attrs[keyword.arg] = self._get_constant_value(keyword.value)
            
            return field_attrs
        
        return {}
      
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
    
    def _get_constant_value(self, node: ast.AST) -> Any:
        # get constant value
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        return None
    
    def _get_base_name(self, base: ast.AST) -> str:
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return ""
    
    def _get_keyword_value(self, keyword: ast.keyword) -> Any:
        if isinstance(keyword.value, ast.Constant):
            return keyword.value.value
        elif isinstance(keyword.value, ast.NameConstant):
            return keyword.value.value
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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.declarations[node.name] = {
            'type': 'function', 
            'lineno': node.lineno,
            'async': False
        }
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.declarations[node.name] = {
            'type': 'function',
            'lineno': node.lineno, 
            'async': True
        }
        self.generic_visit(node)
    
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
        
        if class_info.get('type') == 'sql_class' and 'model_fields' in class_info:
            class_node["model_fields"] = class_info['model_fields']
        
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
            "children": [],
            "args": self._parse_arguments(node.args),
            "calls": []
        })
        
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
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
        
        if node.decorator_list:
            function_node["decorators"] = [self._get_decorator_name(decorator) for decorator in node.decorator_list]
        
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


# Обновленный usage
if __name__ == "__main__":
    input_data = {
        "modules": [
            {
                "module": "backend.app.test.file_example",
            },
            {
                "module": "backend.app.test.file_example_imported",
            },
            {
                "module": "backend.app.test.models",
            }
        ]
    }
    
    analyzer = ProjectAnalyzer(input_data)
    result = analyzer.analyze()
    print(result)