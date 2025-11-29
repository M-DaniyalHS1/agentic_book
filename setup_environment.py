#!/usr/bin/env python3
"""
Virtual Environment Setup Script for AI-Enhanced Interactive Book Agent

This script automates the setup of a virtual environment with all required dependencies
for the AI-Enhanced Interactive Book Agent project.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path


def create_virtual_environment(venv_path):
    """Create a virtual environment at the specified path."""
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("Virtual environment created successfully!")


def install_dependencies(venv_path):
    """Install project dependencies into the virtual environment."""
    print("Installing project dependencies...")
    
    # Determine the path to pip in the virtual environment
    if os.name == 'nt':  # Windows
        pip_path = venv_path / 'Scripts' / 'pip.exe'
        python_path = venv_path / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        pip_path = venv_path / 'bin' / 'pip'
        python_path = venv_path / 'bin' / 'python'
    
    # Upgrade pip first
    subprocess.check_call([str(pip_path), 'install', '--upgrade', 'pip'])
    
    # Install requirements
    requirements_path = Path(__file__).parent / 'requirements.txt'
    subprocess.check_call([str(pip_path), 'install', '-r', str(requirements_path)])
    
    # Install development requirements
    dev_requirements_path = Path(__file__).parent / 'requirements-dev.txt'
    if dev_requirements_path.exists():
        subprocess.check_call([str(pip_path), 'install', '-r', str(dev_requirements_path)])
    
    print("Dependencies installed successfully!")


def setup_pre_commit_hooks(venv_path):
    """Optionally setup pre-commit hooks if pre-commit is in requirements."""
    if os.name == 'nt':  # Windows
        python_path = venv_path / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        python_path = venv_path / 'bin' / 'python'
    
    try:
        # Check if pre-commit is installed
        result = subprocess.run([str(python_path), '-c', 'import pre_commit'], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            # If pre-commit is installed, install the hooks
            subprocess.check_call([str(python_path), '-m', 'pre_commit', 'install'])
            print("Pre-commit hooks installed successfully!")
        else:
            print("Pre-commit not found in requirements, skipping hook installation")
    except subprocess.CalledProcessError:
        print("Error checking for pre-commit, skipping hook installation")


def main():
    """Main function to orchestrate the virtual environment setup."""
    project_root = Path(__file__).parent
    
    # Define virtual environment path
    venv_path = project_root / '.venv'
    
    print("Setting up virtual environment for AI-Enhanced Interactive Book Agent...")
    print(f"Project root: {project_root}")
    print(f"Virtual environment path: {venv_path}")
    
    # Create virtual environment
    create_virtual_environment(venv_path)
    
    # Install dependencies
    install_dependencies(venv_path)
    
    # Setup pre-commit hooks if available
    setup_pre_commit_hooks(venv_path)
    
    print("\nVirtual environment setup completed successfully!")
    print(f"Virtual environment located at: {venv_path}")
    
    if os.name == 'nt':  # Windows
        activate_command = f"{venv_path / 'Scripts' / 'activate'}"
        print(f"To activate the virtual environment, run: {activate_command}")
    else:  # Unix/Linux/macOS
        activate_command = f"source {venv_path / 'bin' / 'activate'}"
        print(f"To activate the virtual environment, run: {activate_command}")


if __name__ == "__main__":
    main()