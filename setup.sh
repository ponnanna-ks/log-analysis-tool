#!/bin/bash

# Function to check Python version
check_python_version() {
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -gt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 6 ]); then
            return 0
        else
            echo "Error: Python 3.6 or higher is required. Found version $PYTHON_VERSION"
            return 1
        fi
    else
        echo "Error: Python 3 is not installed"
        return 1
    fi
}

# Check Python version
if ! check_python_version; then
    exit 1
fi

# Check if virtual environment exists and remove it if it does
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

echo "Creating Python virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing required packages..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install required packages"
    exit 1
fi

echo "Setup complete!"
echo "To run the application, use: source venv/bin/activate && python log_analysis_ui.py" 