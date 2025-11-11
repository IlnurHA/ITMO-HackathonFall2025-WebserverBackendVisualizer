#!/usr/bin/env python3
"""
Универсальный анализатор зависимостей Python проектов с поддержкой FastAPI эндпоинтов

Использование:
    python dep_analyzer.py [папка_проекта] [опции]

Примеры:
    python dep_analyzer.py ./myproject
    python dep_analyzer.py ./src --include-external --exclude tests,venv
    python dep_analyzer.py ./backend --output-format json,dot --analyze-fastapi
"""

import os
import ast
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set, Tuple

# Импорт FastAPI анализатора (если доступен)
try:
    from fastapi_analyzer import FastAPIEndpointAnalyzer
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("ℹ️  Модуль fastapi_analyzer не найден. Анализ FastAPI эндпоинтов недоступен.")
    print("💡 Чтобы включить анализ FastAPI, создайте файл fastapi_analyzer.py рядом с этим скриптом.")

def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(description='Универсальный анализатор зависимостей Python проектов')
    parser.add_argument('project_path', type=str, nargs='?', default='.',
                        help='Путь к анализируемому проекту (по умолчанию: текущая директория)')
    parser.add_argument('--output', type=str, default='dependencies',
                        help='Базовое имя выходного файла (по умолчанию: dependencies)')
    parser.add_argument('--output-format', type=str, default='json,dot',
                        help='Форматы вывода через запятую: json, dot, svg (по умолчанию: json,dot)')
    parser.add_argument('--include-external', action='store_true',
                        help='Включить внешние зависимости (из site-packages)')
    parser.add_argument('--exclude', type=str, default='tests,venv,.venv,__pycache__,migrations,alembic,scripts,.git',
                        help='Директории/файлы для исключения через запятую (по умолчанию: tests,venv,.venv,__pycache__,migrations)')
    parser.add_argument('--root-module', type=str, default='',
                        help='Корневой модуль для преобразования путей (опционально)')
    parser.add_argument('--verbose', action='store_true',
                        help='Показывать подробную информацию')
    parser.add_argument('--max-depth', type=int, default=0,
                        help='Максимальная глубина анализа (0 = без ограничений)')
    parser.add_argument('--analyze-fastapi', action='store_true',
                        help='Анализировать FastAPI эндпоинты в проекте')
    parser.add_argument('--fastapi-file-patterns', type=str, default='*api*.py,*router*.py,*endpoint*.py,main.py',
                        help='Шаблоны файлов для поиска FastAPI эндпоинтов (через запятую)')
    
    return parser.parse_args()

def get_project_structure(project_root, root_module='', excluded_dirs=None):
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
    for py_file in project_root.rglob('*.py'):
        # Пропускаем исключенные директории
        rel_path = py_file.relative_to(project_root).as_posix()
        if any(excl in rel_path.split('/') for excl in excluded_dirs):
            continue
        
        # Определяем модульный путь
        module_path = rel_path.replace('.py', '').replace('/', '.')
        
        # Особый случай для __init__.py
        if py_file.name == '__init__.py':
            module_path = '.'.join(module_path.split('.')[:-1])
            if module_path == '':
                continue
        
        # Добавляем корневой модуль, если указан
        if root_module and not module_path.startswith(f"{root_module}."):
            full_module_path = f"{root_module}.{module_path}"
        else:
            full_module_path = module_path
        
        module_to_file[full_module_path] = rel_path
        file_to_module[rel_path] = full_module_path
    
    return module_to_file, file_to_module

def resolve_import_path(import_name, current_module, module_to_file, include_external=False):
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
    possible_prefixes = ['', 'src.', 'app.', 'lib.', 'package.', 'main.']
    for prefix in possible_prefixes:
        full_name = f"{prefix}{import_name}"
        for module_path in module_to_file:
            if module_path == full_name or module_path.startswith(f"{full_name}."):
                return module_to_file[module_path]
    
    # Пытаемся разрешить через текущий модуль (для относительных импортов)
    if current_module:
        current_parts = current_module.split('.')
        for i in range(1, len(current_parts)):
            base = '.'.join(current_parts[:-i])
            candidate = f"{base}.{import_name}"
            for module_path in module_to_file:
                if module_path == candidate or module_path.startswith(f"{candidate}."):
                    return module_to_file[module_path]
    
    # Если разрешение не удалось и разрешены внешние зависимости
    if include_external:
        return import_name  # Возвращаем имя модуля как есть
    
    return None

