"""
Unit tests for core.models module
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    STPAModel, SystemNode, ControlLink, Loss, Hazard, State,
    HazardCondition, UCAContext, UnsafeControlAction, ControlStructure
)


class TestState(unittest.TestCase):
    """Test cases for the State class"""
    
    def test_state_creation(self):
        """Test State creation with default values"""
        state = State(name="TestState")
        self.assertEqual(state.name, "TestState")
        self.assertEqual(state.description, "")
        self.assertFalse(state.is_initial)
        
    def test_state_creation_with_values(self):
        """Test State creation with custom values"""
        state = State(
            name="InitialState",
            description="The initial state",
            is_initial=True
        )
        self.assertEqual(state.name, "InitialState")
        self.assertEqual(state.description, "The initial state")
        self.assertTrue(state.is_initial)


class TestSystemNode(unittest.TestCase):
    """Test cases for the SystemNode class"""
    
    def test_node_creation(self):
        """Test SystemNode creation with default values"""
        node = SystemNode(id="node1", name="Test Node")
        self.assertEqual(node.id, "node1")
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.position, (0.0, 0.0))
        self.assertEqual(node.shape, "circle")
        self.assertEqual(node.size, 24.0)
        self.assertEqual(node.description, "")
        self.assertEqual(len(node.states), 0)
        
    def test_node_add_state(self):
        """Test adding states to a node"""
        node = SystemNode(id="node1", name="Test Node")
        
        # Add initial state
        node.add_state("State1", "First state", is_initial=True)
        self.assertEqual(len(node.states), 1)
        self.assertEqual(node.states[0].name, "State1")
        self.assertTrue(node.states[0].is_initial)
        
        # Add another state
        node.add_state("State2", "Second state")
        self.assertEqual(len(node.states), 2)
        self.assertEqual(node.states[1].name, "State2")
        self.assertFalse(node.states[1].is_initial)
        
        # Add another initial state (should clear previous initial)
        node.add_state("State3", "Third state", is_initial=True)
        self.assertEqual(len(node.states), 3)
        self.assertFalse(node.states[0].is_initial)  # First state no longer initial
        self.assertFalse(node.states[1].is_initial)
        self.assertTrue(node.states[2].is_initial)   # New state is initial
        
    def test_node_get_initial_state(self):
        """Test getting initial state from a node"""
        node = SystemNode(id="node1", name="Test Node")
        
        # No initial state
        initial = node.get_initial_state()
        self.assertIsNone(initial)
        
        # Add states with one initial
        node.add_state("State1", "First state")
        node.add_state("State2", "Second state", is_initial=True)
        
        initial = node.get_initial_state()
        self.assertIsNotNone(initial)
        self.assertEqual(initial.name, "State2")


class TestControlLink(unittest.TestCase):
    """Test cases for the ControlLink class"""
    
    def test_link_creation(self):
        """Test ControlLink creation with default values"""
        link = ControlLink(id="link1", source_id="node1", target_id="node2")
        self.assertEqual(link.id, "link1")
        self.assertEqual(link.source_id, "node1")
        self.assertEqual(link.target_id, "node2")
        self.assertEqual(link.name, "")
        self.assertEqual(link.description, "")
        self.assertEqual(link.weight, 1.0)
        self.assertFalse(link.undirected)
        self.assertFalse(link.bidirectional)
        
    def test_link_creation_with_values(self):
        """Test ControlLink creation with custom values"""
        link = ControlLink(
            id="link1",
            source_id="node1", 
            target_id="node2",
            name="Control Signal",
            description="Main control signal",
            weight=2.5,
            undirected=True,
            bidirectional=True
        )
        self.assertEqual(link.name, "Control Signal")
        self.assertEqual(link.description, "Main control signal")
        self.assertEqual(link.weight, 2.5)
        self.assertTrue(link.undirected)
        self.assertTrue(link.bidirectional)


class TestLoss(unittest.TestCase):
    """Test cases for the Loss class"""
    
    def test_loss_creation(self):
        """Test Loss creation"""
        loss = Loss(
            description="Loss of life",
            severity="High",
            rationale="Human safety is paramount"
        )
        self.assertEqual(loss.description, "Loss of life")
        self.assertEqual(loss.severity, "High")
        self.assertEqual(loss.rationale, "Human safety is paramount")


class TestHazard(unittest.TestCase):
    """Test cases for the Hazard class"""
    
    def test_hazard_creation(self):
        """Test Hazard creation"""
        hazard = Hazard(
            description="Vehicle collision",
            severity="High",
            rationale="Could lead to loss of life",
            related_losses=["loss1", "loss2"]
        )
        self.assertEqual(hazard.description, "Vehicle collision")
        self.assertEqual(hazard.severity, "High")
        self.assertEqual(hazard.rationale, "Could lead to loss of life")
        self.assertEqual(hazard.related_losses, ["loss1", "loss2"])
        self.assertIsNone(hazard.condition)
        
    def test_hazard_with_condition(self):
        """Test Hazard creation with condition"""
        condition = HazardCondition(description="Node A in State X AND Node B in State Y")
        hazard = Hazard(
            description="System failure",
            condition=condition
        )
        self.assertIsNotNone(hazard.condition)
        self.assertEqual(hazard.condition.description, "Node A in State X AND Node B in State Y")


class TestUnsafeControlAction(unittest.TestCase):
    """Test cases for the UnsafeControlAction class"""
    
    def test_uca_creation(self):
        """Test UCA creation"""
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
        self.assertEqual(uca.id, "uca1")
        self.assertEqual(uca.control_action, "Brake")
        self.assertEqual(uca.context, "Normal driving")
        self.assertEqual(uca.category, "Not Provided")
        self.assertEqual(uca.hazard_links, ["hazard1"])
        self.assertEqual(uca.rationale, "Could cause collision")
        self.assertEqual(uca.severity, 4)
        self.assertEqual(uca.likelihood, 3)
        
    def test_uca_risk_score(self):
        """Test UCA risk score calculation"""
        uca = UnsafeControlAction(
            id="uca1",
            control_action="Brake",
            context="Normal driving",
            category="Not Provided",
            severity=4,
            likelihood=3
        )
        self.assertEqual(uca.risk_score, 12)  # 4 * 3 = 12


class TestControlStructure(unittest.TestCase):
    """Test cases for the ControlStructure class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cs = ControlStructure()
        
    def test_control_structure_creation(self):
        """Test ControlStructure creation"""
        self.assertIsInstance(self.cs, ControlStructure)
        self.assertEqual(len(self.cs.nodes), 0)
        self.assertEqual(len(self.cs.edges), 0)
        
    def test_add_node_with_data(self):
        """Test adding node with data"""
        node = self.cs.add_node_with_data(
            node_id="node1",
            name="Controller",
            position=(100.0, 50.0),
            shape="rectangle"
        )
        
        self.assertIsInstance(node, SystemNode)
        self.assertEqual(node.id, "node1")
        self.assertEqual(node.name, "Controller")
        self.assertEqual(node.position, (100.0, 50.0))
        self.assertEqual(node.shape, "rectangle")
        
        # Check it was added to the graph
        self.assertIn("node1", self.cs.nodes)
        
    def test_add_link(self):
        """Test adding link"""
        # First add nodes
        self.cs.add_node_with_data("node1", "Controller")
        self.cs.add_node_with_data("node2", "Actuator")
        
        # Add link
        link = self.cs.add_link(
            link_id="link1",
            source_id="node1",
            target_id="node2",
            name="Control Signal",
            weight=2.0
        )
        
        self.assertIsInstance(link, ControlLink)
        self.assertEqual(link.id, "link1")
        self.assertEqual(link.source_id, "node1")
        self.assertEqual(link.target_id, "node2")
        self.assertEqual(link.name, "Control Signal")
        self.assertEqual(link.weight, 2.0)
        
        # Check it was added to the graph
        self.assertTrue(self.cs.has_edge("node1", "node2"))
        
    def test_get_node_data(self):
        """Test getting node data"""
        # Add a node
        original_node = self.cs.add_node_with_data(
            node_id="node1",
            name="Controller",
            description="Main controller"
        )
        
        # Get node data
        retrieved_node = self.cs.get_node_data("node1")
        self.assertIsNotNone(retrieved_node)
        self.assertEqual(retrieved_node.id, "node1")
        self.assertEqual(retrieved_node.name, "Controller")
        self.assertEqual(retrieved_node.description, "Main controller")
        
        # Test non-existent node
        missing_node = self.cs.get_node_data("nonexistent")
        self.assertIsNone(missing_node)
        
    def test_remove_node_with_links(self):
        """Test removing node with its links"""
        # Add nodes and links
        self.cs.add_node_with_data("node1", "Controller")
        self.cs.add_node_with_data("node2", "Actuator")
        self.cs.add_node_with_data("node3", "Sensor")
        
        self.cs.add_link("link1", "node1", "node2")
        self.cs.add_link("link2", "node2", "node3")
        self.cs.add_link("link3", "node3", "node1")
        
        # Verify setup
        self.assertEqual(len(self.cs.nodes), 3)
        self.assertEqual(len(self.cs.edges), 3)
        
        # Remove node1 (should remove links involving node1)
        self.cs.remove_node_with_links("node1")
        
        self.assertEqual(len(self.cs.nodes), 2)
        self.assertNotIn("node1", self.cs.nodes)
        self.assertEqual(len(self.cs.edges), 1)  # Only link2 should remain

    def test_id_conflict_prevention(self):
        """Test that adding nodes doesn't cause 'multiple values for keyword argument id' error"""
        # This test verifies the fix for the bug where sync_to_model would fail
        # when node data included 'id' field
        
        # Add nodes normally
        self.cs.add_node_with_data("node1", "Test Node 1", position=(100, 200))
        self.cs.add_node_with_data("node2", "Test Node 2", position=(300, 400))
        
        # Verify nodes were added
        self.assertEqual(len(self.cs.nodes), 2)
        self.assertIn("node1", self.cs.nodes)
        self.assertIn("node2", self.cs.nodes)
        
        # Simulate what happens in UI sync_to_model - this used to cause the error
        temp_nodes = list(self.cs.nodes(data=True))
        self.cs.clear()
        
        # This should not raise "multiple values for keyword argument 'id'"
        for node_id, data in temp_nodes:
            # The fix: exclude 'id' from data to avoid conflict
            node_data = {k: v for k, v in data.items() if k != 'id'}
            self.cs.add_node(node_id, **node_data)
        
        # Verify reconstruction worked
        self.assertEqual(len(self.cs.nodes), 2)
        self.assertIn("node1", self.cs.nodes)
        self.assertIn("node2", self.cs.nodes)
        
        # Verify data integrity
        node1_data = self.cs.nodes["node1"]
        self.assertEqual(node1_data.get('name'), "Test Node 1")
        self.assertEqual(node1_data.get('position'), (100, 200))
        
    def test_get_node_data_after_id_fix(self):
        """Test that get_node_data works correctly after the id field fix"""
        # Add a node
        original_node = self.cs.add_node_with_data(
            "test_node", "Test Node", position=(50, 75), shape="rectangle"
        )
        
        # Get node data back (this used to fail after removing id from stored attrs)
        retrieved_node = self.cs.get_node_data("test_node")
        
        # Verify the retrieved node is correct
        self.assertIsNotNone(retrieved_node)
        self.assertEqual(retrieved_node.id, "test_node")
        self.assertEqual(retrieved_node.name, "Test Node")
        self.assertEqual(retrieved_node.position, (50, 75))
        self.assertEqual(retrieved_node.shape, "rectangle")


