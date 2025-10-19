"""
Constants for Eir with dynamic configuration support.

This module provides backward compatibility while integrating with 
the new configuration system.
"""

from typing import Union, Optional

# Static constants that don't change
APP_NAME = "Eir"
VERSION = "0.4.6"
ORGANIZATION = "Eir"

# Risk scale constants
RISK_SCALE_MIN = 1
RISK_SCALE_MAX = 5

# Graphics constants  
NODE_SELECTION_COLOR = "#FF0000"  # Red
NODE_SELECTION_WIDTH = 2
EDGE_DEFAULT_WIDTH = 2
FONT_SIZE_DEFAULT = 10
FONT_FAMILY_DEFAULT = "Arial"

# File constants
SUPPORTED_FILE_EXTENSIONS = [".json"]


def get_config_value(key: str, default_value: Union[int, float, str, bool]) -> Union[int, float, str, bool]:
    """
    Get a configuration value with fallback to default.
    
    Args:
        key: Configuration key path (e.g., 'ui.window_width')
        default_value: Default value if config is not available
        
    Returns:
        Configuration value or default
    """
    try:
        from core.config import get_config
        config = get_config()
        
        # Navigate the config object based on the key path
        keys = key.split('.')
        value = config
        for k in keys:
            value = getattr(value, k)
        return value
    except (ImportError, AttributeError, Exception):
        # Fallback to default if config system not available
        return default_value


# Dynamic constants with configuration system integration

def get_default_node_size() -> float:
    """Default node size from configuration or fallback"""
    return get_config_value('ui.default_node_size', 24.0)

def get_default_window_width() -> int:
    """Default window width from configuration"""
    return get_config_value('ui.window_width', 1600)

def get_default_window_height() -> int:
    """Default window height from configuration"""
    return get_config_value('ui.window_height', 1000)

def get_min_window_width() -> int:
    """Minimum window width from configuration"""
    return get_config_value('ui.min_window_width', 1200)

def get_min_window_height() -> int:
    """Minimum window height from configuration"""
    return get_config_value('ui.min_window_height', 700)

def get_default_model_name() -> str:
    """Default model name"""
    return "Untitled STPA Project"

def get_max_recent_files() -> int:
    """Maximum number of recent files to track"""
    return get_config_value('ui.recent_files_count', 10)

def get_max_undo_history() -> int:
    """Maximum undo history size"""
    return get_config_value('performance.max_undo_history', 50)

def get_min_zoom_factor() -> float:
    """Minimum zoom factor"""
    return get_config_value('ui.min_zoom_level', 0.1)

def get_max_zoom_factor() -> float:
    """Maximum zoom factor"""
    return get_config_value('ui.max_zoom_level', 3.0)

def get_default_padding() -> int:
    """Default UI padding"""
    return 50

def get_default_edge_weight() -> float:
    """Default edge weight"""
    return 1.0


# Backward compatibility - these will be deprecated in future versions
# but are kept for existing code

try:
    from core.config import get_config
    _config = get_config()
    
    # Populate backward compatibility constants
    DEFAULT_NODE_SIZE_COMPAT = _config.ui.window_width if hasattr(_config, 'ui') else 24.0
    DEFAULT_WINDOW_WIDTH_COMPAT = _config.ui.window_width if hasattr(_config, 'ui') else 1600
    DEFAULT_WINDOW_HEIGHT_COMPAT = _config.ui.window_height if hasattr(_config, 'ui') else 1000
    MAX_UNDO_HISTORY_COMPAT = _config.performance.max_undo_history if hasattr(_config, 'performance') else 50
    
except (ImportError, Exception):
    # Fallback values when config system is not available
    DEFAULT_NODE_SIZE_COMPAT = 24.0
    DEFAULT_WINDOW_WIDTH_COMPAT = 1600
    DEFAULT_WINDOW_HEIGHT_COMPAT = 1000
    MAX_UNDO_HISTORY_COMPAT = 50

# For code that still uses the old names (to be deprecated)
DEFAULT_EDGE_WEIGHT = 1.0
DEFAULT_MODEL_NAME = "Untitled STPA Project"
MAX_RECENT_FILES = 10
MIN_ZOOM_FACTOR = 0.1
MAX_ZOOM_FACTOR = 3.0
DEFAULT_PADDING = 50

# Backward compatibility constants that the UI expects
DEFAULT_WINDOW_WIDTH = get_default_window_width()
DEFAULT_WINDOW_HEIGHT = get_default_window_height() 
MIN_WINDOW_WIDTH = get_min_window_width()
MIN_WINDOW_HEIGHT = get_min_window_height()
DEFAULT_NODE_SIZE = get_default_node_size()
MAX_UNDO_HISTORY = get_max_undo_history()
MIN_ZOOM_LEVEL = get_min_zoom_factor()
MAX_ZOOM_LEVEL = get_max_zoom_factor()
DEFAULT_PROJECT_NAME = get_default_model_name()

# Additional constants the application might need
DEFAULT_ZOOM_LEVEL = 1.0
MIN_NODE_SIZE = 12.0
MAX_NODE_SIZE = 100.0
NODE_SELECTION_TOLERANCE = 5.0
DEFAULT_EDGE_OFFSET = 15.0
EDGE_ARROW_SIZE = 8.0
EDGE_SELECTION_TOLERANCE = 3.0
ZOOM_STEP = 0.1


def get_ui_constant(name: str, default: Union[int, float, str] = None) -> Union[int, float, str]:
    """
    Get a UI constant by name with optional default.
    
    Args:
        name: Constant name
        default: Default value if not found
        
    Returns:
        Constant value
    """
    # Map old constant names to new config paths
    constant_map = {
        'DEFAULT_NODE_SIZE': 'ui.default_node_size',
        'DEFAULT_WINDOW_WIDTH': 'ui.window_width', 
        'DEFAULT_WINDOW_HEIGHT': 'ui.window_height',
        'MIN_WINDOW_WIDTH': 'ui.min_window_width',
        'MIN_WINDOW_HEIGHT': 'ui.min_window_height',
        'MAX_UNDO_HISTORY': 'performance.max_undo_history',
        'MIN_ZOOM_FACTOR': 'ui.min_zoom_level',
        'MAX_ZOOM_FACTOR': 'ui.max_zoom_level'
    }
    
    if name in constant_map:
        config_key = constant_map[name]
        fallback_value = default if default is not None else globals().get(f"{name}_COMPAT", 0)
        return get_config_value(config_key, fallback_value)
    
    # Return from globals if exists
    return globals().get(name, default)


# Performance constants
def get_performance_constant(name: str, default: Union[int, float] = None) -> Union[int, float]:
    """Get a performance-related constant"""
    performance_map = {
        'MAX_UNDO_HISTORY': 'performance.max_undo_history',
        'LARGE_MODEL_THRESHOLD': 'performance.large_model_threshold',
        'CACHE_SIZE': 'performance.cache_size'
    }
    
    if name in performance_map:
        config_key = performance_map[name]
        fallback_value = default if default is not None else 50
        return get_config_value(config_key, fallback_value)
    
    return default
