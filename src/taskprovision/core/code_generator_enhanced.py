"""
Enhanced Code Generator Module

This module provides an enhanced version of the CodeGenerator class with improved
error handling, validation, and logging.
"""

import asyncio
import re
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from ..services.ollama_service import OllamaService
from .quality_guard import QualityGuard

logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    """Supported programming languages for code generation."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    BASH = "bash"
    SQL = "sql"

@dataclass
class CodeGenerationRequest:
    """Code generation request parameters."""
    description: str
    language: CodeLanguage
    context: Optional[str] = None
    existing_code: Optional[str] = None
    requirements: List[str] = None
    style_preferences: Dict[str, Any] = None
    max_length: int = 1000

@dataclass
class CodeGenerationResult:
    """Code generation result container."""
    generated_code: str
    language: CodeLanguage
    quality_score: float
    suggestions: List[str]
    tests: Optional[str] = None
    documentation: Optional[str] = None
    execution_time: float = 0.0
    iterations: int = 1

class EnhancedCodeGenerator:
    """Enhanced AI-powered code generator with quality assurance.
    
    This class provides an improved version of the original CodeGenerator with:
    - Better error handling and validation
    - Enhanced logging
    - More robust code improvement
    - Better type hints and documentation
    """
    
    def __init__(self, ollama_service: OllamaService):
        """Initialize the EnhancedCodeGenerator.
        
        Args:
            ollama_service: An instance of OllamaService for LLM interactions
        """
        self.ollama = ollama_service
        self.quality_guard = QualityGuard()
        
        # Initialize language-specific prompts
        self.language_prompts = {
            CodeLanguage.PYTHON: self._get_python_prompt(),
            CodeLanguage.JAVASCRIPT: self._get_javascript_prompt(),
            CodeLanguage.TYPESCRIPT: self._get_typescript_prompt(),
            CodeLanguage.GO: self._get_go_prompt(),
            CodeLanguage.RUST: self._get_rust_prompt(),
            CodeLanguage.BASH: self._get_bash_prompt(),
            CodeLanguage.SQL: self._get_sql_prompt(),
        }
    
    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResult:
        """Generate code based on request with enhanced error handling.
        
        Args:
            request: CodeGenerationRequest containing generation parameters
            
        Returns:
            CodeGenerationResult with the generated code and quality metrics
            
        Raises:
            ValueError: If request validation fails
            RuntimeError: If code generation fails after maximum retries
        """
        import time
        start_time = time.time()
        
        # Input validation
        if not request or not isinstance(request, CodeGenerationRequest):
            raise ValueError("Request must be a valid CodeGenerationRequest instance")
            
        if not request.description or not request.description.strip():
            raise ValueError("Description cannot be empty")
            
        if not isinstance(request.language, CodeLanguage):
            raise ValueError(f"Invalid language: {request.language}. Must be a CodeLanguage enum value")
            
        if request.max_length <= 0:
            raise ValueError(f"max_length must be positive, got {request.max_length}")
            
        logger.info(f"Generating {request.language.value} code for: {request.description[:100]}...")
        
        try:
            # Build prompt
            prompt = self._build_prompt(request)
            
            # Generate initial code with retry logic
            try:
                generated_code = await self._generate_initial_code(prompt)
            except Exception as e:
                raise RuntimeError(f"Failed to generate initial code: {str(e)}") from e
            
            # Quality check and improvement
            try:
                quality_result = await self._improve_code_quality(
                    generated_code, 
                    request.language, 
                    max_iterations=3
                )
            except Exception as e:
                logger.warning(f"Code quality improvement failed, using initial code: {str(e)}")
                quality_result = {
                    'code': generated_code,
                    'score': 0.7,  # Default score for unimproved code
                    'suggestions': ["Quality improvement step was skipped"],
                    'iterations': 0
                }
            
            # Generate tests if Python
            tests = None
            if request.language == CodeLanguage.PYTHON:
                try:
                    tests = await self._generate_tests(quality_result['code'])
                except Exception as e:
                    logger.warning(f"Test generation failed: {str(e)}")
            
            # Generate documentation
            try:
                documentation = await self._generate_documentation(
                    quality_result['code'], 
                    request.language
                )
            except Exception as e:
                logger.warning(f"Documentation generation failed: {str(e)}")
                documentation = "Documentation generation failed"
            
            execution_time = time.time() - start_time
            
            result = CodeGenerationResult(
                generated_code=quality_result['code'],
                language=request.language,
                quality_score=quality_result['score'],
                suggestions=quality_result['suggestions'],
                tests=tests,
                documentation=documentation,
                execution_time=execution_time,
                iterations=quality_result['iterations']
            )
            
            logger.info(f"Successfully generated {request.language.value} code in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Code generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    async def _improve_code_quality(self, code: str, language: CodeLanguage, max_iterations: int = 3) -> Dict:
        """Improve code quality through iterations with validation and error handling.
        
        Args:
            code: The initial code to improve
            language: The programming language of the code
            max_iterations: Maximum number of improvement iterations (default: 3)
            
        Returns:
            Dict containing:
                - code: The improved code
                - score: Quality score (0.0-1.0)
                - suggestions: List of improvement suggestions
                - iterations: Number of iterations performed
                
        Raises:
            ValueError: If input validation fails
            RuntimeError: If quality improvement fails
        """
        # Input validation
        if not code or not isinstance(code, str):
            raise ValueError("Code must be a non-empty string")
            
        if not isinstance(language, CodeLanguage):
            raise ValueError(f"Invalid language: {language}. Must be a CodeLanguage enum value")
            
        if max_iterations < 1:
            raise ValueError(f"max_iterations must be at least 1, got {max_iterations}")
            
        logger.debug(f"Starting code quality improvement for {language.value} code ({len(code)} chars)")
        
        current_code = code
        iterations = 0
        best_score = 0.0
        best_code = code
        suggestions = []
        
        try:
            for iteration in range(max_iterations):
                iterations += 1
                logger.debug(f"Quality improvement iteration {iteration}/{max_iterations}")
                
                # Analyze code quality
                try:
                    if language == CodeLanguage.PYTHON:
                        quality_result = self.quality_guard.analyze_python_code(current_code)
                    else:
                        quality_result = self.quality_guard.analyze_general_code(current_code, language.value)
                    
                    score = quality_result.get('score', 0.0)
                    issues = quality_result.get('issues', [])
                    
                    # Update best if improved
                    if score > best_score:
                        best_score = score
                        best_code = current_code
                        suggestions = quality_result.get('suggestions', [])
                        logger.debug(f"New best score: {best_score:.2f}")
                    
                    # If quality is good enough, stop
                    if score >= 90 or not issues:
                        logger.debug("Quality threshold reached, stopping improvements")
                        break
                    
                    # Generate improvement prompt
                    improvement_prompt = self._build_improvement_prompt(current_code, issues, language)
                    
                    # Get improved code
                    try:
                        improved_code = await self._generate_initial_code(improvement_prompt)
                        current_code = improved_code
                    except Exception as e:
                        logger.warning(f"Code improvement iteration {iteration} failed: {e}")
                        break
                        
                except Exception as e:
                    logger.error(f"Error during quality improvement iteration {iteration}: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Unexpected error during quality improvement: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to improve code quality: {str(e)}") from e
            
        return {
            'code': best_code,
            'score': best_score,
            'suggestions': suggestions,
            'iterations': iterations
        }
    
    # Add other methods from the original CodeGenerator class here
    # (_get_python_prompt, _get_javascript_prompt, etc.)
    # _build_prompt, _generate_initial_code, _extract_code_from_response, etc.
    
    # For now, we'll add placeholder methods to make the code runnable
    
    def _get_python_prompt(self) -> str:
        """Get Python-specific prompt template."""
        return """You are an expert Python developer. Generate high-quality, production-ready Python code.

