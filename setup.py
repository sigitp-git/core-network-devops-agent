"""
Setup configuration for Core Network DevOps Agent

This package provides an AI agent built with Amazon Bedrock's AgentCore framework
for managing core network infrastructure and DevOps operations on AWS.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="core-network-devops-agent",
    version="1.0.0",
    author="Core Network DevOps Team",
    author_email="core-network-devops@example.com",
    description="AI agent built with Amazon Bedrock AgentCore framework for core network infrastructure and DevOps operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/core-network-devops-agent",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Include additional files
    include_package_data=True,
    package_data={
        "core_network_devops_agent": [
            "config/*.yaml",
            "templates/*.yaml",
            "schemas/*.json"
        ]
    },
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings>=0.22.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "grafana-api>=1.0.3",
        ]
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "core-network-agent=core_network_devops_agent.__main__:main",
            "cn-agent=core_network_devops_agent.__main__:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Communications",
        "Topic :: System :: Networking",
    ],
    
    # Python version requirement
    python_requires=">=3.9",
    
    # Keywords
    keywords=[
        "ai", "agent", "bedrock", "agentcore", "framework", "aws", "5g", "core-network", 
        "devops", "kubernetes", "infrastructure", "automation", "decorators",
        "network-functions", "telecommunications", "tool-registry", "conversation-memory"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/your-org/core-network-devops-agent/issues",
        "Source": "https://github.com/your-org/core-network-devops-agent",
        "Documentation": "https://core-network-devops-agent.readthedocs.io/",
    },
)