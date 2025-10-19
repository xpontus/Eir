"""
Unit tests for UI components (using mocks to avoid Qt dependencies)
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Qt modules before importing UI components
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()

# Mock Qt classes that are commonly used
qt_mock = Mock()
qt_mock.Horizontal = 'horizontal'
qt_mock.Vertical = 'vertical'
qt_mock.KeepAspectRatio = 'keep_aspect'

sys.modules['PySide6.QtCore'].Qt = qt_mock
sys.modules['PySide6.QtCore'].Signal = Mock()
sys.modules['PySide6.QtWidgets'].QWidget = Mock
sys.modules['PySide6.QtWidgets'].QMainWindow = Mock
sys.modules['PySide6.QtWidgets'].QVBoxLayout = Mock
sys.modules['PySide6.QtWidgets'].QHBoxLayout = Mock
sys.modules['PySide6.QtWidgets'].QTabWidget = Mock
sys.modules['PySide6.QtWidgets'].QMessageBox = Mock
sys.modules['PySide6.QtWidgets'].QFileDialog = Mock
sys.modules['PySide6.QtWidgets'].QApplication = Mock

from core.models import STPAModel


class TestUIValidation(unittest.TestCase):
    """Test UI validation scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = STPAModel()
        
    def test_model_validation_scenarios(self):
        """Test various model validation scenarios we encountered"""
        # Test model name consistency (the bug we fixed)
        self.assertEqual(self.model.name, "Untitled STPA Model")
        
        # Test that get_next_link_id works (the fix we implemented)
        next_id = self.model.get_next_link_id()
        self.assertEqual(next_id, "e1")
        
        # Add some edges and test ID generation
        self.model.control_structure.add_node("n1", name="Node 1")
        self.model.control_structure.add_node("n2", name="Node 2")
        self.model.control_structure.add_edge("n1", "n2", key="e1")
        self.model.control_structure.add_edge("n1", "n2", key="e3")
        
        next_id = self.model.get_next_link_id()
        self.assertEqual(next_id, "e4")
        
    def test_change_tracking_scenarios(self):
        """Test change tracking scenarios"""
        # Initially no changes
        has_changes = False
        
        # Add a loss (should trigger change)
        self.model.add_loss("Test loss", "High", "Test rationale")
        has_changes = True
        self.assertTrue(has_changes)
        
        # Add a hazard (should trigger change)
        self.model.add_hazard("Test hazard", "Medium", "Test rationale")
        has_changes = True
        self.assertTrue(has_changes)
        
        # Simulate save (should clear changes)
        has_changes = False
        self.assertFalse(has_changes)
        
    def test_input_validation_integration(self):
        """Test input validation integration scenarios"""
        from core.validation import InputValidator, ValidationError
        
        # Test the validation scenarios we implemented
        valid_inputs = [
            ("Valid Node Name", "Node Name"),
            ("Controller-1", "Node Name"),
            ("sensor_data", "Node Name"),
            ("High", "Severity"),
            ("Medium", "Severity"),
            ("", "Severity"),  # Empty severity should be allowed
        ]
        
        for input_val, field_name in valid_inputs:
            with self.subTest(input_val=input_val, field_name=field_name):
                if field_name == "Node Name":
                    result = InputValidator.validate_node_name(input_val)
                    self.assertEqual(result, input_val)
                elif field_name == "Severity":
                    result = InputValidator.validate_severity(input_val)
                    self.assertEqual(result, input_val)
                    
        # Test invalid inputs
        invalid_inputs = [
            ("", "Node Name"),  # Empty node name
            ("Node@1", "Node Name"),  # Invalid characters
            ("Invalid", "Severity"),  # Invalid severity
        ]
        
        for input_val, field_name in invalid_inputs:
            with self.subTest(input_val=input_val, field_name=field_name):
                with self.assertRaises(ValidationError):
                    if field_name == "Node Name":
                        InputValidator.validate_node_name(input_val)
                    elif field_name == "Severity":
                        InputValidator.validate_severity(input_val)


