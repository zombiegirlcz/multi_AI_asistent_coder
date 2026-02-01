from setuptools import setup, find_packages

setup(
    name="multi-ai-asistent-coder",
    version="2.1.0",
    description="Genius Copilot with multiple AI providers",
    author="zombiegirlcz",
    url="https://github.com/zombiegirlcz/multi_AI_asistent_coder",
    packages=find_packages(),
    install_requires=[
        "inquirer>=3.0.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-coder=ai_coder:main",
        ],
    },
    python_requires=">=3.8",
)
