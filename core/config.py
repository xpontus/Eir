"""
Configuration management for Eir application.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, asdict, field
import tempfile


@dataclass
class PathConfig:
    """Path configuration settings"""
    app_data_dir: Path
    documents_dir: Path
    templates_dir: Path
    log_file: Optional[Path] = None
    
    def __post_init__(self):
        """Ensure all directories exist"""
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class UIConfig:
    """User interface configuration settings"""
    window_width: int = 1600
    window_height: int = 1000
    min_window_width: int = 1200
    min_window_height: int = 700
    auto_save_interval: int = 300  # seconds
    recent_files_count: int = 10
    default_zoom_level: float = 1.0
    min_zoom_level: float = 0.1
    max_zoom_level: float = 5.0


@dataclass 
class AIConfig:
    """AI integration configuration settings"""
    provider: str = "ollama"
    model: str = "llama3"
    base_url: str = "http://localhost:11434"
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 4000
    enable_ai: bool = True


@dataclass
class PerformanceConfig:
    """Performance-related configuration settings"""
    max_undo_history: int = 50
    large_model_threshold: int = 500
    background_save: bool = True
    lazy_loading: bool = True
    cache_size: int = 100
    
    # ID generation optimization
    id_cache_enabled: bool = True
    id_preallocation_size: int = 100


@dataclass
class DevelopmentConfig:
    """Development and debugging configuration"""
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_profiling: bool = False
    test_mode: bool = False
    mock_ai: bool = False


@dataclass
class EirConfig:
    """Central configuration for Eir application"""
    paths: PathConfig
    ui: UIConfig = field(default_factory=UIConfig)
    ai: AIConfig = field(default_factory=AIConfig) 
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    
    # Application metadata
    version: str = "0.4.6"
    app_name: str = "Eir"
    organization: str = "Eir"
    
    @classmethod
    def get_default_paths(cls) -> PathConfig:
        """Get default path configuration based on platform"""
        if os.name == 'nt':  # Windows
            base_dir = Path.home() / "AppData" / "Local" / "Eir"
        elif os.name == 'posix':  # macOS/Linux
            if os.uname().sysname == 'Darwin':  # macOS
                base_dir = Path.home() / "Library" / "Application Support" / "Eir"
            else:  # Linux
                base_dir = Path.home() / ".config" / "eir"
        else:
            # Fallback
            base_dir = Path.home() / ".eir"
        
        return PathConfig(
            app_data_dir=base_dir,
            documents_dir=base_dir / "documents",
            templates_dir=base_dir / "templates",
            log_file=base_dir / "eir.log"
        )
    
    @classmethod
    def create_default(cls) -> 'EirConfig':
        """Create default configuration"""
        return cls(paths=cls.get_default_paths())
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> 'EirConfig':
        """Load configuration from file"""
        if config_path is None:
            config_path = cls.get_default_config_path()
        
        if not config_path.exists():
            # Create default config if none exists
            config = cls.create_default()
            config.save_to_file(config_path)
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle paths specially since they need to be Path objects
            if 'paths' in data:
                paths_data = data['paths']
                # Convert string paths to Path objects
                for key, value in paths_data.items():
                    if value is not None:
                        paths_data[key] = Path(value)
                data['paths'] = PathConfig(**paths_data)
            
            # Create other config sections
            if 'ui' in data:
                data['ui'] = UIConfig(**data['ui'])
            if 'ai' in data:
                data['ai'] = AIConfig(**data['ai'])
            if 'performance' in data:
                data['performance'] = PerformanceConfig(**data['performance'])
            if 'development' in data:
                data['development'] = DevelopmentConfig(**data['development'])
            
            return cls(**data)
            
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # If config is corrupted, create default and backup the old one
            if config_path.exists():
                backup_path = config_path.with_suffix('.backup')
                config_path.rename(backup_path)
            
            config = cls.create_default()
            config.save_to_file(config_path)
            return config
    
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file"""
        if config_path is None:
            config_path = self.get_default_config_path()
        
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and handle Path objects
        data = asdict(self)
        
        # Convert Path objects to strings for JSON serialization
        if 'paths' in data:
            paths_data = data['paths']
            for key, value in paths_data.items():
                if isinstance(value, Path):
                    paths_data[key] = str(value)
                elif value is None:
                    paths_data[key] = None
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
    
    @classmethod
    def get_default_config_path(cls) -> Path:
        """Get the default configuration file path"""
        paths = cls.get_default_paths()
        return paths.app_data_dir / "config.json"
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables"""
        # AI configuration from environment
        if os.getenv("EIR_AI_PROVIDER"):
            self.ai.provider = os.getenv("EIR_AI_PROVIDER")
        if os.getenv("EIR_AI_MODEL"):
            self.ai.model = os.getenv("EIR_AI_MODEL")
        if os.getenv("EIR_AI_BASE_URL"):
            self.ai.base_url = os.getenv("EIR_AI_BASE_URL")
        if os.getenv("EIR_AI_TIMEOUT"):
            try:
                self.ai.timeout = int(os.getenv("EIR_AI_TIMEOUT"))
            except ValueError:
                pass
        
        # Development configuration
        if os.getenv("EIR_DEBUG"):
            self.development.debug_mode = os.getenv("EIR_DEBUG").lower() in ("true", "1", "yes")
        if os.getenv("EIR_LOG_LEVEL"):
            self.development.log_level = os.getenv("EIR_LOG_LEVEL").upper()
        if os.getenv("EIR_TEST_MODE"):
            self.development.test_mode = os.getenv("EIR_TEST_MODE").lower() in ("true", "1", "yes")
        
        # Performance configuration
        if os.getenv("EIR_MAX_UNDO"):
            try:
                self.performance.max_undo_history = int(os.getenv("EIR_MAX_UNDO"))
            except ValueError:
                pass
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory for the application"""
        temp_dir = Path(tempfile.gettempdir()) / "eir"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features should be enabled"""
        return self.ai.enable_ai and not self.development.mock_ai
    
    def get_log_path(self) -> Optional[Path]:
        """Get the log file path"""
        return self.paths.log_file
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        try:
            # Validate UI settings
            assert self.ui.window_width > 0
            assert self.ui.window_height > 0
            assert self.ui.auto_save_interval > 0
            assert 0 < self.ui.default_zoom_level <= self.ui.max_zoom_level
            assert self.ui.min_zoom_level > 0
            
            # Validate performance settings
            assert self.performance.max_undo_history > 0
            assert self.performance.large_model_threshold > 0
            assert self.performance.cache_size > 0
            
            # Validate AI settings
            assert self.ai.timeout > 0
            assert 0 <= self.ai.temperature <= 2.0
            assert self.ai.max_tokens > 0
            
            # Validate paths exist
            assert self.paths.app_data_dir.exists()
            assert self.paths.documents_dir.exists()
            assert self.paths.templates_dir.exists()
            
            return True
        except AssertionError:
            return False


# Global configuration instance
_global_config: Optional[EirConfig] = None


def get_config() -> EirConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = EirConfig.load_from_file()
        _global_config.update_from_env()
    return _global_config


def set_config(config: EirConfig) -> None:
    """Set the global configuration instance"""
    global _global_config
    _global_config = config


def initialize_config(config_path: Optional[Path] = None) -> EirConfig:
    """Initialize the global configuration"""
    global _global_config
    _global_config = EirConfig.load_from_file(config_path)
    _global_config.update_from_env()
    
    # Validate configuration
    if not _global_config.validate():
        raise RuntimeError("Configuration validation failed")
    
    return _global_config


def save_config() -> None:
    """Save the current global configuration"""
    config = get_config()
    config.save_to_file()


# Convenience functions for common configuration access
def get_app_data_dir() -> Path:
    """Get application data directory"""
    return get_config().paths.app_data_dir


def get_documents_dir() -> Path:
    """Get documents directory"""
    return get_config().paths.documents_dir


def get_log_file() -> Optional[Path]:
    """Get log file path"""
    return get_config().paths.log_file


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return get_config().development.debug_mode


def get_max_undo_history() -> int:
    """Get maximum undo history size"""
    return get_config().performance.max_undo_history