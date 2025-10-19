"""
Unit tests for core.config module
"""

import unittest
import sys
import os
import tempfile
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import (
    EirConfig, PathConfig, UIConfig, AIConfig, PerformanceConfig, DevelopmentConfig,
    get_config, set_config, initialize_config, save_config,
    get_app_data_dir, get_documents_dir, is_debug_mode, get_max_undo_history
)


class TestPathConfig(unittest.TestCase):
    """Test cases for PathConfig class"""
    
    def test_path_config_creation(self):
        """Test PathConfig creation with default values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = PathConfig(
                app_data_dir=temp_path / "app_data",
                documents_dir=temp_path / "documents", 
                templates_dir=temp_path / "templates"
            )
            
            self.assertEqual(config.app_data_dir, temp_path / "app_data")
            self.assertEqual(config.documents_dir, temp_path / "documents")
            self.assertEqual(config.templates_dir, temp_path / "templates")
            self.assertIsNone(config.log_file)
    
    def test_path_config_post_init(self):
        """Test that PathConfig creates directories on initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = PathConfig(
                app_data_dir=temp_path / "new_app_data",
                documents_dir=temp_path / "new_documents",
                templates_dir=temp_path / "new_templates"
            )
            
            # Directories should be created automatically
            self.assertTrue(config.app_data_dir.exists())
            self.assertTrue(config.documents_dir.exists())
            self.assertTrue(config.templates_dir.exists())


class TestUIConfig(unittest.TestCase):
    """Test cases for UIConfig class"""
    
    def test_ui_config_defaults(self):
        """Test UIConfig default values"""
        config = UIConfig()
        
        self.assertEqual(config.window_width, 1600)
        self.assertEqual(config.window_height, 1000)
        self.assertEqual(config.min_window_width, 1200)
        self.assertEqual(config.min_window_height, 700)
        self.assertEqual(config.auto_save_interval, 300)
        self.assertEqual(config.recent_files_count, 10)
        self.assertEqual(config.default_zoom_level, 1.0)
        self.assertEqual(config.min_zoom_level, 0.1)
        self.assertEqual(config.max_zoom_level, 5.0)
    
    def test_ui_config_custom_values(self):
        """Test UIConfig with custom values"""
        config = UIConfig(
            window_width=1920,
            window_height=1080,
            auto_save_interval=600
        )
        
        self.assertEqual(config.window_width, 1920)
        self.assertEqual(config.window_height, 1080)
        self.assertEqual(config.auto_save_interval, 600)


class TestAIConfig(unittest.TestCase):
    """Test cases for AIConfig class"""
    
    def test_ai_config_defaults(self):
        """Test AIConfig default values"""
        config = AIConfig()
        
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.model, "llama3")
        self.assertEqual(config.timeout, 30)
        self.assertTrue(config.enable_ai)
        self.assertEqual(config.max_tokens, 4000)
        self.assertEqual(config.temperature, 0.7)


class TestPerformanceConfig(unittest.TestCase):
    """Test cases for PerformanceConfig class"""
    
    def test_performance_config_defaults(self):
        """Test PerformanceConfig default values"""
        config = PerformanceConfig()
        
        self.assertEqual(config.cache_size, 100)
        self.assertEqual(config.max_undo_history, 50)
        self.assertTrue(config.background_save)
        self.assertTrue(config.id_cache_enabled)
        self.assertEqual(config.id_preallocation_size, 100)


class TestDevelopmentConfig(unittest.TestCase):
    """Test cases for DevelopmentConfig class"""
    
    def test_development_config_defaults(self):
        """Test DevelopmentConfig default values"""
        config = DevelopmentConfig()
        
        self.assertFalse(config.debug_mode)
        self.assertEqual(config.log_level, "INFO")
        self.assertFalse(config.enable_profiling)
        self.assertFalse(config.test_mode)
        self.assertFalse(config.mock_ai)


class TestEirConfig(unittest.TestCase):
    """Test cases for EirConfig class"""
    
    def test_create_default(self):
        """Test creating default EirConfig"""
        config = EirConfig.create_default()
        
        self.assertIsInstance(config.paths, PathConfig)
        self.assertIsInstance(config.ui, UIConfig)
        self.assertIsInstance(config.ai, AIConfig)
        self.assertIsInstance(config.performance, PerformanceConfig)
        self.assertIsInstance(config.development, DevelopmentConfig)
    
    def test_config_validation(self):
        """Test config validation"""
        config = EirConfig.create_default()
        self.assertTrue(config.validate())
        
        # Test invalid config
        config.ui.window_width = -100
        self.assertFalse(config.validate())
    
    def test_save_and_load_config(self):
        """Test saving and loading config to/from file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            # Create and save config
            original_config = EirConfig.create_default()
            original_config.ui.window_width = 1920
            original_config.development.debug_mode = True
            original_config.save_to_file(config_path)
            
            # Load config and verify
            loaded_config = EirConfig.load_from_file(config_path)
            self.assertEqual(loaded_config.ui.window_width, 1920)
            self.assertTrue(loaded_config.development.debug_mode)
    
    def test_environment_variable_integration(self):
        """Test environment variable integration"""
        config = EirConfig.create_default()
        
        # Set environment variable
        os.environ["EIR_DEBUG"] = "true"
        config.update_from_env()
        
        self.assertTrue(config.development.debug_mode)
        
        # Clean up
        if "EIR_DEBUG" in os.environ:
            del os.environ["EIR_DEBUG"]


class TestConfigGlobals(unittest.TestCase):
    """Test cases for global config functions"""
    
    def setUp(self):
        """Set up clean config state for each test"""
        # Reset global config
        initialize_config()
    
    def test_initialize_config(self):
        """Test config initialization"""
        config = initialize_config()
        self.assertIsInstance(config, EirConfig)
        
        # Should be the same instance when called again
        config2 = get_config()
        self.assertIs(config, config2)
    
    def test_set_and_get_config(self):
        """Test setting and getting config"""
        new_config = EirConfig.create_default()
        new_config.ui.window_width = 2560
        
        set_config(new_config)
        retrieved_config = get_config()
        
        self.assertEqual(retrieved_config.ui.window_width, 2560)
    
    def test_helper_functions(self):
        """Test config helper functions"""
        config = get_config()
        
        # Test helper function results
        self.assertEqual(get_app_data_dir(), config.paths.app_data_dir)
        self.assertEqual(get_documents_dir(), config.paths.documents_dir)
        self.assertEqual(is_debug_mode(), config.development.debug_mode)
        self.assertEqual(get_max_undo_history(), config.performance.max_undo_history)


if __name__ == '__main__':
    unittest.main()