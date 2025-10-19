"""
Unit tests for core.constants module
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import (
    DEFAULT_NODE_SIZE, DEFAULT_EDGE_WEIGHT, DEFAULT_WINDOW_WIDTH, 
    DEFAULT_WINDOW_HEIGHT, APP_NAME, VERSION, DEFAULT_MODEL_NAME,
    RISK_SCALE_MIN, RISK_SCALE_MAX, MAX_UNDO_HISTORY,
    MIN_ZOOM_FACTOR, MAX_ZOOM_FACTOR, DEFAULT_PADDING
)


class TestConstants(unittest.TestCase):
    """Test cases for the constants module"""
    
    def test_node_constants(self):
        """Test node-related constants"""
        self.assertIsInstance(DEFAULT_NODE_SIZE, float)
        self.assertGreater(DEFAULT_NODE_SIZE, 0)
        self.assertEqual(DEFAULT_NODE_SIZE, 24.0)
        
    def test_edge_constants(self):
        """Test edge-related constants"""
        self.assertIsInstance(DEFAULT_EDGE_WEIGHT, float)
        self.assertGreater(DEFAULT_EDGE_WEIGHT, 0)
        self.assertEqual(DEFAULT_EDGE_WEIGHT, 1.0)
        
    def test_window_constants(self):
        """Test window size constants"""
        self.assertIsInstance(DEFAULT_WINDOW_WIDTH, int)
        self.assertIsInstance(DEFAULT_WINDOW_HEIGHT, int)
        self.assertGreater(DEFAULT_WINDOW_WIDTH, 0)
        self.assertGreater(DEFAULT_WINDOW_HEIGHT, 0)
        self.assertEqual(DEFAULT_WINDOW_WIDTH, 1600)
        self.assertEqual(DEFAULT_WINDOW_HEIGHT, 1000)
        
    def test_app_metadata(self):
        """Test application metadata constants"""
        self.assertIsInstance(APP_NAME, str)
        self.assertIsInstance(VERSION, str)
        self.assertIsInstance(DEFAULT_MODEL_NAME, str)
        self.assertEqual(APP_NAME, "Eir")
        self.assertEqual(VERSION, "0.4.6")
        self.assertEqual(DEFAULT_MODEL_NAME, "Untitled STPA Project")
        
    def test_risk_scale_constants(self):
        """Test risk scale constants"""
        self.assertIsInstance(RISK_SCALE_MIN, int)
        self.assertIsInstance(RISK_SCALE_MAX, int)
        self.assertGreater(RISK_SCALE_MAX, RISK_SCALE_MIN)
        self.assertEqual(RISK_SCALE_MIN, 1)
        self.assertEqual(RISK_SCALE_MAX, 5)
        
    def test_zoom_constants(self):
        """Test zoom-related constants"""
        self.assertIsInstance(MIN_ZOOM_FACTOR, float)
        self.assertIsInstance(MAX_ZOOM_FACTOR, float)
        self.assertGreater(MAX_ZOOM_FACTOR, MIN_ZOOM_FACTOR)
        self.assertEqual(MIN_ZOOM_FACTOR, 0.1)
        self.assertEqual(MAX_ZOOM_FACTOR, 3.0)
        
    def test_misc_constants(self):
        """Test miscellaneous constants"""
        self.assertIsInstance(MAX_UNDO_HISTORY, int)
        self.assertIsInstance(DEFAULT_PADDING, int)
        self.assertGreater(MAX_UNDO_HISTORY, 0)
        self.assertGreater(DEFAULT_PADDING, 0)
        self.assertEqual(MAX_UNDO_HISTORY, 50)
        self.assertEqual(DEFAULT_PADDING, 50)


if __name__ == '__main__':
    unittest.main()
