#!/usr/bin/env bash

# Script settings for cleaner output
set +x  # Disable command echoing
set -e  # Exit on any error

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo ""
    echo "========================================"
    printf "${BLUE}%s${NC}\n" "$1"
    echo "========================================"
}

# Function to print status messages
print_status() {
    printf "${GREEN}✓${NC} %s\n" "$1"
}

# Function to print warning messages
print_warning() {
    printf "${YELLOW}⚠${NC} %s\n" "$1"
}

# Function to print error messages
print_error() {
    printf "${RED}✗${NC} %s\n" "$1"
}

print_section "Python Virtual Environment Setup"
echo "This script will create a Python virtual environment and install dependencies."

print_section "Checking Existing Virtual Environment"
# Checking if .venv dir already exists.
if [ -d ".venv" ]; then
    print_warning "VENV directory (.venv) already exists, removing it..."
    rm -rf .venv
    print_status "Old virtual environment removed"
else
    print_status "No existing virtual environment found"
fi

print_section "Detecting Python Version"
# Checking if python3.11 is available in PATH.
if command -v python3.11 &>/dev/null; then
    python_executable="python3.11"
    print_status "Python 3.11 found and will be used for creating virtual environment"
else
    python_executable="python3"
    print_warning "Python 3.11 not found, using default python3 instead"
fi

print_section "Creating Virtual Environment"
echo "Creating virtual environment with $python_executable..."
if $python_executable -m venv .venv; then
    print_status "Virtual environment created successfully"
else
    print_error "Failed to create virtual environment"
    exit 1
fi

print_section "Activating Virtual Environment"
if source .venv/bin/activate; then
    print_status "Virtual environment activated"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_section "Installing Dependencies"
echo "Installing packages from dev/requirements.txt..."
if pip3 install -r dev/requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    deactivate
    exit 1
fi

print_section "Setup Complete"
print_status "Virtual environment is ready and configured!"
print_status "Dependencies have been installed from dev/requirements.txt"
echo ""
printf "${BLUE}To activate the virtual environment manually, run:${NC}\n"
printf "${YELLOW}source .venv/bin/activate${NC}\n"
echo ""