def analyze_file_dependencies(file_path, module_to_file, file_to_module, include_external=False, max_depth=0):
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
    rel_path = str(file_path.relative_to(file_path.parent.parent)) if len(file_path.parts) > 2 else file_path.name
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        return dependencies
    
    # Определяем текущий модуль
    current_module = file_to_module.get(rel_path)
    if not current_module:
        # Пробуем создать модульное имя из пути
        try:
            module_name = str(file_path.relative_to(file_path.parent.parent)).replace('.py', '').replace('/', '.')
            current_module = module_name
        except:
            current_module = rel_path.replace('.py', '').replace('/', '.')
    
    for node in ast.walk(tree):
        try:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dep_file = resolve_import_path(alias.name, current_module, module_to_file, include_external)
                    if dep_file:
                        dependencies.add(dep_file)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Обработка относительных импортов
                    if node.level > 0 and current_module:
                        current_parts = current_module.split('.')
                        base_parts = current_parts[:-node.level] if node.level < len(current_parts) else []
                        full_module = '.'.join(base_parts + [node.module]) if base_parts else node.module
                    else:
                        full_module = node.module
                    
                    dep_file = resolve_import_path(full_module, current_module, module_to_file, include_external)
                    if dep_file:
                        dependencies.add(dep_file)
        except Exception as e:
            continue
    
    return dependencies

def analyze_project(project_path, include_external=False, excluded_dirs=None, root_module='', max_depth=0):
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
        raise FileNotFoundError(f"Директория {project_root} не существует")
    
    # Получаем структуру проекта
    module_to_file, file_to_module = get_project_structure(project_root, root_module, excluded_dirs)
    
    # Анализируем зависимости
    dependencies = defaultdict(list)
    processed_files = 0
    
    for py_file in project_root.rglob('*.py'):
        # Пропускаем исключенные файлы
        rel_path = py_file.relative_to(project_root).as_posix()
        if any(excl in rel_path.split('/') for excl in excluded_dirs):
            continue
        
        deps = analyze_file_dependencies(py_file, module_to_file, file_to_module, include_external, max_depth)
        processed_files += 1
        
        if deps:
            dependencies[rel_path] = list(deps)
    
    return dict(dependencies)

def analyze_fastapi_endpoints(project_path: Path, file_patterns: List[str]) -> Dict[str, Any]:
    """
    Анализирует FastAPI эндпоинты в проекте
    
    Args:
        project_path: Путь к проекту
        file_patterns: Список шаблонов файлов для анализа
    
    Returns:
        Словарь с результатами анализа
    """
    if not FASTAPI_AVAILABLE:
        return {}
    
    analyzer = FastAPIEndpointAnalyzer()
    return analyzer.analyze_project(project_path, file_patterns)

def generate_dot_file(dependencies, output_file, fastapi_endpoints=None):
    """
    Генерирует DOT файл для визуализации
    
    Args:
        dependencies (dict): Словарь зависимостей
        output_file (str): Имя выходного файла
        fastapi_endpoints (dict): Словарь с FastAPI эндпоинтами (опционально)
    """
    dot_content = [
        'digraph G {',
        '    concentrate=true;',
        '    rankdir=TB;',
        '    node [style=filled, fillcolor="#e8f4f8", fontcolor="#000000", fontname=Helvetica, fontsize=10];',
        '    edge [color="#333333"];',
        ''
    ]
    
    # Собираем все файлы
    all_files = set()
    for file, deps in dependencies.items():
        all_files.add(file)
        for dep in deps:
            all_files.add(dep)
    
    # Добавляем файлы с FastAPI эндпоинтами (если есть)
    if fastapi_endpoints:
        for file_path in fastapi_endpoints.get('endpoints_by_file', {}):
            all_files.add(file_path)
    
    if not all_files:
        dot_content.append('    "Нет зависимостей" [shape=box, fillcolor="#ffcccc"];')
        dot_content.append('}')
    else:
        # Группируем по директориям
        dir_nodes = defaultdict(list)
        for file in all_files:
            dir_path = str(Path(file).parent)
            dir_nodes[dir_path].append(file)
        
        # Создаем кластеры для директорий
        cluster_id = 0
        for dir_path, files in dir_nodes.items():
            if dir_path != '.' and len(files) > 1:
                # Проверяем, есть ли в этой директории FastAPI эндпоинты
                has_endpoints = False
                if fastapi_endpoints:
                    for file in files:
                        if file in fastapi_endpoints.get('endpoints_by_file', {}):
                            has_endpoints = True
                            break
                
                dot_content.append(f'    subgraph cluster_{cluster_id} {{')
                label = f"{dir_path} {'🚀' if has_endpoints else ''}"
                dot_content.append(f'        label="{label}";')
                dot_content.append(f'        style="filled,rounded";')
                dot_content.append(f'        fillcolor="{"#e6f7ff" if has_endpoints else "#f0f7ff"}";')
                dot_content.append(f'        color="{"#4da6ff" if has_endpoints else "#a0c8ff"}";')
                
                for file in files:
                    node_name = re.sub(r'[^a-zA-Z0-9_]', '_', file)
                    
                    # Проверяем, есть ли в файле FastAPI эндпоинты
                    endpoint_count = 0
                    if fastapi_endpoints and file in fastapi_endpoints.get('endpoints_by_file', {}):
                        endpoint_count = len(fastapi_endpoints['endpoints_by_file'][file])
                    
                    label = Path(file).name
                    if endpoint_count > 0:
                        label = f"{label}\\n🚀 {endpoint_count} endpoints"
                        fillcolor = "#d6eaff"
                        shape = "box3d"
                    else:
                        fillcolor = "#e8f4f8"
                        shape = "box"
                    
                    dot_content.append(f'        "{node_name}" [label="{label}", fillcolor="{fillcolor}", shape={shape}];')
                
                dot_content.append('    }')
                cluster_id += 1
            else:
                for file in files:
                    node_name = re.sub(r'[^a-zA-Z0-9_]', '_', file)
                    label = Path(file).name
                    dot_content.append(f'    "{node_name}" [label="{label}"];')
        
        dot_content.append('')
        
        # Добавляем связи
        for file, deps in dependencies.items():
            source_node = re.sub(r'[^a-zA-Z0-9_]', '_', file)
            for dep in deps:
                target_node = re.sub(r'[^a-zA-Z0-9_]', '_', dep)
                dot_content.append(f'    "{source_node}" -> "{target_node}";')
        
        dot_content.append('}')
    
    # Сохраняем DOT файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dot_content))
    
    return output_file

