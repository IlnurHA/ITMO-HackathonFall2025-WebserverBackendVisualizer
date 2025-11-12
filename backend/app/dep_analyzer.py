#!/usr/bin/env python3
"""
Универсальный анализатор зависимостей Python проектов

Использование:
    python dep_analyzer.py [папка_проекта] [опции]

Примеры:
    python dep_analyzer.py ./myproject
    python dep_analyzer.py ./src --include-external --exclude tests,venv
    python dep_analyzer.py ./backend --output-format json,dot
"""

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path

from file_processor import ProjectAnalyzer
import sys


def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description="Универсальный анализатор зависимостей Python проектов"
    )
    parser.add_argument(
        "project_path",
        type=str,
        nargs="?",
        default=".",
        help="Путь к анализируемому проекту (по умолчанию: текущая директория)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dependencies",
        help="Базовое имя выходного файла (по умолчанию: dependencies)",
    )
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Включить внешние зависимости (из site-packages)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="tests,venv,.venv,__pycache__,migrations,alembic,scripts,.git",
        help="Директории/файлы для исключения через запятую (по умолчанию: tests,venv,.venv,__pycache__,migrations)",
    )
    parser.add_argument(
        "--root-module",
        type=str,
        default="",
        help="Корневой модуль для преобразования путей (опционально)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Показывать подробную информацию"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Максимальная глубина анализа (0 = без ограничений)",
    )

    return parser.parse_args()


def get_project_structure(project_root, root_module="", excluded_dirs=None):
    """
    Получает структуру проекта и маппинг модулей на файлы

    Args:
        project_root (Path): Корневая директория проекта
        root_module (str): Корневой модуль (например, 'myproject')
        excluded_dirs (list): Список директорий для исключения

    Returns:
        tuple: (module_to_file, file_to_module) - маппинги модулей и файлов
    """
    if excluded_dirs is None:
        excluded_dirs = []

    project_root = Path(project_root).resolve()
    module_to_file = {}
    file_to_module = {}

    # Проходим по всем .py файлам
    for py_file in project_root.rglob("*.py"):
        # Пропускаем исключенные директории
        rel_path = py_file.relative_to(project_root).as_posix()
        if any(excl in rel_path.split("/") for excl in excluded_dirs):
            continue

        # Определяем модульный путь
        module_path = rel_path.replace(".py", "").replace("/", ".")

        # Особый случай для __init__.py
        if py_file.name == "__init__.py":
            module_path = ".".join(module_path.split(".")[:-1])
            if module_path == "":
                continue

        # Добавляем корневой модуль, если указан
        if root_module and not module_path.startswith(f"{root_module}."):
            full_module_path = f"{root_module}.{module_path}"
        else:
            full_module_path = module_path

        module_to_file[full_module_path] = rel_path
        file_to_module[rel_path] = full_module_path

    return module_to_file, file_to_module


def resolve_import_path(
    import_name, current_module, module_to_file, include_external=False
):
    """
    Разрешает импорты и находит реальный файл

    Args:
        import_name (str): Имя импортируемого модуля
        current_module (str): Текущий модуль (откуда происходит импорт)
        module_to_file (dict): Маппинг модулей на файлы
        include_external (bool): Включать внешние зависимости

    Returns:
        str: Путь к файлу или None, если не найден
    """
    # Проверяем, есть ли модуль в нашем проекте
    for module_path in module_to_file:
        if module_path == import_name or module_path.startswith(f"{import_name}."):
            return module_to_file[module_path]

    # Проверяем варианты с разными префиксами
    possible_prefixes = ["", "src.", "app.", "lib.", "package.", "main."]
    for prefix in possible_prefixes:
        full_name = f"{prefix}{import_name}"
        for module_path in module_to_file:
            if module_path == full_name or module_path.startswith(f"{full_name}."):
                return module_to_file[module_path]

    # Пытаемся разрешить через текущий модуль (для относительных импортов)
    if current_module:
        current_parts = current_module.split(".")
        for i in range(1, len(current_parts)):
            base = ".".join(current_parts[:-i])
            candidate = f"{base}.{import_name}"
            for module_path in module_to_file:
                if module_path == candidate or module_path.startswith(f"{candidate}."):
                    return module_to_file[module_path]

    # Если разрешение не удалось и разрешены внешние зависимости
    if include_external:
        return import_name  # Возвращаем имя модуля как есть

    return None


