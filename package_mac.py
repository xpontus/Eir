#!/usr/bin/env python3
"""
Eir Mac App Distribution Builder
Creates a distributable DMG file for the Eir STPA tool.
"""

import os
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command with error handling."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0

def create_dmg():
    """Create a distributable DMG file."""
    print("🏗️ Creating distributable DMG...")
    
    # Clean any existing DMG files
    dmg_files = list(Path(".").glob("Eir*.dmg"))
    for dmg_file in dmg_files:
        dmg_file.unlink()
        print(f"  Removed existing {dmg_file}")
    
    # Create temporary directory for DMG contents
    dmg_dir = Path("dmg_temp")
    if dmg_dir.exists():
        shutil.rmtree(dmg_dir)
    dmg_dir.mkdir()
    
    # Copy the app to DMG directory
    app_path = Path("dist/Eir.app")
    if not app_path.exists():
        print("❌ Eir.app not found. Please build the app first.")
        return False
    
    shutil.copytree(app_path, dmg_dir / "Eir.app")
    
    # Create Applications folder symlink
    run_command(f"ln -s /Applications '{dmg_dir}/Applications'")
    
    # Create README for the DMG
    readme_content = """Eir STPA Tool v0.4.6

Installation Instructions:
1. Drag Eir.app to the Applications folder
2. Launch from Applications or Spotlight

The Eir STPA (System-Theoretic Process Analysis) Tool helps you:
• Create control structure diagrams
• Analyze losses and hazards  
• Perform UCA (Unsafe Control Actions) analysis
• Generate comprehensive safety documentation

For support and documentation, visit:
https://github.com/eir-project

Built with PySide6 and optimized for macOS 11.0+
"""
    
    with open(dmg_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    # Create the DMG
    dmg_name = "Eir-STPA-Tool-v0.4.6.dmg"
    success = run_command(f"""
        hdiutil create -volname "Eir STPA Tool" \
        -srcfolder "{dmg_dir}" \
        -ov -format UDZO \
        -imagekey zlib-level=9 \
        "{dmg_name}"
    """)
    
    # Clean up temp directory
    shutil.rmtree(dmg_dir)
    
    if success and Path(dmg_name).exists():
        size = Path(dmg_name).stat().st_size / (1024 * 1024)
        print(f"✅ DMG created successfully: {dmg_name} ({size:.1f} MB)")
        print(f"📦 Ready for distribution!")
        return True
    else:
        print("❌ Failed to create DMG")
        return False

def build_and_package():
    """Build the app and create distributable package."""
    print("🚀 Building and packaging Eir for distribution...")
    
    # Clean previous builds
    for path in ["build", "dist"]:
        if Path(path).exists():
            shutil.rmtree(path)
            print(f"  Cleaned {path}/")
    
    # Build the app
    venv_python = Path(".venv/bin/python")
    venv_pyinstaller = Path(".venv/bin/pyinstaller")
    
    if not venv_pyinstaller.exists():
        print("Installing PyInstaller...")
        run_command(f"{venv_python} -m pip install pyinstaller")
    
    # Build with custom spec
    success = run_command(f"{venv_pyinstaller} eir_standalone.spec")
    
    if success and Path("dist/Eir.app").exists():
        print("✅ App build completed")
        
        # Create DMG
        return create_dmg()
    else:
        print("❌ App build failed")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "dmg-only":
        create_dmg()
    else:
        build_and_package()