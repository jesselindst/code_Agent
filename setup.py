from setuptools import setup, find_packages

setup(
    name="code_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "openai",
        "colorama",
        "python-dotenv",
    ],
    entry_points={
        'console_scripts': [
            'code-agent=code_agent.cli:main',
        ],
    },
    author="Jesse Lindstadt",
    author_email="your.email@example.com",
    description="A library for LLM agents to operate as programmers using shell commands",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code_agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)