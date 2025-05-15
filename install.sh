#!/bin/bash
# Install script for KuPa

set -e  # Exit on any error

echo "KuPa - Kubernetes Upgrade Path Analyzer Installation"
echo "===================================================="

# Check Python version
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3 is not installed. Please install Python 3.8 or newer."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Using Python $PYTHON_VERSION"

# Compare versions: 3.8 minimum
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc) -eq 1 ]]; then
    echo "Error: Python 3.8 or newer is required. Your version: $PYTHON_VERSION"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install KuPa
echo "Installing KuPa and dependencies..."
if [ "$1" == "--dev" ]; then
    echo "Installing in development mode..."
    pip install -e ".[dev]"
else
    pip install -e .
fi

echo "Setting up config directory..."
mkdir -p ~/.config/kupa
if [ ! -f ~/.config/kupa/kupa.yaml ]; then
    cp config/kupa.yaml ~/.config/kupa/kupa.yaml
fi

echo ""
echo "Installation complete! You can now use KuPa with:"
echo "  source venv/bin/activate  # Activate the virtual environment"
echo "  kupa --help               # View available commands"
echo ""
echo "Don't forget to set up your environment variables:"
echo "  export OPENAI_API_KEY=your_key"
echo "  export GITHUB_TOKEN=your_token"
echo ""
