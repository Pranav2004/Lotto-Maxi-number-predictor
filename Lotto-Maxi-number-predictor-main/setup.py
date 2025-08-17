"""Setup script for Lotto Max Analyzer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="lotto-max-analyzer",
    version="1.0.0",
    author="Lotto Max Analyzer Team",
    author_email="contact@example.com",
    description="A comprehensive Python application for analyzing Lotto Max lottery data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/lotto-max-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "psutil>=5.9.0",
            "mypy>=1.5.0",
            "types-requests>=2.31.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lotto-max-analyzer=lotto_max_analyzer.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "lotto_max_analyzer": ["config/*.json", "data/*.sql"],
    },
)