Requirements:
- Follow PEP 8 style guidelines
- Include type hints for all functions
- Add comprehensive docstrings
- Include error handling where appropriate
- Use modern Python features (3.8+)
- Ensure code is secure and efficient

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented Python code:"""

    def _get_javascript_prompt(self) -> str:
        """Get JavaScript-specific prompt template."""
        return """You are an expert JavaScript developer. Generate modern, clean JavaScript code.

Requirements:
- Use ES6+ features
- Follow modern JavaScript best practices
- Include JSDoc comments
- Use async/await for asynchronous operations
- Implement proper error handling
- Ensure cross-browser compatibility

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented JavaScript code:"""

    def _get_typescript_prompt(self) -> str:
        """Get TypeScript-specific prompt template."""
        return """You are an expert TypeScript developer. Generate type-safe, production-ready TypeScript code.

Requirements:
- Use strict TypeScript typing
- Follow TypeScript best practices
- Include JSDoc comments with types
- Use async/await for asynchronous operations
- Implement proper error handling
- Export necessary types and interfaces

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented TypeScript code:"""

    def _get_go_prompt(self) -> str:
        """Get Go-specific prompt template."""
        return """You are an expert Go developer. Generate idiomatic, production-ready Go code.

Requirements:
- Follow Go coding standards and idioms
- Include proper error handling
- Add godoc comments
- Use appropriate concurrency patterns
- Ensure code is efficient and readable
- Handle all possible error cases

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented Go code:"""

    def _get_rust_prompt(self) -> str:
        """Get Rust-specific prompt template."""
        return """You are an expert Rust developer. Generate safe, idiomatic Rust code.

Requirements:
- Follow Rust coding standards
- Use proper error handling with Result and Option
- Include documentation comments
- Follow ownership and borrowing rules
- Make code as safe as possible
- Use appropriate crates when needed

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented Rust code:"""

    def _get_bash_prompt(self) -> str:
        """Get Bash-specific prompt template."""
        return """You are an expert Bash scripter. Generate robust, production-ready Bash scripts.

Requirements:
- Add proper shebang line
- Include error handling with set -euo pipefail
- Add comments explaining complex logic
- Use shellcheck-compliant code
- Handle edge cases and errors gracefully
- Make scripts as portable as possible

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, well-documented Bash script:"""

    def _get_sql_prompt(self) -> str:
        """Get SQL-specific prompt template."""
        return """You are an expert SQL developer. Generate optimized, production-ready SQL queries.

Requirements:
- Use proper indexing
- Optimize for performance
- Include comments for complex queries
- Handle edge cases
- Ensure data integrity
- Follow SQL best practices

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate optimized SQL code:"""

    def _build_prompt(self, request: CodeGenerationRequest) -> str:
        """Build prompt for code generation."""
        template = self.language_prompts.get(request.language, self.language_prompts[CodeLanguage.PYTHON])
        
        context = request.context or "No specific context provided"
        requirements = "\n".join(f"- {req}" for req in (request.requirements or [])) or "No specific requirements"
        
        prompt = template.format(
            description=request.description,
            context=context,
            requirements=requirements
        )
        
        if request.existing_code:
            prompt += f"\n\nExisting code to modify/extend:\n```{request.language.value}\n{request.existing_code}\n```"
            
        return prompt
    
    async def _generate_initial_code(self, prompt: str) -> str:
        """Generate initial code using LLM with retry logic."""
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self.ollama.generate(prompt)
                if not response or not response.strip():
                    raise ValueError("Empty response from LLM")
                return self._extract_code_from_response(response)
            except Exception as e:
                last_error = e
                logger.warning(f"Code generation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        
        raise RuntimeError(f"Failed to generate code after {max_retries} attempts: {str(last_error)}")
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code blocks from LLM response."""
        # Look for code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            # Return the largest code block
            return max(code_blocks, key=len).strip()
        
        # If no code blocks found, try to extract code-like content
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            # Skip markdown headers, plain text explanations
            if line.strip() and not line.startswith('#') and not line.startswith('*'):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _build_improvement_prompt(self, code: str, issues: List[str], language: CodeLanguage) -> str:
        """Build prompt for code improvement."""
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        
        return f"""Improve this {language.value} code by fixing the following issues:

Issues to fix:
{issues_text}

Current code:
```{language.value}
{code}
```

Improved code:
```{language.value}
"""
    
    async def _generate_tests(self, code: str) -> str:
        """Generate tests for the given code."""
        # Implementation would generate tests using the LLM
        return "# Tests would be generated here"
    
    async def _generate_documentation(self, code: str, language: CodeLanguage) -> str:
        """Generate documentation for the given code."""
        # Implementation would generate documentation using the LLM
        return "# Documentation would be generated here"
