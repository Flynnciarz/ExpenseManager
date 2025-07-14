#!/usr/bin/env python3
"""
Expense Manager Launcher Script

This script provides an easy way to run the expense management application
with proper error handling and environment setup.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['bcrypt', 'cryptography']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Error: Missing required dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """Setup the application environment."""
    # Add current directory to Python path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Create logs directory if it doesn't exist
    logs_dir = current_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    return True

def install_dependencies():
    """Install dependencies automatically."""
    try:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("Error: pip not found. Please install pip first.")
        return False

def main():
    """Main launcher function."""
    print("=" * 60)
    print("    SECURE EXPENSE MANAGEMENT SYSTEM LAUNCHER")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("Failed to setup environment.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        response = input("\nWould you like to install missing dependencies? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            if not install_dependencies():
                sys.exit(1)
            # Check again after installation
            if not check_dependencies():
                print("Dependencies still missing after installation.")
                sys.exit(1)
        else:
            print("Cannot run without required dependencies.")
            sys.exit(1)
    
    print("Environment check passed. Starting application...\n")
    
    try:
        # Import and run the main application
        from main import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Please ensure all files are in the correct location.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Unexpected error in launcher")
        sys.exit(1)

if __name__ == "__main__":
    main()
