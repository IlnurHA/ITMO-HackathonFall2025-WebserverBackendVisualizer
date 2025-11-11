import ast
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path

class FastAPIEndpointAnalyzer:
    """
    Анализатор для обнаружения FastAPI эндпоинтов в Python файлах
    """
    
    def __init__(self):
        # Паттерны для поиска FastAPI декораторов
        self.route_decorators = {
            'get': re.compile(r'@(?:app|router)\.get\((.*?)\)'),
            'post': re.compile(r'@(?:app|router)\.post\((.*?)\)'),
            'put': re.compile(r'@(?:app|router)\.put\((.*?)\)'),
            'delete': re.compile(r'@(?:app|router)\.delete\((.*?)\)'),
            'patch': re.compile(r'@(?:app|router)\.patch\((.*?)\)'),
            'options': re.compile(r'@(?:app|router)\.options\((.*?)\)'),
            'head': re.compile(r'@(?:app|router)\.head\((.*?)\)'),
            'api_route': re.compile(r'@(?:app|router)\.api_route\((.*?)\)'),
        }
        # Паттерны для определения зависимостей
        self.dependency_pattern = re.compile(r'Depends\((.*?)\)')
        self.router_include_pattern = re.compile(r'(?:app|router)\.include_router\((.*?)\)')
    
    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Анализирует файл на наличие FastAPI эндпоинтов
        
        Args:
            file_path: Путь к Python файлу
            
        Returns:
            Список обнаруженных эндпоинтов с их метаданными
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
            
            endpoints = []
            # Поиск декораторов на уровне модуля
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._analyze_function_as_endpoint(node, content)
                    if endpoint:
                        endpoint['file'] = str(file_path)
                        endpoints.append(endpoint)
            
            # Поиск включенных роутеров
            included_routers = self._find_included_routers(tree, content)
            
            # Объединяем результаты
            result = {
                'endpoints': endpoints,
                'included_routers': included_routers,
                'file_path': str(file_path)
            }
            
            return endpoints
            
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            print(f"⚠️ Ошибка при анализе FastAPI эндпоинтов в {file_path}: {e}")
            return []
    
    def _analyze_function_as_endpoint(self, node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """
        Анализирует функцию на предмет наличия FastAPI декораторов
        """
        # Получаем текст функции из исходного кода
        func_text = ast.get_source_segment(content, node)
        if not func_text:
            return None
        
        # Проверяем каждый декоратор
        for decorator in node.decorator_list:
            dec_text = ast.get_source_segment(content, decorator)
            if not dec_text:
                continue
            
            # Проверяем на наличие FastAPI декораторов
            for method, pattern in self.route_decorators.items():
                match = pattern.search(dec_text)
                if match:
                    path = match.group(1).strip('"\'')
                    return self._extract_endpoint_details(
                        node, func_text, method, path, dec_text
                    )
        
        return None
    
    def _extract_endpoint_details(self, node: ast.FunctionDef, func_text: str, 
                                 method: str, path: str, decorator_text: str) -> Dict[str, Any]:
        """
        Извлекает детали эндпоинта
        """
        # Основные параметры
        endpoint = {
            'name': node.name,
            'method': method.upper(),
            'path': path,
            'line_number': node.lineno,
            'summary': self._extract_docstring_summary(node),
            'dependencies': [],
            'parameters': [],
            'response_model': None,
            'status_code': None,
            'tags': [],
            'deprecated': False,
            'decorator_raw': decorator_text.strip()
        }
        
        # Анализируем аргументы декоратора для дополнительной информации
        self._analyze_decorator_arguments(decorator_text, endpoint)
        
        # Анализируем параметры функции
        self._analyze_function_parameters(node, endpoint)
        
        return endpoint
    
    def _analyze_decorator_arguments(self, decorator_text: str, endpoint: Dict[str, Any]):
        """
        Анализирует аргументы декоратора для извлечения дополнительной информации
        """
        # Поиск тегов
        tags_match = re.search(r'tags\s*=\s*(\[[^\]]*\])', decorator_text)
        if tags_match:
            try:
                tags_str = tags_match.group(1)
                # Упрощенный парсинг тегов
                tags = [tag.strip('"\' ') for tag in tags_str.strip('[]').split(',') if tag.strip()]
                endpoint['tags'] = tags
            except:
                pass
        
        # Поиск статус кода
        status_match = re.search(r'status_code\s*=\s*(\d+)', decorator_text)
        if status_match:
            try:
                endpoint['status_code'] = int(status_match.group(1))
            except:
                pass
        
        # Поиск deprecated
        if 'deprecated=True' in decorator_text:
            endpoint['deprecated'] = True
        
        # Поиск response_model
        response_match = re.search(r'response_model\s*=\s*([^,\)]+)', decorator_text)
        if response_match:
            endpoint['response_model'] = response_match.group(1).strip()
    
    def _analyze_function_parameters(self, node: ast.FunctionDef, endpoint: Dict[str, Any]):
        """
        Анализирует параметры функции для поиска зависимостей и путевых параметров
        """
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'annotation': None,
                'default': None,
                'type': 'regular'  # regular, path, dependency
            }
            
            # Аннотация типа
            if arg.annotation:
                try:
                    param_info['annotation'] = ast.unparse(arg.annotation)
                except:
                    param_info['annotation'] = str(arg.annotation)
            
            # Поиск значения по умолчанию
            if node.args.defaults:
                default_idx = len(node.args.args) - len(node.args.defaults) + node.args.args.index(arg)
                if default_idx >= 0 and default_idx < len(node.args.defaults):
                    try:
                        default_val = node.args.defaults[default_idx]
                        param_info['default'] = ast.unparse(default_val)
                        
                        # Проверка на зависимость
                        if isinstance(default_val, ast.Call) and hasattr(default_val.func, 'id'):
                            if default_val.func.id == 'Depends':
                                param_info['type'] = 'dependency'
                                dep_match = self.dependency_pattern.search(param_info['default'])
                                if dep_match:
                                    param_info['dependency_name'] = dep_match.group(1).strip()
                    except:
                        pass
            
            # Проверка на путь параметр (если есть аннотация Path)
            if param_info['annotation'] and 'Path' in param_info['annotation']:
                param_info['type'] = 'path'
            
            endpoint['parameters'].append(param_info)
    
    def _find_included_routers(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """
        Находит включенные роутеры в приложении
        """
        routers = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                try:
                    call_text = ast.get_source_segment(content, node)
                    if call_text and ('.include_router(' in call_text or '.include_router(' in call_text.lower()):
                        # Извлекаем параметры вызова
                        router_match = self.router_include_pattern.search(call_text)
                        if router_match:
                            router_info = {
                                'raw_call': call_text.strip(),
                                'line_number': node.lineno
                            }
                            
                            # Пытаемся извлечь имя роутера
                            router_name = router_match.group(1).split(',')[0].strip()
                            router_info['router_name'] = router_name
                            
                            # Пытаемся извлечь префикс
                            prefix_match = re.search(r'prefix\s*=\s*(.*?)(?:,|\))', call_text)
                            if prefix_match:
                                router_info['prefix'] = prefix_match.group(1).strip('"\'')
                            
                            routers.append(router_info)
                except:
                    continue
        
        return routers
    
    def _extract_docstring_summary(self, node: ast.FunctionDef) -> str:
        """
        Извлекает краткое описание из docstring функции
        """
        if ast.get_docstring(node):
            doc = ast.get_docstring(node)
            # Берем первую строку или первое предложение
            summary = doc.strip().split('\n')[0]
            if len(summary) > 100:
                summary = summary[:97] + '...'
            return summary
        return ''
    
    def analyze_project(self, project_path: Path, file_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Анализирует весь проект на наличие FastAPI эндпоинтов
        
        Args:
            project_path: Корневой путь проекта
            file_patterns: Шаблоны файлов для анализа (например, ['*api*.py', '*router*.py'])
            
        Returns:
            Словарь с результатами анализа
        """
        if file_patterns is None:
            file_patterns = ['*.py']
        
        endpoints_by_file = {}
        all_endpoints = []
        router_includes = []
        
        # Проходим по всем Python файлам
        for pattern in file_patterns:
            for file_path in project_path.rglob(pattern):
                # Пропускаем исключенные файлы
                if any(excl in str(file_path) for excl in ['tests', 'venv', '.venv', '__pycache__', 'migrations']):
                    continue
                
                endpoints = self.analyze_file(file_path)
                if endpoints:
                    rel_path = file_path.relative_to(project_path).as_posix()
                    endpoints_by_file[rel_path] = endpoints
                    all_endpoints.extend(endpoints)
        
        # Собираем статистику
        stats = {
            'total_files_analyzed': len(endpoints_by_file),
            'total_endpoints': len(all_endpoints),
            'endpoints_by_method': {},
            'endpoints_by_tag': {}
        }
        
        # Статистика по HTTP методам
        for endpoint in all_endpoints:
            method = endpoint['method']
            stats['endpoints_by_method'][method] = stats['endpoints_by_method'].get(method, 0) + 1
            
            # Статистика по тегам
            for tag in endpoint.get('tags', []):
                stats['endpoints_by_tag'][tag] = stats['endpoints_by_tag'].get(tag, 0) + 1
        
        result = {
            'endpoints_by_file': endpoints_by_file,
            'all_endpoints': all_endpoints,
            'router_includes': router_includes,
            'stats': stats,
            'project_path': str(project_path)
        }
        
        return result
    
    def generate_endpoints_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        Генерирует отчет об эндпоинтах в текстовом формате
        """
        report_lines = []
        report_lines.append("🔍 FastAPI Endpoints Analysis Report")
        report_lines.append("=" * 50)
        report_lines.append(f"📁 Project: {analysis_result['project_path']}")
        report_lines.append(f"📊 Total files with endpoints: {analysis_result['stats']['total_files_analyzed']}")
        report_lines.append(f"🚀 Total endpoints: {analysis_result['stats']['total_endpoints']}")
        report_lines.append("")
        
        # Статистика по методам
        report_lines.append("📈 Endpoints by HTTP Method:")
        for method, count in analysis_result['stats']['endpoints_by_method'].items():
            report_lines.append(f"  {method}: {count}")
        report_lines.append("")
        
        # Статистика по тегам
        if analysis_result['stats']['endpoints_by_tag']:
            report_lines.append("🏷️ Endpoints by Tag:")
            for tag, count in analysis_result['stats']['endpoints_by_tag'].items():
                report_lines.append(f"  {tag}: {count}")
            report_lines.append("")
        
        # Детали по файлам
        report_lines.append("📂 Endpoints by File:")
        for file_path, endpoints in analysis_result['endpoints_by_file'].items():
            report_lines.append(f"\n📁 {file_path}:")
            for endpoint in endpoints:
                tags = ", ".join(endpoint.get('tags', [])) if endpoint.get('tags') else "no tags"
                report_lines.append(f"  {endpoint['method']} {endpoint['path']} - {endpoint['name']}")
                if endpoint.get('summary'):
                    report_lines.append(f"    📝 {endpoint['summary']}")
                if tags:
                    report_lines.append(f"    🏷️ Tags: {tags}")
                if endpoint.get('dependencies'):
                    deps = ", ".join([d.get('name', '') for d in endpoint['dependencies']])
                    report_lines.append(f"    ⚙️ Dependencies: {deps}")
        
        return "\n".join(report_lines)
    
    def generate_endpoints_json(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует JSON-совместимый отчет об эндпоинтах
        """
        return {
            'summary': {
                'total_files': analysis_result['stats']['total_files_analyzed'],
                'total_endpoints': analysis_result['stats']['total_endpoints'],
                'methods': analysis_result['stats']['endpoints_by_method'],
                'tags': analysis_result['stats']['endpoints_by_tag']
            },
            'files': analysis_result['endpoints_by_file'],
            'all_endpoints': analysis_result['all_endpoints']
        }
