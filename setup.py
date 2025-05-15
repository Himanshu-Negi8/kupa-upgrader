from setuptools import setup, find_packages

setup(
    name="kupa",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "pyyaml",
        "requests",
        "gitpython",
        "pygithub",
        "fastapi",
        "uvicorn[standard]",
        "openai",
        "beautifulsoup4",
    ],
    entry_points={
        "console_scripts": [
            "kupa=kupa.cli:main",
        ],
    },
    python_requires=">=3.8",
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pytest-cov>=4.0.0",
            "wheel>=0.38.0",
        ]
    },
    author="KuPa Team",
    author_email="example@example.com",
    description="Kubernetes Upgrade Path Analyzer - Detects breaking changes in K8s YAML resources",
    keywords="kubernetes, upgrade, breaking changes, yaml, analysis",
    url="https://github.com/yourusername/kupa",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
