#!/usr/bin/env python3
"""
KuPa runner script - ensures proper execution of the CLI tool
"""

import sys
import os

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the CLI
from kupa.cli import main

if __name__ == "__main__":
    main()