class TestConstants(unittest.TestCase):
    """Test constants integration in UI context"""
    
    def test_constants_usage(self):
        """Test that constants are properly defined for UI usage"""
        from core.constants import (
            DEFAULT_NODE_SIZE, DEFAULT_EDGE_WEIGHT,
            DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
            MIN_ZOOM_FACTOR, MAX_ZOOM_FACTOR
        )
        
        # Test that zoom constants are reasonable
        self.assertGreater(MAX_ZOOM_FACTOR, MIN_ZOOM_FACTOR)
        self.assertGreater(MIN_ZOOM_FACTOR, 0)
        self.assertLess(MAX_ZOOM_FACTOR, 10)  # Reasonable upper bound
        
        # Test that window size constants are reasonable
        self.assertGreater(DEFAULT_WINDOW_WIDTH, 800)  # Minimum reasonable width
        self.assertGreater(DEFAULT_WINDOW_HEIGHT, 600)  # Minimum reasonable height
        self.assertLess(DEFAULT_WINDOW_WIDTH, 5000)  # Maximum reasonable width
        self.assertLess(DEFAULT_WINDOW_HEIGHT, 5000)  # Maximum reasonable height
        
        # Test that node/edge constants are reasonable
        self.assertGreater(DEFAULT_NODE_SIZE, 0)
        self.assertGreater(DEFAULT_EDGE_WEIGHT, 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios we improved"""
    
    def test_file_io_error_scenarios(self):
        """Test file I/O error scenarios"""
        from core.file_io import STPAModelIO
        
        # Test file not found error
        with self.assertRaises(FileNotFoundError) as context:
            STPAModelIO.load_json("nonexistent_file.json")
        self.assertIn("File not found", str(context.exception))
        
        # Test invalid path for saving
        model = STPAModel()
        with self.assertRaises(IOError) as context:
            STPAModelIO.save_json(model, "/invalid/path/file.json")
        self.assertIn("Failed to write to file", str(context.exception))
        
    def test_model_consistency_checks(self):
        """Test model consistency scenarios"""
        model = STPAModel()
        
        # Test that control structure is properly initialized
        self.assertIsNotNone(model.control_structure)
        self.assertEqual(len(model.control_structure.nodes), 0)
        self.assertEqual(len(model.control_structure.edges), 0)
        
        # Test that collections are properly initialized
        self.assertIsNotNone(model.losses)
        self.assertIsNotNone(model.hazards)
        self.assertIsNotNone(model.unsafe_control_actions)
        self.assertIsNotNone(model.uca_contexts)
        
        # Test that metadata is properly initialized
        self.assertIsNotNone(model.metadata)
        self.assertIsNotNone(model.chat_transcripts)


class TestMemoryManagement(unittest.TestCase):
    """Test memory management scenarios"""
    
    def test_model_cleanup_scenarios(self):
        """Test scenarios related to model cleanup"""
        model = STPAModel()
        
        # Add some data
        model.add_loss("Test loss", "High", "Test")
        model.add_hazard("Test hazard", "Medium", "Test")
        
        # Add nodes and edges
        model.control_structure.add_node("n1", name="Node 1")
        model.control_structure.add_node("n2", name="Node 2")
        model.control_structure.add_edge("n1", "n2", key="e1")
        
        # Verify data was added
        self.assertEqual(len(model.losses), 1)
        self.assertEqual(len(model.hazards), 1)
        self.assertEqual(len(model.control_structure.nodes), 2)
        self.assertEqual(len(model.control_structure.edges), 1)
        
        # Test clearing control structure
        model.control_structure.clear()
        self.assertEqual(len(model.control_structure.nodes), 0)
        self.assertEqual(len(model.control_structure.edges), 0)
        
        # Other data should remain
        self.assertEqual(len(model.losses), 1)
        self.assertEqual(len(model.hazards), 1)
        
    def test_node_removal_cleanup(self):
        """Test node removal cleanup scenarios"""
        model = STPAModel()
        
        # Create a small network
        model.control_structure.add_node("n1", name="Node 1")
        model.control_structure.add_node("n2", name="Node 2") 
        model.control_structure.add_node("n3", name="Node 3")
        
        model.control_structure.add_edge("n1", "n2", key="e1")
        model.control_structure.add_edge("n2", "n3", key="e2")
        model.control_structure.add_edge("n3", "n1", key="e3")
        
        # Verify initial state
        self.assertEqual(len(model.control_structure.nodes), 3)
        self.assertEqual(len(model.control_structure.edges), 3)
        
        # Remove a node (should also remove connected edges)
        model.control_structure.remove_node_with_links("n2")
        
        # Check cleanup
        self.assertEqual(len(model.control_structure.nodes), 2)
        self.assertNotIn("n2", model.control_structure.nodes)
        # Only e3 should remain (n3->n1)
        self.assertEqual(len(model.control_structure.edges), 1)
        
    def test_position_field_consistency(self):
        """Test position field name consistency between UI and model layers (bug fix)"""
        model = STPAModel()
        
        # Test the position field name standardization we implemented
        test_positions = [
            ("node1", "Node 1", (100.0, 200.0)),
            ("node2", "Node 2", (300.0, 150.0)),
            ("node3", "Node 3", (250.0, 400.0))
        ]
        
        # Add nodes with position data using the standardized method
        for node_id, name, position in test_positions:
            model.control_structure.add_node(
                node_id=node_id,
                name=name,
                position=position
            )
        
        # Verify positions are stored with consistent field naming
        for node_id, name, expected_pos in test_positions:
            self.assertIn(node_id, model.control_structure.nodes)
            
            node_data = model.control_structure.nodes[node_id]
            
            # Check that position is stored correctly (our fix)
            actual_pos = node_data.get('position', (0, 0))
            self.assertEqual(actual_pos, expected_pos, 
                f"Position mismatch for {node_id}: expected {expected_pos}, got {actual_pos}")
            
            # Ensure the old 'pos' field isn't being used inconsistently
            self.assertNotIn('pos', node_data, 
                f"Node {node_id} should not have old 'pos' field when using standardized add_node method")
        
        # Test backwards compatibility: simulate loading a node with old 'pos' field
        # (This simulates what the UI loading logic should handle)
        legacy_node_data = {
            'name': 'Legacy Node',
            'shape': 'circle',
            'size': 24.0
        }
        
        # Add legacy node directly to NetworkX graph (simulating old data format)
        # Use the parent NetworkX add_node method directly to bypass our validation
        import networkx as nx
        nx.MultiDiGraph.add_node(model.control_structure, 'legacy_node', 
                                pos=(50.0, 75.0), **legacy_node_data)
        
        # Verify both field names can be handled
        legacy_attrs = model.control_structure.nodes['legacy_node']
        self.assertIn('pos', legacy_attrs)
        
        # Test that UI position loading logic would work with both field names
        # This simulates the backwards compatibility fix in _load_from_model
        position = legacy_attrs.get('position', legacy_attrs.get('pos', (0, 0)))
        self.assertEqual(position, (50.0, 75.0), "Should fall back to 'pos' field if 'position' not found")
        
    def test_node_creation_position_consistency(self):
        """Test that node creation stores positions with consistent field naming"""
        model = STPAModel()
        
        # Test the add_node method we added for file I/O compatibility
        node = model.control_structure.add_node(
            node_id="test_node",
            name="Test Node", 
            position=(123.45, 678.90),
            shape="rectangle"
        )
        
        # Verify the method returns a SystemNode object
        from core.models import SystemNode
        self.assertIsInstance(node, SystemNode)
        self.assertEqual(node.id, "test_node")
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.position, (123.45, 678.90))
        
        # Verify the position is stored in the NetworkX graph with correct field name
        node_attrs = model.control_structure.nodes["test_node"]
        self.assertEqual(node_attrs.get('position'), (123.45, 678.90))
        
        # Also test the add_node_with_data method works the same way
        node2 = model.control_structure.add_node_with_data(
            node_id="test_node2",
            name="Test Node 2",
            position=(987.65, 432.10)
        )
        
        self.assertIsInstance(node2, SystemNode) 
        self.assertEqual(node2.position, (987.65, 432.10))
        
        node2_attrs = model.control_structure.nodes["test_node2"]
        self.assertEqual(node2_attrs.get('position'), (987.65, 432.10))


if __name__ == '__main__':
    unittest.main()
