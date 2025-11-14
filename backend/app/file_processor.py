import ast  # noqa: D100
import json
import app.cfg_visitor as cfg_visitor
from typing import Any, Literal

# TODO: process import using *
# TODO: check __tablename__ in class (DB)
# TODO: process handlers


class ProjectAnalyzer:
    def __init__(
        self,
        input_data: dict[Literal["module", "imports"], str],
        project_root_dir: str,
    ):
        self.input_data = input_data
        self.project_root_dir = project_root_dir
        self.project_index = {}
        self.modules_data = {}
        self.module_mapping = self._build_module_mapping()

    def _build_module_mapping(self) -> dict[str, str]:
        mapping = {}
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]

            module_name = file_path[:-3].replace(
                "/",
                ".",
            )  # Remove file extension and format as modules

            mapping[module_name] = module_name

            parts = module_name.split(".")
            if parts:
                short_name = parts[-1]
                mapping[short_name] = module_name

            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                mapping[prefix] = module_name

        return mapping

    def _first_pass(self) -> None:
        analyzing_dir = self.project_root_dir
        for module_info in self.input_data["modules"]:
            file_path = analyzing_dir + "/" + module_info["module"]
            print(f"{file_path=}")

            with open(file_path, encoding="utf-8") as file:  # noqa: FURB101, PTH123
                source_code = file.read()

            tree = ast.parse(source_code)
            module_name = file_path

            collector = DeclarationCollector(module_name, self.module_mapping)
            collector.visit(tree)

            self.modules_data[module_name] = {
                "declarations": collector.get_declarations(),
                "imports": collector.get_imports(),
                "exports": collector.get_exports(),
                "source_tree": tree,
                "filename": file_path,
                "original_path": file_path,
            }

            self._update_project_index(module_name, collector.get_declarations())

    def analyze(self) -> str:  # noqa: D102
        self._first_pass()  # declarations
        self._second_pass()  # calls
        return self._generate_output()

    def analyze_and_get_dict(self) -> dict:  # noqa: D102
        self._first_pass()  # declarations
        self._second_pass()  # calls
        output = {"modules": []}
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]
            module_name = self.project_root_dir + "/" + file_path
            module_data = self.modules_data.get(module_name, {})
            output_module = dict(module_info)
            output_module.update({"tree": module_data.get("tree", {"children": []})})
            output["modules"].append(output_module)
        return output

    def _update_project_index(
        self,
        module_name: str,
        declarations: dict[str, Any],
    ) -> None:
        for name, decl_info in declarations.items():
            full_name = f"{module_name}.{name}"
            self.project_index[full_name] = {
                "module": module_name,
                "name": name,
                "type": decl_info["type"],
                "lineno": decl_info["lineno"],
            }
            # short name for searching
            self.project_index[name] = {
                "module": module_name,
                "name": name,
                "type": decl_info["type"],
                "lineno": decl_info["lineno"],
            }

    def _second_pass(self) -> None:
        for module_name, module_data in self.modules_data.items():
            if module_data["source_tree"] is None:
                continue

            analyzer = CallAnalyzer(
                module_name=module_name,
                module_data=module_data,
                project_index=self.project_index,
                modules_data=self.modules_data,
            )
            analyzer.visit(module_data["source_tree"])

            module_data["tree"] = analyzer.get_tree()

    def _generate_output(self) -> str:
        output = {"modules": []}
        for module_info in self.input_data["modules"]:
            file_path = module_info["module"]
            module_name = self.project_root_dir + "/" + file_path
            module_data = self.modules_data.get(module_name, {})
            output_module = dict(module_info)
            output_module.update({"tree": module_data.get("tree", {"children": []})})
            output["modules"].append(output_module)
        return json.dumps(output, indent=2, ensure_ascii=False)


class DeclarationCollector(ast.NodeVisitor):
    def __init__(
        self,
        module_name: str,
        module_mapping: dict[str, str],
    ) -> "DeclarationCollector":
        self.module_name = module_name
        self.module_mapping = module_mapping
        self.declarations = {}
        self.imports = {}
        self.exports = set()
        self.found_sql_models = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_type = "class"
        model_fields = []
        table_name = "None"

        for item in node.body:
            if (
                isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and item.targets[0].id == "__tablename__"
            ):
                class_type = "sql_class"
                self.found_sql_models.add(node.name)
                table_name = item.value.value
                break

        if class_type == "sql_class":
            model_fields = self._extract_model_fields(node)

        self.declarations[node.name] = {
            "type": class_type,
            "lineno": node.lineno,
            "table_name": table_name,
            "model_fields": model_fields,
        }
        self.generic_visit(node)

    def _get_string_value(self, node: ast.AST) -> str:  # noqa: PLR6301
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def _extract_model_fields(self, node: ast.ClassDef) -> list[dict[str, Any]]:
        fields = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                field_info = self._parse_assign_field(item)
                if field_info:
                    fields.append(field_info)

        return fields

    def _parse_assign_field(self, node: ast.Assign) -> dict[str, Any]:
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None

        field_name = node.targets[0].id

        if field_name.startswith("__"):
            return None

        field_info = {"name": field_name, "type": "unknown"}

        if node.value and isinstance(node.value, ast.Call):
            field_type = self._get_column_type(node.value)
            if field_type:
                field_info["type"] = field_type

        return field_info

    def _get_column_type(self, call: ast.Call) -> str:
        if (
            isinstance(call.func, ast.Name)
            and call.func.id == "Column"
            and call.args
            and len(call.args) > 0
        ):
            return self._get_type_name(call.args[0])

        return "unknown"

    def _get_type_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._get_attribute_chain(node)
        if isinstance(node, ast.Call):
            return self._get_type_name(node.func)
        return "unknown"

    def _get_constant_value(self, node: ast.AST) -> Any:  # noqa: ANN401, PLR6301
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.NameConstant):
            return node.value
        if isinstance(node, ast.Name):
            return node.id
        return None

    def _get_attribute_chain(self, node: ast.Attribute) -> str:  # noqa: PLR6301
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _analyze_field_value(self, value: ast.AST) -> dict[str, Any]:
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
        if isinstance(annotation, ast.Subscript):
            return self._get_subscript_type(annotation)
        if isinstance(annotation, ast.Attribute):
            return self._get_attribute_chain(annotation)
        return "unknown"

    def _get_subscript_type(self, node: ast.Subscript) -> str:
        # process generic types
        base = self._get_type_annotation(node.value)
        if isinstance(node.slice, ast.Tuple):
            slices = [self._get_type_annotation(el) for el in node.slice.elts]
            return f"{base}[{', '.join(slices)}]"
        slice_type = self._get_type_annotation(node.slice)
        return f"{base}[{slice_type}]"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
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
            "type": function_type,
            "lineno": node.lineno,
            "async": False,
            "http_method": http_method,
            "path": path,
        }
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
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
            "type": function_type,
            "lineno": node.lineno,
            "async": True,
            "http_method": http_method,
            "path": path,
        }
        self.generic_visit(node)

    def _parse_router_decorator(self, decorator: ast.AST) -> tuple[str, str]:
        method = None
        path = None

        if isinstance(decorator, ast.Attribute):
            if isinstance(decorator.value, ast.Name) and decorator.value.id == "router":
                method = decorator.attr
                path = "/"

        elif (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "router"
        ):
            method = decorator.func.attr

            if decorator.args and len(decorator.args) > 0:
                path = self._get_string_value(decorator.args[0])
            else:
                path = "/"

        return method, path

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            # form full path
            full_module_path = self._resolve_full_module_path(alias.name)
            self.imports[alias.name] = full_module_path
            if alias.asname:
                self.imports[alias.asname] = full_module_path

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
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

        short_name = (
            module_name.rsplit(".", maxsplit=1)[-1]
            if "." in module_name
            else module_name
        )
        if short_name in self.module_mapping:
            return self.module_mapping[short_name]

        return module_name

    def visit_Assign(self, node: ast.Assign) -> None:
        # processing __all__ = [...] for exports
        if (
            isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            for element in node.value.elts:
                if isinstance(element, ast.Str):
                    self.exports.add(element.s)
                elif isinstance(element, ast.Constant) and isinstance(
                    element.value,
                    str,
                ):
                    self.exports.add(element.value)

    def get_declarations(self) -> dict[str, Any]:
        return self.declarations

    def get_imports(self) -> dict[str, str]:
        return self.imports

    def get_exports(self) -> set[str]:
        return self.exports


class CallAnalyzer(ast.NodeVisitor):
    def __init__(
        self,
        module_name: str,
        module_data: dict[str, Any],
        project_index: dict[str, Any],
        modules_data: dict[str, Any],
    ):
        self.module_name = module_name
        self.module_data = module_data
        self.project_index = project_index
        self.modules_data = modules_data

        self.tree = {"children": []}
        self._current_path = [self.tree]
        self._available_names = self._build_available_names()

    def _build_available_names(self) -> dict[str, str]:
        # map of available names
        available = {}

        # local declarations
        for name in self.module_data["declarations"]:
            available[name] = self.module_name

        # imports  # noqa: ERA001
        for imported_name, source in self.module_data["imports"].items():
            if imported_name == "*":
                # imports with *
                if source in self.modules_data:
                    source_exports = self.modules_data[source].get("exports", set())
                    source_declarations = self.modules_data[source].get(
                        "declarations",
                        {},
                    )
                    for export_name in source_exports:
                        if export_name in source_declarations:
                            available[export_name] = source
            else:
                available[imported_name] = source

        return available

    def _get_current_node(self) -> dict[str, Any]:
        return self._current_path[-1]

    def _add_child(self, node_data: dict[str, Any]) -> dict[str, Any]:
        current_node = self._get_current_node()
        if "children" not in current_node:
            current_node["children"] = []
        current_node["children"].append(node_data)
        return node_data

    def _add_call(self, call_data: dict[str, Any]) -> None:
        current_node = self._get_current_node()
        current_node["calls"].append(call_data)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_info = self.module_data["declarations"].get(node.name, {})

        class_node = self._add_child(
            {
                "name": node.name,
                "type": class_info.get("type", "class"),
                "lineno": node.lineno,
                "children": [],
                "calls": [],
            },
        )

        if class_info.get("type") == "sql_class":
            if "table_name" in class_info:
                class_node["table_name"] = class_info["table_name"]
            if "model_fields" in class_info:
                class_node["model_fields"] = class_info["model_fields"]

        if node.decorator_list:
            class_node["decorators"] = [
                self._get_decorator_name(decorator) for decorator in node.decorator_list
            ]

        self._current_path.append(class_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: D102
        func_info = self.module_data["declarations"].get(node.name, {})

        function_node = {
            "name": node.name,
            "type": func_info.get("type", "function"),
            "lineno": node.lineno,
            "children": [],
            "args": self._parse_arguments(node.args),
            "calls": [],
        }

        file_path = self.module_data.get("filename")
        cfg_json = cfg_visitor.generate_cfg_from_file(file_path, node.name)
        function_node["cfg"] = json.loads(cfg_json)


        if func_info.get("type") == "handler":
            function_node["http_method"] = func_info.get("http_method")
            function_node["path"] = func_info.get("path")

        if node.decorator_list:
            function_node["decorators"] = [
                self._get_decorator_name(decorator) for decorator in node.decorator_list
            ]

        self._add_child(function_node)
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: D102
        func_info = self.module_data["declarations"].get(node.name, {})

        function_node = {
            "name": node.name,
            "type": func_info.get("type", "function"),
            "lineno": node.lineno,
            "async": True,
            "children": [],
            "args": self._parse_arguments(node.args),
            "calls": [],
        }

        file_path = self.module_data.get("filename")
        cfg_json = cfg_visitor.generate_cfg_from_file(file_path, node.name)
        function_node["cfg"] = json.loads(cfg_json)

        # Добавляем информацию о handler'е если это handler  # noqa: RUF003
        if func_info.get("type") == "handler":
            function_node["http_method"] = func_info.get("http_method")
            function_node["path"] = func_info.get("path")

        if node.decorator_list:
            function_node["decorators"] = [
                self._get_decorator_name(decorator) for decorator in node.decorator_list
            ]

        self._add_child(function_node)
        self._current_path.append(function_node)
        self.generic_visit(node)
        self._current_path.pop()

    def visit_Call(self, node: ast.Call) -> None:
        call_info = self._analyze_call(node)
        try:
            if call_info:
                self._add_call(call_info)
        except Exception as _e:  # noqa: BLE001, S110
            pass

        self.generic_visit(node)

    def _analyze_call(self, node: ast.Call) -> dict[str, Any]:
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
            return self._resolve_call(function_name, node.lineno)

        if isinstance(node.func, ast.Attribute):
            return self._analyze_attribute_call(node.func, node.lineno)

        return None

    def _resolve_call(self, name: str, lineno: int) -> dict[str, Any]:
        if name in self._available_names:
            source_module = self._available_names[name]

            if source_module in self.modules_data:
                if source_module == self.module_name:
                    return {
                        "function": name,
                        "module": None,
                        "lineno": lineno,
                        "type": "local",
                    }
                return {
                    "function": name,
                    "module": source_module,
                    "lineno": lineno,
                    "type": "internal",
                }
        return None

    def _analyze_attribute_call(
        self,
        node: ast.Attribute,
        lineno: int,
    ) -> dict[str, Any]:
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
                        "type": "internal",
                    }

        return None

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Attribute):
            parts = []
            current = decorator
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        if isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown_decorator"

    def _parse_arguments(self, args: ast.arguments) -> list[str]:  # noqa: PLR6301
        arguments = [arg.arg for arg in args.args]
        if args.vararg:
            arguments.append(f"*{args.vararg.arg}")
        if args.kwarg:
            arguments.append(f"**{args.kwarg.arg}")
        return arguments

    def get_tree(self) -> dict[str, Any]:  # noqa: D102
        return self.tree


# Обновленный usage
if __name__ == "__main__":
    input_data = {
        "modules": [
            {"module": "app/test/routing.py", "imports": []},
            {"module": "app/test/file_example.py", "imports": []},
            {"module": "app/test/file_example_imported.py", "imports": []},
            {"module": "app/test/another_backend/domain/models_sqlalchemy.py", "imports": []},
        ],
    }

    analyzer = ProjectAnalyzer(input_data, ".")
    result = analyzer.analyze()
    print(result)