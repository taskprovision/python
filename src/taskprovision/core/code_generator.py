"""
TaskProvision Code Generator
AI-powered code generation with quality assurance
"""

import asyncio
import ast
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..services.ollama_service import OllamaService
from .quality_guard import QualityGuard

logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    BASH = "bash"
    SQL = "sql"

@dataclass
class CodeGenerationRequest:
    """Code generation request parameters"""
    description: str
    language: CodeLanguage
    context: Optional[str] = None
    existing_code: Optional[str] = None
    requirements: List[str] = None
    style_preferences: Dict[str, Any] = None
    max_length: int = 1000

@dataclass
class CodeGenerationResult:
    """Code generation result"""
    generated_code: str
    language: CodeLanguage
    quality_score: float
    suggestions: List[str]
    tests: Optional[str] = None
    documentation: Optional[str] = None
    execution_time: float = 0.0
    iterations: int = 1

class CodeGenerator:
    """AI-powered code generator with quality assurance"""

    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.quality_guard = QualityGuard()

        # Language-specific prompts
        self.language_prompts = {
            CodeLanguage.PYTHON: self._get_python_prompt(),
            CodeLanguage.JAVASCRIPT: self._get_javascript_prompt(),
            CodeLanguage.TYPESCRIPT: self._get_typescript_prompt(),
            CodeLanguage.GO: self._get_go_prompt(),
            CodeLanguage.RUST: self._get_rust_prompt(),
            CodeLanguage.BASH: self._get_bash_prompt(),
            CodeLanguage.SQL: self._get_sql_prompt(),
        }

    def _get_python_prompt(self) -> str:
        """Get Python-specific prompt template"""
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
        """Get JavaScript-specific prompt template"""
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

Generate clean, modern JavaScript code:"""

    def _get_typescript_prompt(self) -> str:
        """Get TypeScript-specific prompt template"""
        return """You are an expert TypeScript developer. Generate type-safe, modern TypeScript code.

Requirements:
- Use strict TypeScript configuration
- Define proper interfaces and types
- Include comprehensive type annotations
- Follow TypeScript best practices
- Use modern ES6+ features
- Implement proper error handling

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, type-safe TypeScript code:"""

    def _get_go_prompt(self) -> str:
        """Get Go-specific prompt template"""
        return """You are an expert Go developer. Generate idiomatic, efficient Go code.

Requirements:
- Follow Go conventions and idioms
- Include proper error handling
- Add comprehensive comments
- Use appropriate data structures
- Ensure thread safety where needed
- Follow gofmt standards

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, idiomatic Go code:"""

    def _get_rust_prompt(self) -> str:
        """Get Rust-specific prompt template"""
        return """You are an expert Rust developer. Generate safe, efficient Rust code.

Requirements:
- Follow Rust idioms and best practices
- Proper ownership and borrowing
- Include comprehensive documentation
- Handle errors using Result types
- Use appropriate data structures
- Ensure memory safety

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate safe, idiomatic Rust code:"""

    def _get_bash_prompt(self) -> str:
        """Get Bash-specific prompt template"""
        return """You are an expert Bash scripter. Generate robust, portable shell scripts.

Requirements:
- Use proper error handling (set -e, etc.)
- Include helpful comments
- Make scripts portable across systems
- Use best practices for security
- Include usage information
- Handle edge cases

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate robust Bash script:"""

    def _get_sql_prompt(self) -> str:
        """Get SQL-specific prompt template"""
        return """You are an expert SQL developer. Generate efficient, secure SQL queries.

