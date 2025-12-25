#!/usr/bin/env python
"""
Setup script for slack-notifications.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="slack-notifications",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A simple Python library for Slack notifications at application milestones",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/slack-notifications",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "slack-sdk>=3.25.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "test": ["pytest>=7.4.0", "pytest-asyncio>=0.21.0"],
        "dev": ["black", "isort", "flake8", "mypy"],
    },
    package_data={
        "slack_notifications": ["py.typed"],
    },
    include_package_data=True,
)