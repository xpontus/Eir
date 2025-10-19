"""
Unit tests for core.file_io module
"""

import unittest
import json
import tempfile
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_io import STPAModelIO
from core.models import STPAModel, Loss, Hazard, UnsafeControlAction, UCAContext


class TestSTPAModelIO(unittest.TestCase):
    """Test cases for the STPAModelIO class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = STPAModel()
        self.model.name = "Test Model"
        self.model.description = "A test model for unit testing"
        
        # Add some test data
        self.model.add_loss("Loss of life", "High", "Human safety critical")
        self.model.add_hazard("Vehicle collision", "High", "Could cause loss of life", ["0"])
        
        # Add nodes to control structure
        self.model.control_structure.add_node(
            "controller",
            name="Controller",
            position=(100.0, 50.0),
            shape="rectangle"
        )
        self.model.control_structure.add_node(
            "actuator", 
            name="Actuator",
            position=(100.0, 150.0),
            shape="circle"
        )
        
        # Add edge
        self.model.control_structure.add_edge(
            "controller", "actuator",
            key="control_signal",
            name="Control Signal",
            weight=1.0
        )
        
    def test_model_to_dict(self):
        """Test converting model to dictionary"""
        data = STPAModelIO._model_to_dict(self.model)
        
        # Check basic structure
        self.assertIsInstance(data, dict)
        self.assertIn('name', data)
        self.assertIn('version', data)
        self.assertIn('description', data)
        self.assertIn('control_structure', data)
        self.assertIn('losses', data)
        self.assertIn('hazards', data)
        
        # Check model metadata
        self.assertEqual(data['name'], "Test Model")
        self.assertEqual(data['description'], "A test model for unit testing")
        
        # Check control structure
        cs_data = data['control_structure']
        self.assertIn('nodes', cs_data)
        self.assertIn('edges', cs_data)
        self.assertEqual(len(cs_data['nodes']), 2)
        self.assertEqual(len(cs_data['edges']), 1)
        
        # Check node data
        controller_node = next(n for n in cs_data['nodes'] if n['id'] == 'controller')
        self.assertEqual(controller_node['name'], 'Controller')
        self.assertEqual(controller_node['shape'], 'rectangle')
        self.assertEqual(controller_node['position'], [100.0, 50.0])
        
        # Check edge data
        edge = cs_data['edges'][0]
        self.assertEqual(edge['source_id'], 'controller')
        self.assertEqual(edge['target_id'], 'actuator')
        self.assertEqual(edge['name'], 'Control Signal')
        
        # Check losses and hazards
        self.assertEqual(len(data['losses']), 1)
        self.assertEqual(len(data['hazards']), 1)
        self.assertEqual(data['losses'][0]['description'], "Loss of life")
        self.assertEqual(data['hazards'][0]['description'], "Vehicle collision")
        
    def test_dict_to_model(self):
        """Test converting dictionary to model"""
        # First convert model to dict
        original_data = STPAModelIO._model_to_dict(self.model)
        
        # Then convert back to model
        restored_model = STPAModelIO._dict_to_model(original_data)
        
        # Check basic properties
        self.assertEqual(restored_model.name, self.model.name)
        self.assertEqual(restored_model.description, self.model.description)
        
        # Check control structure
        self.assertEqual(len(restored_model.control_structure.nodes), 2)
        self.assertEqual(len(restored_model.control_structure.edges), 1)
        
        # Check nodes
        self.assertIn('controller', restored_model.control_structure.nodes)
        self.assertIn('actuator', restored_model.control_structure.nodes)
        
        controller_attrs = restored_model.control_structure.nodes['controller']
        self.assertEqual(controller_attrs['name'], 'Controller')
        self.assertEqual(controller_attrs['shape'], 'rectangle')
        
        # Check edges
        self.assertTrue(restored_model.control_structure.has_edge('controller', 'actuator'))
        
        # Check losses and hazards
        self.assertEqual(len(restored_model.losses), 1)
        self.assertEqual(len(restored_model.hazards), 1)
        self.assertEqual(restored_model.losses[0].description, "Loss of life")
        self.assertEqual(restored_model.hazards[0].description, "Vehicle collision")
        
    def test_save_and_load_json(self):
        """Test saving and loading JSON files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Save model
            STPAModelIO.save_json(self.model, temp_path)
            
            # Verify file exists and has content
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            self.assertIsInstance(saved_data, dict)
            self.assertIn('name', saved_data)
            
            # Load model
            loaded_model = STPAModelIO.load_json(temp_path)
            
            # Verify loaded model
            self.assertEqual(loaded_model.name, self.model.name)
            self.assertEqual(loaded_model.description, self.model.description)
            self.assertEqual(len(loaded_model.control_structure.nodes), 2)
            self.assertEqual(len(loaded_model.control_structure.edges), 1)
            self.assertEqual(len(loaded_model.losses), 1)
            self.assertEqual(len(loaded_model.hazards), 1)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_save_json_error_handling(self):
        """Test error handling in save_json"""
        # Test invalid file path
        with self.assertRaises(IOError):
            STPAModelIO.save_json(self.model, "/invalid/path/that/does/not/exist.json")
            
    def test_load_json_error_handling(self):
        """Test error handling in load_json"""
        # Test non-existent file
        with self.assertRaises(FileNotFoundError):
            STPAModelIO.load_json("nonexistent_file.json")
            
        # Test invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write("invalid json content {")
            temp_path = temp_file.name
            
        try:
            with self.assertRaises(ValueError):
                STPAModelIO.load_json(temp_path)
        finally:
            os.unlink(temp_path)
            
        # Test invalid model format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            # Create truly invalid format that should fail
            json.dump({"control_structure": "invalid_structure_format"}, temp_file)
            temp_path = temp_file.name
            
        try:
            with self.assertRaises((ValueError, TypeError, AttributeError, RuntimeError)):
                STPAModelIO.load_json(temp_path)
        finally:
            os.unlink(temp_path)
            
    def test_complex_model_serialization(self):
        """Test serialization of complex model with UCA data"""
        # Create a more complex model
        complex_model = STPAModel()
        complex_model.name = "Complex Test Model"
        
        # Add multiple losses and hazards
        complex_model.add_loss("Loss 1", "High", "Critical loss")
        complex_model.add_loss("Loss 2", "Medium", "Moderate loss")
        
        complex_model.add_hazard("Hazard 1", "High", "Critical hazard", ["0"])
        complex_model.add_hazard("Hazard 2", "Medium", "Moderate hazard", ["0", "1"])
        
        # Add UCA data
        uca = UnsafeControlAction(
            id="uca1",
            control_action="Brake",
            context="Normal driving",
            category="Not Provided",
            hazard_links=["hazard1"],
            rationale="Could cause collision",
            severity=4,
            likelihood=3
        )
        complex_model.unsafe_control_actions.append(uca)
        
        context = UCAContext(
            id="ctx1",
            name="Normal Operation",
            description="Normal operating conditions",
            conditions=["Good weather", "Day time"]
        )
        complex_model.uca_contexts.append(context)
        
        # Test round-trip serialization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Save and load
            STPAModelIO.save_json(complex_model, temp_path)
            loaded_model = STPAModelIO.load_json(temp_path)
            
            # Verify all data is preserved
            self.assertEqual(loaded_model.name, "Complex Test Model")
            self.assertEqual(len(loaded_model.losses), 2)
            self.assertEqual(len(loaded_model.hazards), 2)
            self.assertEqual(len(loaded_model.unsafe_control_actions), 1)
            self.assertEqual(len(loaded_model.uca_contexts), 1)
            
            # Check UCA data
            loaded_uca = loaded_model.unsafe_control_actions[0]
            self.assertEqual(loaded_uca.id, "uca1")
            self.assertEqual(loaded_uca.control_action, "Brake")
            self.assertEqual(loaded_uca.severity, 4)
            self.assertEqual(loaded_uca.likelihood, 3)
            
            # Check context data
            loaded_context = loaded_model.uca_contexts[0]
            self.assertEqual(loaded_context.id, "ctx1")
            self.assertEqual(loaded_context.name, "Normal Operation")
            self.assertEqual(loaded_context.conditions, ["Good weather", "Day time"])
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_position_persistence(self):
        """Test that node positions are correctly saved and loaded (bug fix verification)"""
        # Create a model with nodes at specific positions
        model = STPAModel()
        
        test_positions = [
            ("node1", "TestNode1", (100.0, 200.0)),
            ("node2", "TestNode2", (300.0, 150.0)), 
            ("node3", "TestNode3", (250.0, 400.0))
        ]
        
        # Add nodes with specific positions
        for node_id, name, position in test_positions:
            model.control_structure.add_node(
                node_id=node_id,
                name=name,
                position=position
            )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Save the model
            STPAModelIO.save_json(model, temp_path)
            
            # Load the model back
            loaded_model = STPAModelIO.load_json(temp_path)
            
            # Verify positions are preserved
            for node_id, name, expected_pos in test_positions:
                self.assertIn(node_id, loaded_model.control_structure.nodes)
                
                node_data = loaded_model.control_structure.nodes[node_id]
                actual_pos = node_data.get('position', (0, 0))
                
                self.assertEqual(actual_pos, expected_pos, 
                    f"Position mismatch for node {node_id}: expected {expected_pos}, got {actual_pos}")
                
            # Also verify the raw JSON contains position data
            with open(temp_path, 'r') as f:
                json_data = json.load(f)
                
            nodes = json_data['control_structure']['nodes']
            self.assertEqual(len(nodes), 3)
            
            for node in nodes:
                self.assertIn('position', node, f"Node {node['id']} missing position field")
                self.assertIsInstance(node['position'], list, f"Position should be a list for node {node['id']}")
                self.assertEqual(len(node['position']), 2, f"Position should have 2 coordinates for node {node['id']}")
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_backwards_compatibility_pos_field(self):
        """Test that models with old 'pos' field names can still be loaded"""
        # Create a JSON structure with old 'pos' field format
        old_format_data = {
            "version": "0.4.6",
            "name": "Legacy Model",
            "description": "Model with old pos field format",
            "control_structure": {
                "nodes": [
                    {
                        "id": "legacy_node",
                        "name": "Legacy Node",
                        "pos": [50.0, 75.0],  # Old field name
                        "shape": "circle",
                        "size": 24.0,
                        "description": "",
                        "states": []
                    }
                ],
                "edges": []
            },
            "losses": [],
            "hazards": [],
            "unsafe_control_actions": [],
            "uca_contexts": [],
            "loss_scenarios": [],
            "metadata": {},
            "chat_transcripts": {
                "control_structure": "",
                "description": "",
                "losses_hazards": "",
                "uca": "",
                "scenarios": ""
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(old_format_data, temp_file)
            temp_path = temp_file.name
            
        try:
            # This should still work with old format
            loaded_model = STPAModelIO.load_json(temp_path)
            
            # Verify the model loads correctly
            self.assertEqual(loaded_model.name, "Legacy Model")
            self.assertEqual(len(loaded_model.control_structure.nodes), 1)
            self.assertIn("legacy_node", loaded_model.control_structure.nodes)
            
            # Verify position was loaded (from old 'pos' field to new 'position' field)
            node_data = loaded_model.control_structure.nodes["legacy_node"]
            actual_pos = node_data.get('position', (0, 0))
            
            # Note: The current implementation loads 'pos' field data during JSON loading
            # and the position should be preserved as (50.0, 75.0)
            self.assertNotEqual(actual_pos, (0, 0), "Position should not default to origin for legacy model")
            
        except Exception as e:
            # If backwards compatibility isn't implemented yet, this test documents the expected behavior
            self.fail(f"Loading legacy model with 'pos' field failed: {e}")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    def test_helper_methods(self):
        """Test helper serialization methods"""
        # Test loss serialization
        loss = Loss("Test loss", "High", "Test rationale")
        loss_dict = STPAModelIO._loss_to_dict(loss)
        expected = {
            'description': 'Test loss',
            'severity': 'High', 
            'rationale': 'Test rationale'
        }
        self.assertEqual(loss_dict, expected)
        
        # Test hazard serialization
        hazard = Hazard("Test hazard", "Medium", "Test rationale", ["loss1"])
        hazard_dict = STPAModelIO._hazard_to_dict(hazard)
        expected = {
            'description': 'Test hazard',
            'severity': 'Medium',
            'rationale': 'Test rationale', 
            'related_losses': ['loss1'],
            'condition': None
        }
        self.assertEqual(hazard_dict, expected)


if __name__ == '__main__':
    unittest.main()