def generate_json_file(dependencies, output_file, fastapi_endpoints=None):
    """
    Генерирует JSON файл с зависимостями и FastAPI эндпоинтами
    
    Args:
        dependencies (dict): Словарь зависимостей
        output_file (str): Имя выходного файла
        fastapi_endpoints (dict): Словарь с FastAPI эндпоинтами (опционально)
    """
    result = {
        'dependencies': dependencies,
        'metadata': {
            'generated_by': 'Universal Python Dependency Analyzer',
            'files_with_dependencies': len(dependencies)
        }
    }
    
    if fastapi_endpoints:
        result['fastapi_endpoints'] = fastapi_endpoints
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return output_file

def generate_svg_from_dot(dot_file, svg_file):
    """
    Генерирует SVG файл из DOT файла с помощью Graphviz
    
    Args:
        dot_file (str): Путь к DOT файлу
        svg_file (str): Путь к SVG файлу
    """
    try:
        import subprocess
        subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file], check=True)
        return True
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
        return False

def main():
    args = parse_arguments()
    
    # Обработка исключений
    excluded_dirs = [d.strip() for d in args.exclude.split(',') if d.strip()]
    
    try:
        print(f"🔍 Анализируем проект: {Path(args.project_path).resolve()}")
        
        # Анализ зависимостей
        dependencies = analyze_project(
            project_path=args.project_path,
            include_external=args.include_external,
            excluded_dirs=excluded_dirs,
            root_module=args.root_module,
            max_depth=args.max_depth
        )
        
        print(f"✅ Найдено {len(dependencies)} файлов с зависимостями")
        
        # Анализ FastAPI эндпоинтов (если запрошено)
        fastapi_endpoints = {}
        if args.analyze_fastapi and FASTAPI_AVAILABLE:
            print("🔍 Анализируем FastAPI эндпоинты...")
            file_patterns = [p.strip() for p in args.fastapi_file_patterns.split(',') if p.strip()]
            fastapi_endpoints = analyze_fastapi_endpoints(Path(args.project_path), file_patterns)
            
            if fastapi_endpoints:
                stats = fastapi_endpoints.get('stats', {})
                print(f"✅ Найдено {stats.get('total_endpoints', 0)} FastAPI эндпоинтов в {stats.get('total_files_analyzed', 0)} файлах")
            else:
                print("ℹ️  FastAPI эндпоинты не найдены")
        elif args.analyze_fastapi and not FASTAPI_AVAILABLE:
            print("⚠️  Анализ FastAPI недоступен. Установите модуль fastapi_analyzer.py")
        
        # Генерация выходных файлов
        output_formats = [fmt.strip() for fmt in args.output_format.split(',') if fmt.strip()]
        
        if 'json' in output_formats:
            generate_json_file(dependencies, f"{args.output}.json", fastapi_endpoints)
        
        if 'dot' in output_formats:
            dot_file = generate_dot_file(dependencies, f"{args.output}.dot", fastapi_endpoints)
            
            # Автоматически генерируем SVG, если указан формат или есть dot
            if 'svg' in output_formats:
                svg_generated = generate_svg_from_dot(dot_file, f"{args.output}.svg")
                if svg_generated:
                    print(f"✅ SVG файл сохранен в {args.output}.svg")
                else:
                    print("⚠️  Не удалось сгенерировать SVG файл")
        
        # Показываем пример зависимостей
        if args.verbose and dependencies:
            print("\n📋 Пример зависимостей:")
            for i, (file, deps_list) in enumerate(dependencies.items()):
                if i >= 3:  # Показываем только первые 3 для краткости
                    break
                print(f"  📄 {file}")
                for dep in deps_list[:2]:  # Первые 2 зависимости
                    print(f"    └── {dep}")
            if len(dependencies) > 3:
                print(f"  ... и ещё {len(dependencies) - 3} файлов")
        
        # Показываем отчет по FastAPI эндпоинтам
        if args.verbose and fastapi_endpoints and FASTAPI_AVAILABLE:
            analyzer = FastAPIEndpointAnalyzer()
            report = analyzer.generate_endpoints_report(fastapi_endpoints)
            print("\n" + report)
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
