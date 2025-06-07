"""
TaskProvision Quality Guard
Code quality analysis and enforcement
"""

import ast
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class QualityIssue:
    """Represents a code quality issue"""
    type: str
    severity: str
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class QualityReport:
    """Code quality analysis report"""
    score: float
    level: QualityLevel
    issues: List[QualityIssue]
    suggestions: List[str]
    metrics: Dict[str, Any]

class QualityGuard:
    """Code quality analyzer and enforcer"""

    def __init__(self):
        self.python_rules = self._load_python_rules()
        self.general_rules = self._load_general_rules()

    def _load_python_rules(self) -> Dict[str, Any]:
        """Load Python-specific quality rules"""
        return {
            'max_function_length': 50,
            'max_class_length': 300,
            'max_file_length': 1000,
            'max_complexity': 10,
            'max_parameters': 5,
            'max_line_length': 88,
            'require_docstrings': True,
            'require_type_hints': False,
            'forbidden_patterns': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'os\.system\s*\(',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
            ],
            'security_patterns': [
                r'password\s*=\s*["\'][^"\']*["\']',
                r'api_key\s*=\s*["\'][^"\']*["\']',
                r'secret\s*=\s*["\'][^"\']*["\']',
            ]
        }

    def _load_general_rules(self) -> Dict[str, Any]:
        """Load general quality rules for all languages"""
        return {
            'max_line_length': 120,
            'max_file_length': 2000,
            'forbidden_patterns': [
                r'#\s*TODO\b',         # Matches Python-style TODO comments
                r'//\s*TODO\b',        # Matches JavaScript-style TODO comments
                r'#\s*FIXME\b',        # Matches Python-style FIXME comments
                r'//\s*FIXME\b',       # Matches JavaScript-style FIXME comments
                r'console\.log\s*\(',  # For JavaScript
                r'print\s*\(',         # For Python (in production)
                r'debugger;',          # For JavaScript
            ],
            'security_patterns': [
                r'password\s*[:=]\s*["\'][^"\']*["\']',
                r'token\s*[:=]\s*["\'][^"\']*["\']',
            ]
        }

    def analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python code quality"""
        try:
            # Parse AST
            tree = ast.parse(code)

            # Initialize analysis
            issues = []
            metrics = {}

            # Basic metrics
            lines = code.split('\n')
            metrics['total_lines'] = len(lines)
            metrics['non_empty_lines'] = len([line for line in lines if line.strip()])

            # AST analysis
            analyzer = PythonASTAnalyzer(self.python_rules)
            ast_issues, ast_metrics = analyzer.analyze(tree, code)
            issues.extend(ast_issues)
            metrics.update(ast_metrics)

            # Pattern analysis
            pattern_issues = self._check_patterns(code, self.python_rules)
            issues.extend(pattern_issues)

            # Security analysis
            security_issues = self._check_security_patterns(code, self.python_rules)
            issues.extend(security_issues)

            # Calculate score
            score = self._calculate_quality_score(issues, metrics)

            # Generate suggestions
            suggestions = self._generate_suggestions(issues, metrics)

            return {
                'score': score,
                'level': self._get_quality_level(score).value,
                'issues': [self._issue_to_dict(issue) for issue in issues],
                'suggestions': suggestions,
                'metrics': metrics
            }

        except SyntaxError as e:
            return {
                'score': 0,
                'level': QualityLevel.POOR.value,
                'issues': [{'type': 'syntax_error', 'severity': 'critical', 'message': str(e)}],
                'suggestions': ['Fix syntax errors before proceeding'],
                'metrics': {'syntax_error': True}
            }
        except Exception as e:
            logger.error(f"Python code analysis failed: {e}")
            return self._error_result(str(e))

    def analyze_general_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality for any language"""
        try:
            issues = []
            metrics = {}

            # Basic metrics
            lines = code.split('\n')
            metrics['total_lines'] = len(lines)
            metrics['non_empty_lines'] = len([line for line in lines if line.strip()])
            metrics['language'] = language

            # Line length check
            for i, line in enumerate(lines, 1):
                if len(line) > self.general_rules['max_line_length']:
                    issues.append(QualityIssue(
                        type='line_too_long',
                        severity='minor',
                        message=f'Line {i} exceeds maximum length ({len(line)} > {self.general_rules["max_line_length"]})',
                        line=i,
                        suggestion=f'Break line {i} into multiple lines'
                    ))

            # File length check
            if len(lines) > self.general_rules['max_file_length']:
                issues.append(QualityIssue(
                    type='file_too_long',
                    severity='major',
                    message=f'File too long ({len(lines)} > {self.general_rules["max_file_length"]} lines)',
                    suggestion='Consider splitting into smaller files'
                ))

            # Pattern analysis
            pattern_issues = self._check_patterns(code, self.general_rules)
            issues.extend(pattern_issues)

            # Security analysis
            security_issues = self._check_security_patterns(code, self.general_rules)
            issues.extend(security_issues)

            # Language-specific analysis
            if language.lower() == 'javascript':
                js_issues = self._analyze_javascript_specific(code)
                issues.extend(js_issues)
            elif language.lower() == 'typescript':
                ts_issues = self._analyze_typescript_specific(code)
                issues.extend(ts_issues)

            # Calculate score
            score = self._calculate_quality_score(issues, metrics)

            # Generate suggestions
            suggestions = self._generate_suggestions(issues, metrics)

            return {
                'score': score,
                'level': self._get_quality_level(score).value,
                'issues': [self._issue_to_dict(issue) for issue in issues],
                'suggestions': suggestions,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"General code analysis failed: {e}")
            return self._error_result(str(e))

    def _check_patterns(self, code: str, rules: Dict[str, Any]) -> List[QualityIssue]:
        """Check for forbidden patterns"""
        issues = []

        for pattern in rules.get('forbidden_patterns', []):
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(QualityIssue(
                    type='forbidden_pattern',
                    severity='major',
                    message=f'Forbidden pattern found: {match.group()}',
                    line=line_num,
                    suggestion='Remove or replace forbidden pattern'
                ))

        return issues

    def _check_security_patterns(self, code: str, rules: Dict[str, Any]) -> List[QualityIssue]:
        """Check for security vulnerabilities"""
        issues = []

        for pattern in rules.get('security_patterns', []):
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(QualityIssue(
                    type='security_issue',
                    severity='critical',
                    message=f'Potential security issue: hardcoded sensitive data',
                    line=line_num,
                    suggestion='Use environment variables or secure configuration'
                ))

        return issues

    def _analyze_javascript_specific(self, code: str) -> List[QualityIssue]:
        """JavaScript-specific quality checks"""
        issues = []

        # Check for var usage (should use let/const)
        var_matches = re.finditer(r'\bvar\s+', code)
        for match in var_matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append(QualityIssue(
                type='outdated_syntax',
                severity='minor',
                message='Use let/const instead of var',
                line=line_num,
                suggestion='Replace var with let or const'
            ))

        # Check for == usage (should use ===)
        equality_matches = re.finditer(r'[^=!]==(?!=)', code)
        for match in equality_matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append(QualityIssue(
                type='loose_equality',
                severity='minor',
                message='Use strict equality (===) instead of loose equality (==)',
                line=line_num,
                suggestion='Replace == with ==='
            ))

        return issues

    def _analyze_typescript_specific(self, code: str) -> List[QualityIssue]:
        """TypeScript-specific quality checks"""
        issues = []

        # Check for any type usage
        any_matches = re.finditer(r':\s*any\b', code)
        for match in any_matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append(QualityIssue(
                type='weak_typing',
                severity='minor',
                message='Avoid using "any" type',
                line=line_num,
                suggestion='Use specific types instead of any'
            ))

        return issues

    def _calculate_quality_score(self, issues: List[QualityIssue], metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)"""
        base_score = 100.0

        # Deduct points for issues
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 20
            elif issue.severity == 'major':
                base_score -= 10
            elif issue.severity == 'minor':
                base_score -= 3

        # Bonus points for good practices
        if metrics.get('has_docstrings', False):
            base_score += 5

        if metrics.get('has_type_hints', False):
            base_score += 5

        if metrics.get('has_tests', False):
            base_score += 10

        return max(0, min(100, base_score))

    def _get_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR

    def _generate_suggestions(self, issues: List[QualityIssue], metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        # Issue-based suggestions
        issue_types = [issue.type for issue in issues]

        if 'function_too_long' in issue_types:
            suggestions.append('Break down large functions into smaller, focused functions')

        if 'missing_docstring' in issue_types:
            suggestions.append('Add docstrings to all functions and classes')

        if 'security_issue' in issue_types:
            suggestions.append('Move sensitive data to environment variables')

        if 'forbidden_pattern' in issue_types:
            suggestions.append('Replace forbidden patterns with safer alternatives')

        # Metric-based suggestions
        if metrics.get('total_lines', 0) > 500:
            suggestions.append('Consider splitting large files into smaller modules')

        if not metrics.get('has_type_hints', True):
            suggestions.append('Add type hints to improve code clarity and maintainability')

        return suggestions

    def _issue_to_dict(self, issue: QualityIssue) -> Dict[str, Any]:
        """Convert QualityIssue to dictionary"""
        return {
            'type': issue.type,
            'severity': issue.severity,
            'message': issue.message,
            'line': issue.line,
            'suggestion': issue.suggestion
        }

    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            'score': 0,
            'level': QualityLevel.POOR.value,
            'issues': [{'type': 'analysis_error', 'severity': 'critical', 'message': error_message}],
            'suggestions': ['Fix analysis errors and try again'],
            'metrics': {'error': True}
        }

class PythonASTAnalyzer:
    """Python AST-based code analyzer"""

    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules
        self.issues = []
        self.metrics = {}

    def analyze(self, tree: ast.AST, code: str) -> tuple:
        """Analyze Python AST"""
        self.issues = []
        self.metrics = {
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'has_docstrings': False,
            'has_type_hints': False,
            'complexity_total': 0
        }

        # Walk the AST
        for node in ast.walk(tree):
            self._analyze_node(node, code)

        # Calculate averages
        if self.metrics['functions'] > 0:
            self.metrics['avg_complexity'] = self.metrics['complexity_total'] / self.metrics['functions']

        return self.issues, self.metrics

    def _analyze_node(self, node: ast.AST, code: str):
        """Analyze individual AST node"""
        if isinstance(node, ast.FunctionDef):
            self._analyze_function(node, code)
        elif isinstance(node, ast.ClassDef):
            self._analyze_class(node, code)
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            self.metrics['imports'] += 1

    def _analyze_function(self, node: ast.FunctionDef, code: str):
        """Analyze function definition"""
        self.metrics['functions'] += 1

        # Function length check
        if hasattr(node, 'end_lineno') and node.end_lineno:
            func_length = node.end_lineno - node.lineno
            if func_length > self.rules['max_function_length']:
                self.issues.append(QualityIssue(
                    type='function_too_long',
                    severity='major',
                    message=f'Function {node.name} is too long ({func_length} lines)',
                    line=node.lineno,
                    suggestion=f'Break down {node.name} into smaller functions'
                ))

        # Parameter count check
        if len(node.args.args) > self.rules['max_parameters']:
            self.issues.append(QualityIssue(
                type='too_many_parameters',
                severity='minor',
                message=f'Function {node.name} has too many parameters ({len(node.args.args)})',
                line=node.lineno,
                suggestion=f'Reduce parameters in {node.name} or use a configuration object'
            ))

        # Docstring check
        if self.rules['require_docstrings']:
            if not ast.get_docstring(node):
                self.issues.append(QualityIssue(
                    type='missing_docstring',
                    severity='minor',
                    message=f'Function {node.name} missing docstring',
                    line=node.lineno,
                    suggestion=f'Add docstring to {node.name}'
                ))
            else:
                self.metrics['has_docstrings'] = True

        # Type hints check
        if self.rules['require_type_hints']:
            if not node.returns and node.name != '__init__':
                self.issues.append(QualityIssue(
                    type='missing_return_type',
                    severity='minor',
                    message=f'Function {node.name} missing return type annotation',
                    line=node.lineno,
                    suggestion=f'Add return type annotation to {node.name}'
                ))

            for arg in node.args.args:
                if not arg.annotation:
                    self.issues.append(QualityIssue(
                        type='missing_type_hint',
                        severity='minor',
                        message=f'Parameter {arg.arg} in {node.name} missing type annotation',
                        line=node.lineno,
                        suggestion=f'Add type annotation to parameter {arg.arg}'
                    ))

        # Check for type hints presence
        if node.returns or any(arg.annotation for arg in node.args.args):
            self.metrics['has_type_hints'] = True

        # Complexity analysis
        complexity = self._calculate_complexity(node)
        self.metrics['complexity_total'] += complexity

        if complexity > self.rules['max_complexity']:
            self.issues.append(QualityIssue(
                type='high_complexity',
                severity='major',
                message=f'Function {node.name} has high complexity ({complexity})',
                line=node.lineno,
                suggestion=f'Simplify {node.name} by reducing conditional statements'
            ))

    def _analyze_class(self, node: ast.ClassDef, code: str):
        """Analyze class definition"""
        self.metrics['classes'] += 1

        # Class length check (approximate)
        if hasattr(node, 'end_lineno') and node.end_lineno:
            class_length = node.end_lineno - node.lineno
            if class_length > self.rules['max_class_length']:
                self.issues.append(QualityIssue(
                    type='class_too_long',
                    severity='major',
                    message=f'Class {node.name} is too long ({class_length} lines)',
                    line=node.lineno,
                    suggestion=f'Break down {node.name} into smaller classes'
                ))

        # Docstring check
        if self.rules['require_docstrings']:
            if not ast.get_docstring(node):
                self.issues.append(QualityIssue(
                    type='missing_docstring',
                    severity='minor',
                    message=f'Class {node.name} missing docstring',
                    line=node.lineno,
                    suggestion=f'Add docstring to {node.name}'
                ))
            else:
                self.metrics['has_docstrings'] = True

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

# Quality enforcement decorators
def enforce_quality(min_score: float = 80):
    """Decorator to enforce code quality on functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function source
            import inspect
            source = inspect.getsource(func)

            # Analyze quality
            guard = QualityGuard()
            result = guard.analyze_python_code(source)

            if result['score'] < min_score:
                raise RuntimeError(f"Function {func.__name__} does not meet quality standards (score: {result['score']:.1f})")

            return func(*args, **kwargs)
        return wrapper
    return decorator

# CLI interface for quality checking
def check_file_quality(file_path: str) -> Dict[str, Any]:
    """Check quality of a code file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        guard = QualityGuard()

        # Determine language from extension
        if file_path.endswith('.py'):
            result = guard.analyze_python_code(code)
        elif file_path.endswith(('.js', '.jsx')):
            result = guard.analyze_general_code(code, 'javascript')
        elif file_path.endswith(('.ts', '.tsx')):
            result = guard.analyze_general_code(code, 'typescript')
        else:
            result = guard.analyze_general_code(code, 'general')

        result['file_path'] = file_path
        return result

    except Exception as e:
        return {
            'error': str(e),
            'file_path': file_path,
            'score': 0
        }