class TestSTPAModel(unittest.TestCase):
    """Test cases for the STPAModel class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = STPAModel()
        
    def test_model_creation(self):
        """Test STPAModel creation with default values"""
        self.assertEqual(self.model.name, "Untitled STPA Model")
        self.assertEqual(self.model.version, "0.4.6")
        self.assertEqual(self.model.description, "")
        self.assertIsInstance(self.model.control_structure, ControlStructure)
        self.assertEqual(len(self.model.losses), 0)
        self.assertEqual(len(self.model.hazards), 0)
        self.assertEqual(len(self.model.uca_contexts), 0)
        self.assertEqual(len(self.model.unsafe_control_actions), 0)
        self.assertIsInstance(self.model.metadata, dict)
        self.assertIsInstance(self.model.chat_transcripts, dict)
        
    def test_add_loss(self):
        """Test adding loss to model"""
        loss = self.model.add_loss(
            description="Loss of life",
            severity="High",
            rationale="Human safety"
        )
        
        self.assertIsInstance(loss, Loss)
        self.assertEqual(len(self.model.losses), 1)
        self.assertEqual(self.model.losses[0].description, "Loss of life")
        self.assertEqual(self.model.losses[0].severity, "High")
        self.assertEqual(self.model.losses[0].rationale, "Human safety")
        
    def test_add_hazard(self):
        """Test adding hazard to model"""
        hazard = self.model.add_hazard(
            description="Vehicle collision",
            severity="High",
            rationale="Could cause injury",
            related_losses=["loss1", "loss2"]
        )
        
        self.assertIsInstance(hazard, Hazard)
        self.assertEqual(len(self.model.hazards), 1)
        self.assertEqual(self.model.hazards[0].description, "Vehicle collision")
        self.assertEqual(self.model.hazards[0].related_losses, ["loss1", "loss2"])
        
    def test_get_next_node_id(self):
        """Test node ID generation"""
        # Empty model should start with n1
        next_id = self.model.get_next_node_id()
        self.assertEqual(next_id, "n1")
        
        # Add some nodes
        self.model.control_structure.add_node("n1", name="Node 1")
        self.model.control_structure.add_node("n3", name="Node 3")
        self.model.control_structure.add_node("n5", name="Node 5")
        
        # Should return n6 (next after highest)
        next_id = self.model.get_next_node_id()
        self.assertEqual(next_id, "n6")
        
    def test_get_next_link_id(self):
        """Test link ID generation"""
        # Add some edges first
        self.model.control_structure.add_node("n1", name="Node 1")
        self.model.control_structure.add_node("n2", name="Node 2")
        self.model.control_structure.add_edge("n1", "n2", key="e1")
        self.model.control_structure.add_edge("n1", "n2", key="e3")
        self.model.control_structure.add_edge("n1", "n2", key=5)  # Integer key
        
        # Should return e6 (next after highest)
        next_id = self.model.get_next_link_id()
        self.assertEqual(next_id, "e6")
    
    def test_get_next_link_id_empty_model(self):
        """Test link ID generation on empty model"""
        # Empty model should start with e1
        next_id = self.model.get_next_link_id()
        self.assertEqual(next_id, "e1")


class TestIDGenerator(unittest.TestCase):
    """Test cases for the IDGenerator optimization"""
    
    def setUp(self):
        """Set up test fixtures"""
        from core.models import IDGenerator
        self.id_gen = IDGenerator()
    
    def test_id_generator_initialization(self):
        """Test IDGenerator initialization"""
        self.assertTrue(self.id_gen.enable_cache)
        self.assertEqual(self.id_gen._node_counter, 1)
        self.assertEqual(self.id_gen._link_counter, 1)
        self.assertIsNone(self.id_gen._cached_node_ids)
        self.assertIsNone(self.id_gen._cached_link_ids)
        self.assertTrue(self.id_gen._dirty_node_cache)
        self.assertTrue(self.id_gen._dirty_link_cache)
    
    def test_invalidate_cache(self):
        """Test cache invalidation"""
        self.id_gen._dirty_node_cache = False
        self.id_gen._dirty_link_cache = False
        
        self.id_gen.invalidate_cache()
        
        self.assertTrue(self.id_gen._dirty_node_cache)
        self.assertTrue(self.id_gen._dirty_link_cache)
    
    def test_cache_disabled(self):
        """Test IDGenerator with cache disabled"""
        from core.models import IDGenerator
        id_gen = IDGenerator(enable_cache=False)
        
        self.assertFalse(id_gen.enable_cache)
        self.assertEqual(id_gen._node_counter, 1)
        self.assertEqual(id_gen._link_counter, 1)
    
    def test_id_generator_integration_with_model(self):
        """Test IDGenerator integration with STPAModel"""
        model = STPAModel(name="TestModel")
        
        # Add some nodes and edges manually
        model.control_structure.add_node("n1", "Node 1")
        model.control_structure.add_node("n3", "Node 3")
        model.control_structure.add_edge("n1", "n3", key="e1", **{"label": "Edge 1"})
        model.control_structure.add_edge("n1", "n3", key="e5", **{"label": "Edge 5"})
        
        # Get next IDs - should use optimized generation if available
        next_node_id = model.get_next_node_id()
        next_link_id = model.get_next_link_id()
        
        # Should generate appropriate next IDs
        self.assertTrue(next_node_id.startswith("n"))
        self.assertTrue(next_link_id.startswith("e"))
        
        # Should not conflict with existing IDs
        self.assertNotIn(next_node_id, ["n1", "n3"])
        self.assertNotIn(next_link_id, ["e1", "e5"])
    
    def test_node_id_generation_optimization(self):
        """Test that node ID generation handles existing IDs properly"""
        model = STPAModel(name="TestModel")
        
        # Add nodes with non-sequential IDs
        model.control_structure.add_node("n1", "Node 1")
        model.control_structure.add_node("n5", "Node 5")
        model.control_structure.add_node("n10", "Node 10")
        
        # Next ID should be higher than highest existing
        next_id = model.get_next_node_id()
        
        # Should be n11 or higher
        self.assertTrue(next_id.startswith("n"))
        id_num = int(next_id[1:])
        self.assertGreaterEqual(id_num, 11)
    
    def test_edge_id_generation_optimization(self):
        """Test that edge ID generation handles existing IDs properly"""
        model = STPAModel(name="TestModel")
        
        # Add nodes first
        model.control_structure.add_node("n1", "Node 1")
        model.control_structure.add_node("n2", "Node 2")
        
        # Add edges with non-sequential IDs
        model.control_structure.add_edge("n1", "n2", key="e1", **{"label": "Edge 1"})
        model.control_structure.add_edge("n1", "n2", key="e3", **{"label": "Edge 3"})
        model.control_structure.add_edge("n1", "n2", key="e7", **{"label": "Edge 7"})
        
        # Next ID should be higher than highest existing
        next_id = model.get_next_link_id()
        
        # Should be e8 or higher
        self.assertTrue(next_id.startswith("e"))
        id_num = int(next_id[1:])
        self.assertGreaterEqual(id_num, 8)


if __name__ == '__main__':
    unittest.main()
