"""Setup configuration for the master fantasy-football app."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fantasy-football-app",
    version="1.0.0",
    author="Your Name",
    description="Master fantasy football app with Watson as an embedded subpackage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=0.20.0",
        "reportlab>=4.0.0",
        "beautifulsoup4>=4.11.0",
        "selenium>=4.20.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0.0"],
    },
    entry_points={
        "console_scripts": [
            "watson-ingest=watson.ingest:main",
        ],
    },
)
