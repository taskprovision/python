#!/usr/bin/env python3
"""
TaskProvision - AI-Powered Development Automation Platform
Main FastAPI application
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer
import uvicorn
from typing import Dict, Any

from .config.settings import get_settings
from .api import auth, projects, generation, billing
from .core.code_generator import CodeGenerator
from .core.quality_guard import QualityGuard
from .core.task_manager import TaskManager
from .core.ai_analyzer import AIAnalyzer
from .services.ollama_service import OllamaService
from .services.github_service import GitHubService
from .services.stripe_service import StripeService
from .utils.security import verify_token

# Global services
services: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    settings = get_settings()

    # Initialize services
    services["ollama"] = OllamaService(base_url=settings.ollama_base_url)
    services["github"] = GitHubService(token=settings.github_token)
    services["stripe"] = StripeService(api_key=settings.stripe_api_key)
    services["code_generator"] = CodeGenerator(services["ollama"])
    services["quality_guard"] = QualityGuard()
    services["task_manager"] = TaskManager()
    services["ai_analyzer"] = AIAnalyzer(services["ollama"])

    # Test connections
    try:
        await services["ollama"].health_check()
        print("✅ Ollama service connected")
    except Exception as e:
        print(f"⚠️ Ollama service unavailable: {e}")

    yield

    # Shutdown
    print("🔄 Shutting down TaskProvision services...")


# Create FastAPI app
app = FastAPI(
    title="TaskProvision",
    description="AI-Powered Development Automation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(generation.router, prefix="/api/generation", tags=["Code Generation"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "web", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Root endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with platform overview"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TaskProvision - AI Development Automation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; min-height: 100vh; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .hero { margin-bottom: 3rem; }
            .feature { background: rgba(255,255,255,0.1); padding: 1.5rem; margin: 1rem 0; border-radius: 10px; }
            .cta { background: #ff6b6b; color: white; padding: 1rem 2rem; border: none; border-radius: 5px; font-size: 1.1rem; cursor: pointer; text-decoration: none; display: inline-block; margin: 0.5rem; }
            .stats { display: flex; justify-content: space-around; margin: 2rem 0; }
            .stat { text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>🚀 TaskProvision</h1>
                <h2>AI-Powered Development Automation</h2>
                <p>From idea to production-ready code in minutes, not hours</p>
            </div>

            <div class="stats">
                <div class="stat">
                    <h3>90%</h3>
                    <p>Faster Development</p>
                </div>
                <div class="stat">
                    <h3>95%</h3>
                    <p>Code Quality</p>
                </div>
                <div class="stat">
                    <h3>80%</h3>
                    <p>Cost Reduction</p>
                </div>
            </div>

            <div class="feature">
                <h3>🤖 AI Code Generation</h3>
                <p>Generate high-quality, production-ready code from natural language descriptions</p>
            </div>

            <div class="feature">
                <h3>🛡️ Quality Assurance</h3>
                <p>Automated testing, code review, and security scanning built-in</p>
            </div>

            <div class="feature">
                <h3>📊 Project Management</h3>
                <p>AI-powered task management with intelligent prioritization and insights</p>
            </div>

            <div style="margin-top: 3rem;">
                <a href="/docs" class="cta">🔧 API Documentation</a>
                <a href="/api/auth/demo" class="cta">🎮 Try Demo</a>
                <a href="https://github.com/taskprovision/www" class="cta">📚 Learn More</a>
            </div>

            <div style="margin-top: 2rem; opacity: 0.8;">
                <p>Ready to 10x your development workflow?</p>
                <p><strong>curl -fsSL https://get.taskprovision.com | bash</strong></p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "ollama": await services.get("ollama", {}).health_check() if "ollama" in services else False,
            "database": True,  # Add actual DB check
            "storage": True,  # Add actual storage check
        }
    }


@app.get("/status")
async def system_status():
    """Detailed system status"""
    return {
        "platform": "TaskProvision",
        "version": "1.0.0",
        "uptime": "24h",  # Calculate actual uptime
        "active_projects": 42,  # Get from database
        "generated_lines": 150000,  # Get from metrics
        "quality_score": 94.5,  # Calculate average
        "services": {
            "ai_engine": "operational",
            "code_generator": "operational",
            "quality_guard": "operational",
            "task_manager": "operational"
        }
    }


# Free tools for lead generation
@app.get("/tools/repo-health")
async def repo_health_checker():
    """Free repository health checker tool"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Repository Health Checker - TaskProvision</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui; margin: 0; padding: 2rem; background: #f8f9fa; }
            .container { max-width: 600px; margin: 0 auto; }
            .tool { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            input, button { padding: 0.75rem; margin: 0.5rem 0; width: 100%; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            .result { margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="tool">
                <h2>🔍 Repository Health Checker</h2>
                <p>Get instant analysis of your GitHub repository's health and quality</p>

                <input type="url" placeholder="https://github.com/username/repository" id="repoUrl">
                <button onclick="analyzeRepo()">Analyze Repository</button>

                <div id="result" class="result" style="display:none;">
                    <h3>📊 Health Score: <span id="score">0</span>/100</h3>
                    <div id="issues"></div>
                    <hr>
                    <p><strong>💡 Get full analysis with TaskProvision AutoFix</strong></p>
                    <a href="/signup" style="background: #28a745; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 5px;">Start Free Trial</a>
                </div>
            </div>
        </div>

        <script>
        async function analyzeRepo() {
            const url = document.getElementById('repoUrl').value;
            if (!url) return;

            // Mock analysis - replace with actual API call
            const mockResult = {
                score: Math.floor(Math.random() * 40) + 50,
                issues: [
                    '23% functions lack docstrings',
                    '156 lines of duplicate code detected',
                    '5 security vulnerabilities',
                    'Missing unit tests (43% coverage)',
                    '12 outdated dependencies'
                ]
            };

            document.getElementById('score').textContent = mockResult.score;
            document.getElementById('issues').innerHTML = mockResult.issues.map(issue => `<p>❌ ${issue}</p>`).join('');
            document.getElementById('result').style.display = 'block';
        }
        </script>
    </body>
    </html>
    """)


@app.get("/api/test", response_model=Dict[str, str])
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"status": "success", "message": "TaskProvision API is running!"}

if __name__ == "__main__":
    uvicorn.run(
        "taskprovision.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )