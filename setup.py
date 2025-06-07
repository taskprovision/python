#!/usr/bin/env python3
"""
TaskProvision - AI-Powered Development Automation Platform
Setup configuration for PyPI package
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure Python 3.8+
if sys.version_info < (3, 8):
    sys.exit("TaskProvision requires Python 3.8 or higher")


# Read version from file
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "src", "taskprovision", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


# Read long description from README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    return "AI-Powered Development Automation Platform"


# Read requirements
def get_requirements(filename="requirements.txt"):
    requirements_file = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(requirements_file):
        with open(requirements_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []


setup(
    name="taskprovision",
    version=get_version(),
    author="TaskProvision Team",
    author_email="contact@taskprovision.com",
    description="AI-Powered Development Automation Platform",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/taskprovision/python",
    project_urls={
        "Homepage": "https://github.com/taskprovision/www",
        "Documentation": "https://github.com/taskprovision/www",
        "Source": "https://github.com/taskprovision/taskprovision",
        "Tracker": "https://github.com/taskprovision/taskprovision/issues",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements("requirements.txt"),
    extras_require={
        "dev": get_requirements("requirements-dev.txt"),
        "test": [
            "pytest>=6.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "fakeredis>=2.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.0.0",
            "mkdocstrings[python]>=0.20.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "sentry-sdk[fastapi]>=1.0.0",
        ],
        "all": [
            "pytest>=6.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "fakeredis>=2.0.0",
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.0.0",
            "mkdocstrings[python]>=0.20.0",
            "prometheus-client>=0.16.0",
            "sentry-sdk[fastapi]>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "taskprovision=taskprovision.cli:main",
            "tprov=taskprovision.cli:main",
            "taskprov=taskprovision.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "taskprovision": [
            "templates/*.html",
            "templates/*.txt",
            "static/css/*.css",
            "static/js/*.js",
            "static/images/*",
            "config/*.yaml",
            "config/*.json",
        ],
    },
    zip_safe=False,
    keywords=[
        "ai", "automation", "development", "code-generation",
        "quality-assurance", "task-management", "llm", "fastapi",
        "kubernetes", "devops", "productivity", "sales-automation"
    ],
    platforms=["any"],
    license="Apache 2.0",

    # PyPI metadata
    maintainer="TaskProvision Team",
    maintainer_email="maintainers@taskprovision.com",

    # Security
    download_url="https://github.com/taskprovision/python/archive/refs/heads/main.zip",

    # Additional metadata for better discoverability
    provides=['taskprovision'],
)