def analyze_file_dependencies(
    file_path, module_to_file, file_to_module, include_external=False, max_depth=0
):
    """
    Анализирует зависимости одного файла

    Args:
        file_path (Path): Путь к файлу
        module_to_file (dict): Маппинг модулей на файлы
        file_to_module (dict): Маппинг файлов на модули
        include_external (bool): Включать внешние зависимости
        max_depth (int): Максимальная глубина анализа

    Returns:
        set: Множество зависимостей
    """
    dependencies = set()
    rel_path = (
        file_path.relative_to(file_path.parent.parent.parent).as_posix()
        if len(file_path.parts) > 3
        else file_path.name
    )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        return dependencies

    # Определяем текущий модуль
    current_module = file_to_module.get(rel_path)
    if not current_module:
        # Пробуем создать модульное имя из пути
        module_name = (
            str(file_path.relative_to(file_path.parent.parent))
            .replace(".py", "")
            .replace("/", ".")
        )
        current_module = module_name

    for node in ast.walk(tree):
        try:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dep_file = resolve_import_path(
                        alias.name, current_module, module_to_file, include_external
                    )
                    if dep_file:
                        dependencies.add(dep_file)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Обработка относительных импортов
                    if node.level > 0 and current_module:
                        current_parts = current_module.split(".")
                        base_parts = (
                            current_parts[: -node.level]
                            if node.level < len(current_parts)
                            else []
                        )
                        full_module = (
                            ".".join(base_parts + [node.module])
                            if base_parts
                            else node.module
                        )
                    else:
                        full_module = node.module

                    dep_file = resolve_import_path(
                        full_module, current_module, module_to_file, include_external
                    )
                    if dep_file:
                        dependencies.add(dep_file)
        except Exception as e:
            continue

    return dependencies


def analyze_project(
    project_path,
    include_external=False,
    excluded_dirs=None,
    root_module="",
    max_depth=0,
):
    """
    Анализирует зависимости в проекте

    Args:
        project_path (Path): Путь к проекту
        include_external (bool): Включать внешние зависимости
        excluded_dirs (list): Список директорий для исключения
        root_module (str): Корневой модуль
        max_depth (int): Максимальная глубина анализа

    Returns:
        dict: Словарь зависимостей
    """
    if excluded_dirs is None:
        excluded_dirs = []

    project_root = Path(project_path).resolve()
    if not project_root.exists():
        msg = f"Директория {project_root} не существует"
        raise FileNotFoundError(msg)

    print(f"📁 Анализируем проект: {project_root}")

    # Получаем структуру проекта
    module_to_file, file_to_module = get_project_structure(
        project_root, root_module, excluded_dirs
    )

    if not module_to_file:
        print("⚠️  Не найдено Python модулей для анализа")
        return {}

    print(f"📦 Найдено {len(module_to_file)} модулей")

    # Собираем все модули проекта
    modules_list = []
    processed_files = 0

    for py_file in project_root.rglob("*.py"):
        # Пропускаем исключенные файлы
        rel_path = py_file.relative_to(project_root).as_posix()
        if any(excl in rel_path.split("/") for excl in excluded_dirs):
            continue

        # Получаем зависимости для этого файла
        deps = analyze_file_dependencies(
            py_file,
            module_to_file,
            file_to_module,
            include_external,
            max_depth,
        )
        processed_files += 1

        # Преобразуем зависимости в нужный формат
        imports_list = []
        if deps:
            imports_list = list(deps)

        # Добавляем модуль в список
        module_info = {
            "module": rel_path,  # относительный путь к файлу
            "imports": imports_list,  # список импортов (относительных путей)
        }
        modules_list.append(module_info)

    print(f"✅ Обработано {processed_files} файлов")
    print(f"🔗 Найдено {len(modules_list)} модулей с зависимостями")

    # Возвращаем в формате для AST анализатора
    return {"modules": modules_list}


def get_json_dict(  # noqa: D103
    *,
    root_module: str = "",
    project_path: str = ".",
    included_external: bool = False,
    excluded_dirs: str = "tests,venv,.venv,__pycache__,migrations,alembic,scripts,.git",
    max_depth: int = 0,
) -> dict:
    excluded_dirs_list = [d.strip() for d in excluded_dirs.split(",") if d.strip()]
    dependencies = analyze_project(
        project_path=project_path,
        include_external=included_external,
        excluded_dirs=excluded_dirs_list,
        root_module="",
        max_depth=max_depth,
    )
    return ProjectAnalyzer(
        dependencies,
        project_root_dir=project_path,
    ).analyze_and_get_dict()


def _main() -> None:
    args = parse_arguments()

    # Обработка исключений
    try:
        json_value = get_json_dict(
            project_path=args.project_path,
            included_external=args.include_external,
            excluded_dirs=args.exclude,
            root_module=args.root_module,
            max_depth=args.max_depth,
        )
        with open("test.json", "w", encoding="utf-8") as f:  # noqa: PTH123
            json.dump(json_value, f, indent=4, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        print(f"❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback  # noqa: PLC0415

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    _main()
