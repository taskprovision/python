"""
TaskProvision - AI-Powered Development Automation Platform

A comprehensive platform for automating development workflows using AI,
including code generation, quality assurance, and task management.
"""

__version__ = "1.0.0"
__author__ = "TaskProvision Team"
__email__ = "contact@taskprovision.com"
__license__ = "Apache 2.0"

# Core imports for public API
from .core.code_generator import CodeGenerator
from .core.quality_guard import QualityGuard
from .core.task_manager import TaskManager
from .core.ai_analyzer import AIAnalyzer

# Configuration
from .config.settings import get_settings

# Main application
from .main import app

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "CodeGenerator",
    "QualityGuard",
    "TaskManager",
    "AIAnalyzer",
    "get_settings",
    "app",
]

# Package metadata
PACKAGE_INFO = {
    "name": "taskprovision",
    "version": __version__,
    "description": "AI-Powered Development Automation Platform",
    "author": __author__,
    "email": __email__,
    "license": __license__,
    "url": "https://github.com/taskprovision/python",
    "docs": "https://github.com/taskprovision/www",
    "source": "https://github.com/taskprovision/taskprovision",
}

def get_package_info():
    """Get package information dictionary"""
    return PACKAGE_INFO.copy()

def print_banner():
    """Print TaskProvision banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                        TaskProvision                         ║
║              AI-Powered Development Automation               ║
║                          v{__version__}                          ║
╚══════════════════════════════════════════════════════════════╝

🚀 From idea to production-ready code in minutes
🤖 AI-powered code generation and quality assurance
📊 Intelligent task management with insights
🛡️ Built-in security and best practices

Documentation: https://github.com/taskprovision/www
Support: https://github.com/taskprovision/taskprovision/issues
"""
    print(banner)

# Initialize logging
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"TaskProvision v{__version__} initialized")