Requirements:
- Use proper SQL formatting and indentation
- Include comments explaining complex logic
- Ensure queries are optimized for performance
- Use parameterized queries to prevent SQL injection
- Follow database best practices
- Include appropriate indexes suggestions

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate optimized SQL code:"""

    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResult:
        """Generate code based on request"""
        import time
        start_time = time.time()

        try:
            # Build prompt
            prompt = self._build_prompt(request)

            # Generate initial code
            generated_code = await self._generate_initial_code(prompt)

            # Quality check and improvement
            quality_result = await self._improve_code_quality(
                generated_code,
                request.language,
                max_iterations=3
            )

            # Generate tests if Python
            tests = None
            if request.language == CodeLanguage.PYTHON:
                tests = await self._generate_tests(quality_result['code'])

            # Generate documentation
            documentation = await self._generate_documentation(
                quality_result['code'],
                request.language
            )

            execution_time = time.time() - start_time

            return CodeGenerationResult(
                generated_code=quality_result['code'],
                language=request.language,
                quality_score=quality_result['score'],
                suggestions=quality_result['suggestions'],
                tests=tests,
                documentation=documentation,
                execution_time=execution_time,
                iterations=quality_result['iterations']
            )

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise

    def _build_prompt(self, request: CodeGenerationRequest) -> str:
        """Build prompt for code generation"""
        template = self.language_prompts[request.language]

        context = request.context or "No specific context provided"
        requirements = "\n".join(request.requirements) if request.requirements else "No specific requirements"

        prompt = template.format(
            description=request.description,
            context=context,
            requirements=requirements
        )

        if request.existing_code:
            prompt += f"\n\nExisting code to modify/extend:\n```{request.language.value}\n{request.existing_code}\n```"

        return prompt

    async def _generate_initial_code(self, prompt: str) -> str:
        """Generate initial code using LLM"""
        response = await self.ollama.generate(prompt)

        # Extract code from response
        code = self._extract_code_from_response(response)

        return code

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code blocks from LLM response"""
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

    async def _improve_code_quality(self, code: str, language: CodeLanguage, max_iterations: int = 3) -> Dict:
        """Improve code quality through iterations"""
        current_code = code
        iterations = 0
        best_score = 0
        best_code = code
        suggestions = []

        for iteration in range(max_iterations):
            iterations += 1

            # Analyze code quality
            if language == CodeLanguage.PYTHON:
                quality_result = self.quality_guard.analyze_python_code(current_code)
            else:
                quality_result = self.quality_guard.analyze_general_code(current_code, language.value)

            score = quality_result['score']
            issues = quality_result['issues']

            # Update best if improved
            if score > best_score:
                best_score = score
                best_code = current_code
                suggestions = quality_result['suggestions']

            # If quality is good enough, stop
            if score >= 90 or not issues:
                break

            # Generate improvement prompt
            improvement_prompt = self._build_improvement_prompt(current_code, issues, language)

            # Get improved code
            try:
                improved_code = await self._generate_initial_code(improvement_prompt)
                current_code = improved_code
            except Exception as e:
                logger.warning(f"Code improvement iteration {iteration + 1} failed: {e}")
                break

        return {
            'code': best_code,
            'score': best_score,
            'suggestions': suggestions,
            'iterations': iterations
        }

    def _build_improvement_prompt(self, code: str, issues: List[str], language: CodeLanguage) -> str:
        """Build prompt for code improvement"""
        issues_text = "\n".join(f"- {issue}" for issue in issues)

        return f"""Improve this {language.value} code by fixing the following issues:

Issues to fix:
{issues_text}

Current code:
```{language.value}
{code}
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
import asyncio
import ast
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..services.ollama_service import OllamaService
from .quality_guard import QualityGuard

logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    BASH = "bash"
    SQL = "sql"

@dataclass
class CodeGenerationRequest:
    """Code generation request parameters"""
    description: str
    language: CodeLanguage
    context: Optional[str] = None
    existing_code: Optional[str] = None
    requirements: List[str] = None
    style_preferences: Dict[str, Any] = None
    max_length: int = 1000

@dataclass
class CodeGenerationResult:
    """Code generation result"""
    generated_code: str
    language: CodeLanguage
    quality_score: float
    suggestions: List[str]
    tests: Optional[str] = None
    documentation: Optional[str] = None
    execution_time: float = 0.0
    iterations: int = 1

class CodeGenerator:
    """AI-powered code generator with quality assurance"""

    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.quality_guard = QualityGuard()

        # Language-specific prompts
        self.language_prompts = {
            CodeLanguage.PYTHON: self._get_python_prompt(),
            CodeLanguage.JAVASCRIPT: self._get_javascript_prompt(),
            CodeLanguage.TYPESCRIPT: self._get_typescript_prompt(),
            CodeLanguage.GO: self._get_go_prompt(),
            CodeLanguage.RUST: self._get_rust_prompt(),
            CodeLanguage.BASH: self._get_bash_prompt(),
            CodeLanguage.SQL: self._get_sql_prompt(),
        }

    def _get_python_prompt(self) -> str:
        """Get Python-specific prompt template"""
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
        """Get JavaScript-specific prompt template"""
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

Generate clean, modern JavaScript code:"""

    def _get_typescript_prompt(self) -> str:
        """Get TypeScript-specific prompt template"""
        return """You are an expert TypeScript developer. Generate type-safe, modern TypeScript code.

Requirements:
- Use strict TypeScript configuration
- Define proper interfaces and types
- Include comprehensive type annotations
- Follow TypeScript best practices
- Use modern ES6+ features
- Implement proper error handling

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, type-safe TypeScript code:"""

    def _get_go_prompt(self) -> str:
        """Get Go-specific prompt template"""
        return """You are an expert Go developer. Generate idiomatic, efficient Go code.

Requirements:
- Follow Go conventions and idioms
- Include proper error handling
- Add comprehensive comments
- Use appropriate data structures
- Ensure thread safety where needed
- Follow gofmt standards

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate clean, idiomatic Go code:"""

    def _get_rust_prompt(self) -> str:
        """Get Rust-specific prompt template"""
        return """You are an expert Rust developer. Generate safe, efficient Rust code.

Requirements:
- Follow Rust idioms and best practices
- Proper ownership and borrowing
- Include comprehensive documentation
- Handle errors using Result types
- Use appropriate data structures
- Ensure memory safety

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate safe, idiomatic Rust code:"""

    def _get_bash_prompt(self) -> str:
        """Get Bash-specific prompt template"""
        return """You are an expert Bash scripter. Generate robust, portable shell scripts.

Requirements:
- Use proper error handling (set -e, etc.)
- Include helpful comments
- Make scripts portable across systems
- Use best practices for security
- Include usage information
- Handle edge cases

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate robust Bash script:"""

    def _get_sql_prompt(self) -> str:
        """Get SQL-specific prompt template"""
        return """You are an expert SQL developer. Generate efficient, secure SQL queries.

Requirements:
- Use proper SQL formatting and indentation
- Include comments explaining complex logic
- Ensure queries are optimized for performance
- Use parameterized queries to prevent SQL injection
- Follow database best practices
- Include appropriate indexes suggestions

Task: {description}

Context: {context}

Requirements:
{requirements}

Generate optimized SQL code:"""

    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResult:
        """Generate code based on request"""
        import time
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = self._build_prompt(request)
            
            # Generate initial code
            generated_code = await self._generate_initial_code(prompt)
            
            # Quality check and improvement
            quality_result = await self._improve_code_quality(
                generated_code, 
                request.language, 
                max_iterations=3
            )
            
            # Generate tests if Python
            tests = None
            if request.language == CodeLanguage.PYTHON:
                tests = await self._generate_tests(quality_result['code'])
            
            # Generate documentation
            documentation = await self._generate_documentation(
                quality_result['code'], 
                request.language
            )
            
            execution_time = time.time() - start_time
            
            return CodeGenerationResult(
                generated_code=quality_result['code'],
                language=request.language,
                quality_score=quality_result['score'],
                suggestions=quality_result['suggestions'],
                tests=tests,
                documentation=documentation,
                execution_time=execution_time,
                iterations=quality_result['iterations']
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise

    def _build_prompt(self, request: CodeGenerationRequest) -> str:
        """Build prompt for code generation"""
        template = self.language_prompts[request.language]

        context = request.context or "No specific context provided"
        requirements = "\n".join(request.requirements) if request.requirements else "No specific requirements"

        prompt = template.format(
            description=request.description,
            context=context,
            requirements=requirements
        )

        if request.existing_code:
            prompt += f"\n\nExisting code to modify/extend:\n```{request.language.value}\n{request.existing_code}\n```"

        return prompt

    async def _generate_initial_code(self, prompt: str) -> str:
        """Generate initial code using LLM"""
        response = await self.ollama.generate(prompt)

        # Extract code from response
        code = self._extract_code_from_response(response)

        return code

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code blocks from LLM response"""
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

    async def _improve_code_quality(self, code: str, language: CodeLanguage, max_iterations: int = 3) -> Dict:
        """Improve code quality through iterations"""
        current_code = code
        iterations = 0
        best_score = 0
        best_code = code
        suggestions = []

        for iteration in range(max_iterations):
            iterations += 1

            # Analyze code quality
            if language == CodeLanguage.PYTHON:
                quality_result = self.quality_guard.analyze_python_code(current_code)
            else:
                quality_result = self.quality_guard.analyze_general_code(current_code, language.value)

            score = quality_result['score']
            issues = quality_result['issues']

            # Update best if improved
            if score > best_score:
                best_score = score
                best_code = current_code
                suggestions = quality_result['suggestions']

            # If quality is good enough, stop
            if score >= 90 or not issues:
                break

            # Generate improvement prompt
            improvement_prompt = self._build_improvement_prompt(current_code, issues, language)

            # Get improved code
            try:
                improved_code = await self._generate_initial_code(improvement_prompt)
                current_code = improved_code
            except Exception as e:
                logger.warning(f"Code improvement iteration {iteration + 1} failed: {e}")
                break

        return {
            'code': best_code,
            'score': best_score,
            'suggestions': suggestions,
            'iterations': iterations
        }

    def _build_improvement_prompt(self, code: str, issues: List[str], language: CodeLanguage) -> str:
        """Build prompt for code improvement"""
        issues_text = "\n".join(f"- {issue}" for issue in issues)

        return f"""Improve this {language.value} code by fixing the following issues:

Issues to fix:
{issues_text}

Current code:
```{language.value}
{code}
```

Generate improved code that addresses all the issues while maintaining functionality:"""

    async def _generate_tests(self, code: str) -> Optional[str]:
        """Generate unit tests for Python code"""
        try:
            # Extract functions and classes from code
            tree = ast.parse(code)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            if not functions and not classes:
                return None

            prompt = f"""Generate comprehensive unit tests for this Python code using pytest.

Code to test:
```python
{code}
```

Functions found: {', '.join(functions)}
Classes found: {', '.join(classes)}

Generate complete test suite with:
- Test for normal cases
- Test for edge cases
- Test for error conditions
- Use descriptive test names
- Include docstrings for test functions

Generate pytest test code:"""
            
            tests = await self._generate_initial_code(prompt)
            return tests
            
        except Exception as e:
            logger.warning(f"Test generation failed: {e}")
            return None

    async def _generate_documentation(self, code: str, language: CodeLanguage) -> Optional[str]:
        """Generate documentation for code"""
        try:
            prompt = f"""Generate comprehensive documentation for this {language.value} code.

Code:
```{language.value}
{code}
```

Generate documentation that includes:
- Overview of what the code does
- Function/method descriptions
- Parameter explanations
- Return value descriptions
- Usage examples
- Any important notes or warnings

Format as markdown:"""
            
            docs = await self.ollama.generate(prompt)
            return docs
            
        except Exception as e:
            logger.warning(f"Documentation generation failed: {e}")
            return None

    async def analyze_existing_code(self, code: str, language: CodeLanguage) -> Dict:
        """Analyze existing code and provide suggestions"""
        try:
            if language == CodeLanguage.PYTHON:
                analysis = self.quality_guard.analyze_python_code(code)
            else:
                analysis = self.quality_guard.analyze_general_code(code, language.value)
            
            # Get AI suggestions for improvement
            prompt = f"""Analyze this {language.value} code and provide specific improvement suggestions.

Code:
```{language.value}
{code}
```

Provide analysis including:
- Code quality assessment
- Performance improvements
- Security considerations
- Best practices recommendations
- Refactoring suggestions

Format as structured analysis:"""
            
            ai_analysis = await self.ollama.generate(prompt)
            
            # Combine quality guard and AI analysis
            return {
                'quality_score': analysis['score'],
                'issues': analysis['issues'],
                'suggestions': analysis['suggestions'],
                'ai_analysis': ai_analysis,
                'language': language.value
            }
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {'error': str(e)}

    async def refactor_code(self, code: str, language: CodeLanguage, refactoring_goal: str) -> str:
        """Refactor existing code for specific goal"""
        prompt = f"""Refactor this {language.value} code to achieve: {refactoring_goal}

Current code:
```{language.value}
{code}
```

Refactoring goal: {refactoring_goal}

Requirements:
- Maintain all existing functionality
- Improve code structure and readability
- Follow best practices for {language.value}
- Add comments explaining changes

Generate refactored code:"""
        
        refactored_code = await self._generate_initial_code(prompt)
        
        # Quality check the refactored code
        quality_result = await self._improve_code_quality(refactored_code, language, max_iterations=2)
        
        return quality_result['code']

# Utility functions for code generation
class CodeTemplates:
    """Code templates for common patterns"""

    @staticmethod
    def get_api_template(language: CodeLanguage) -> str:
        """Get REST API template for language"""
        templates = {
            CodeLanguage.PYTHON: '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
async def create_item(item: Item):
    return item
''',
            CodeLanguage.JAVASCRIPT: '''
const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Hello World' });
});

app.get('/items/:id', (req, res) => {
  const itemId = req.params.id;
  res.json({ item_id: itemId });
});

app.post('/items', (req, res) => {
  const item = req.body;
  res.json(item);
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
''',
            CodeLanguage.GO: '''
package main

import (
    "encoding/json"
    "log"
    "net/http"
    "strconv"

    "github.com/gorilla/mux"
)

type Item struct {
    ID          int    `json:"id"`
    Name        string `json:"name"`
    Description string `json:"description"`
}

func main() {
    r := mux.NewRouter()

    r.HandleFunc("/", homeHandler).Methods("GET")
    r.HandleFunc("/items/{id}", getItemHandler).Methods("GET")
    r.HandleFunc("/items", createItemHandler).Methods("POST")

    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{"message": "Hello World"})
}

func getItemHandler(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]int{"item_id": id})
}

func createItemHandler(w http.ResponseWriter, r *http.Request) {
    var item Item
    json.NewDecoder(r.body).Decode(&item)

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(item)
}
'''
        }

        return templates.get(language, "# Template not available for this language")
