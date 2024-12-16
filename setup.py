"""Setup file for LoadApp.AI."""
from setuptools import find_packages, setup

setup(
    name="loadapp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "SQLAlchemy>=2.0.0",
        "python-dotenv>=1.0.0",
        "streamlit>=1.0.0",
        "flask>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=4.0.0",
        ]
    },
)
