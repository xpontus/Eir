#!/usr/bin/env python3
"""
Eir - Systems-Theoretic Process Analysis Tool
Main entry point for Eir.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Fix Qt plugin path issues on macOS
def fix_qt_plugin_path():
    """Set Qt plugin path to fix 'cocoa' plugin not found issues"""
    try:
        import PySide6
        pyside6_dir = os.path.dirname(PySide6.__file__)
        qt_plugin_path = os.path.join(pyside6_dir, 'Qt', 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugin_path, 'platforms')
    except ImportError:
        pass

# Call the fix before importing Qt
fix_qt_plugin_path()

# Import configuration and logging before other modules
from core.config import initialize_config, get_config
from core.logging_config import initialize_logging, get_logger


def setup_application() -> bool:
    """
    Initialize the application configuration and logging.
    
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        # Initialize configuration first
        config = initialize_config()
        
        # Initialize logging with configuration
        logger = initialize_logging()
        
        # Log application startup
        app_logger = get_logger('eir.startup')
        app_logger.info(f"Starting Eir v{config.version}")
        app_logger.info(f"Application data directory: {config.paths.app_data_dir}")
        app_logger.info(f"Debug mode: {config.development.debug_mode}")
        app_logger.info(f"AI enabled: {config.is_ai_enabled()}")
        
        return True
        
    except Exception as e:
        # Use print since logging might not be set up yet
        print(f"Error during application setup: {e}")
        return False


def main() -> int:
    """
    Main entry point for the Eir application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Setup application configuration and logging
    if not setup_application():
        print("Failed to initialize application")
        return 1
    
    # Import UI after setup to ensure logging is available
    try:
        from ui.main_window import main as ui_main
        return ui_main()
    except ImportError as e:
        logger = get_logger('eir.startup')
        logger.error(f"Failed to import UI components: {e}")
        logger.error("Please ensure all dependencies are installed")
        print(f"Error: Failed to import UI components: {e}")
        print("Please run: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger = get_logger('eir.startup')
        logger.error(f"Unexpected error starting application: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    # Enable Python's fault handler for better crash debugging
    import faulthandler
    faulthandler.enable()
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
