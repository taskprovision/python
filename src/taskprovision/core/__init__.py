"""
TaskProvision Core Module

This package contains the core functionality of the TaskProvision platform,
including code generation, quality assurance, task management, and AI analysis.
"""

# Import and expose main components
from .code_generator import CodeGenerator, CodeGenerationRequest, CodeGenerationResult
from .quality_guard import QualityGuard, QualityIssue, QualityLevel
from .task_manager import TaskManager, Task, TaskStatus, TaskPriority, TaskDependency
from .ai_analyzer import AIAnalyzer, AnalysisType, AnalysisResult

__all__ = [
    # Code Generation
    'CodeGenerator',
    'CodeGenerationRequest',
    'CodeGenerationResult',
    
    # Quality Assurance
    'QualityGuard',
    'QualityIssue',
    'QualityLevel',
    
    # Task Management
    'TaskManager',
    'Task',
    'TaskStatus',
    'TaskPriority',
    'TaskDependency',
    
    # AI Analysis
    'AIAnalyzer',
    'AnalysisType',
    'AnalysisResult',
]
