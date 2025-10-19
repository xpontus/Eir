#!/usr/bin/env python3
"""
Eir Build System
Cross-platform build automation for the Eir STPA tool.

Usage:
    python build.py <command>
    
Commands:
    clean       - Clean build artifacts
    test        - Run test suite  
    build       - Build distributable application
    install     - Install dependencies
    dev         - Setup development environment
    lint        - Run code linting
    format      - Format code
    check       - Run all checks (test + lint)
    all         - Full pipeline (clean, install, test, build)
    run         - Run application in development mode
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
PYTHON = sys.executable
VENV_DIR = "venv"
MAIN_SCRIPT = "eir.py"

def run_command(cmd, check=True, cwd=None):
    """Run a shell command with error handling."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, cwd=cwd)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False

def get_venv_python():
    """Get the path to the virtual environment Python."""
    if os.name == 'nt':  # Windows
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:  # Unix-like
        return os.path.join(VENV_DIR, "bin", "python")

def get_venv_pip():
    """Get the path to the virtual environment pip."""
    if os.name == 'nt':  # Windows
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:  # Unix-like
        return os.path.join(VENV_DIR, "bin", "pip")

def clean():
    """Clean build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    # Remove build directories
    dirs_to_remove = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    # Remove .pyc files and __pycache__ directories
    for root, dirs, files in os.walk("."):
        # Remove __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
        
        # Remove .pyc files
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))
    
    print("✅ Clean complete.")

def setup_venv():
    """Create virtual environment if it doesn't exist."""
    if not os.path.exists(VENV_DIR):
        print("🔧 Creating virtual environment...")
        run_command(f"{PYTHON} -m venv {VENV_DIR}")
        print("✅ Virtual environment created.")
    return True

def install():
    """Install dependencies."""
    print("📦 Installing dependencies...")
    setup_venv()
    
    pip_cmd = get_venv_pip()
    venv_python = get_venv_python()
    
    # Upgrade pip
    run_command(f"{venv_python} -m pip install --upgrade pip")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        run_command(f"{pip_cmd} install -r requirements.txt")
    
    # Install PyInstaller for building
    run_command(f"{pip_cmd} install pyinstaller")
    
    print("✅ Dependencies installed.")

def dev():
    """Setup development environment."""
    print("🛠️ Setting up development environment...")
    install()
    
    pip_cmd = get_venv_pip()
    dev_packages = ["pytest", "black", "flake8", "mypy"]
    
    for package in dev_packages:
        run_command(f"{pip_cmd} install {package}")
    
    print("✅ Development environment ready.")

def test():
    """Run test suite."""
    print("🧪 Running test suite...")
    setup_venv()
    
    venv_python = get_venv_python()
    success = run_command(f"{venv_python} -m unittest discover tests -v")
    
    if success:
        print("✅ All tests passed.")
    else:
        print("❌ Some tests failed.")
    return success

def lint():
    """Run code linting."""
    print("🔍 Running code linting...")
    setup_venv()
    
    # Check if flake8 is available
    flake8_cmd = os.path.join(VENV_DIR, "bin", "flake8") if os.name != 'nt' else os.path.join(VENV_DIR, "Scripts", "flake8.exe")
    
    if os.path.exists(flake8_cmd):
        run_command(f"{flake8_cmd} core/ ui/ tests/ --max-line-length=100", check=False)
    else:
        print("⚠️ flake8 not installed, skipping linting")
    
    print("✅ Linting complete.")

def format_code():
    """Format code using black."""
    print("🎨 Formatting code...")
    setup_venv()
    
    black_cmd = os.path.join(VENV_DIR, "bin", "black") if os.name != 'nt' else os.path.join(VENV_DIR, "Scripts", "black.exe")
    
    if os.path.exists(black_cmd):
        run_command(f"{black_cmd} core/ ui/ tests/ --line-length=100", check=False)
    else:
        print("⚠️ black not installed, skipping formatting")
    
    print("✅ Formatting complete.")

def build():
    """Build distributable application."""
    print("🏗️ Building Eir application...")
    
    # Clean first
    clean()
    
    # Ensure dependencies are installed
    install()
    
    # Run tests
    if not test():
        print("❌ Tests failed, aborting build.")
        return False
    
    # Build with PyInstaller
    setup_venv()
    pyinstaller_cmd = os.path.join(VENV_DIR, "bin", "pyinstaller") if os.name != 'nt' else os.path.join(VENV_DIR, "Scripts", "pyinstaller.exe")
    
    success = run_command(f"{pyinstaller_cmd} --onefile --windowed {MAIN_SCRIPT}")
    
    if success:
        print("✅ Build complete. Application available in dist/")
        
        # Show what was built
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\n📁 Built files:")
            for item in dist_dir.iterdir():
                print(f"  - {item.name}")
    else:
        print("❌ Build failed.")
    
    return success

def run_app():
    """Run application in development mode."""
    print("🚀 Running Eir in development mode...")
    setup_venv()
    
    venv_python = get_venv_python()
    run_command(f"{venv_python} eir.py")

def check():
    """Run all checks."""
    print("🔎 Running all checks...")
    test_result = test()
    lint()
    return test_result

def all_pipeline():
    """Run full build pipeline."""
    print("🚀 Running full build pipeline...")
    clean()
    install()
    if test():
        return build()
    return False

def show_help():
    """Show help message."""
    print(__doc__)

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'clean': clean,
        'test': test,
        'build': build,
        'install': install,
        'dev': dev,
        'lint': lint,
        'format': format_code,
        'check': check,
        'all': all_pipeline,
        'run': run_app,
        'help': show_help
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()