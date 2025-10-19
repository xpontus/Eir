"""
Performance tests for the Eir STPA Tool
"""

import unittest
import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import STPAModel
from core.file_io import STPAModelIO
import tempfile


class TestPerformance(unittest.TestCase):
    """Performance tests for critical operations"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.model = STPAModel()
        
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        return result, elapsed
        
    def test_large_model_creation_performance(self):
        """Test performance of creating large models"""
        print("\n--- Large Model Creation Performance ---")
        
        # Test creating model with many nodes
        start_time = time.time()
        
        # Add 1000 nodes
        for i in range(1000):
            self.model.control_structure.add_node(
                f"node_{i}",
                name=f"Node {i}",
                position=(i * 10.0, i * 5.0)
            )
        
        nodes_time = time.time() - start_time
        print(f"Adding 1000 nodes: {nodes_time:.3f} seconds")
        
        # Add edges between sequential nodes
        start_time = time.time()
        for i in range(999):
            self.model.control_structure.add_edge(
                f"node_{i}", f"node_{i+1}",
                key=f"edge_{i}",
                name=f"Edge {i}"
            )
        
        edges_time = time.time() - start_time
        print(f"Adding 999 edges: {edges_time:.3f} seconds")
        
        # Performance assertions (reasonable thresholds)
        self.assertLess(nodes_time, 1.0, "Node creation should be fast")
        self.assertLess(edges_time, 1.0, "Edge creation should be fast")
        
    def test_large_model_serialization_performance(self):
        """Test performance of serializing large models"""
        print("\n--- Large Model Serialization Performance ---")
        
        # Create a reasonably large model
        for i in range(100):
            self.model.control_structure.add_node(f"node_{i}", name=f"Node {i}")
            self.model.add_loss(f"Loss {i}", "High", f"Loss rationale {i}")
            self.model.add_hazard(f"Hazard {i}", "Medium", f"Hazard rationale {i}")
            
        for i in range(99):
            self.model.control_structure.add_edge(
                f"node_{i}", f"node_{i+1}", key=f"edge_{i}"
            )
        
        # Test serialization performance
        _, serialization_time = self.measure_time(
            STPAModelIO._model_to_dict, self.model
        )
        print(f"Serialization (100 nodes, 99 edges, 200 STPA items): {serialization_time:.3f} seconds")
        
        # Test file save performance
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            _, save_time = self.measure_time(
                STPAModelIO.save_json, self.model, temp_path
            )
            print(f"File save: {save_time:.3f} seconds")
            
            # Test file load performance
            loaded_model, load_time = self.measure_time(
                STPAModelIO.load_json, temp_path
            )
            print(f"File load: {load_time:.3f} seconds")
            
            # Verify loaded model is correct
            self.assertEqual(len(loaded_model.control_structure.nodes), 100)
            self.assertEqual(len(loaded_model.losses), 100)
            self.assertEqual(len(loaded_model.hazards), 100)
            
        finally:
            os.unlink(temp_path)
        
        # Performance assertions
        self.assertLess(serialization_time, 0.5, "Serialization should be fast")
        self.assertLess(save_time, 1.0, "File save should be fast")
        self.assertLess(load_time, 1.0, "File load should be fast")
        
    def test_model_operations_performance(self):
        """Test performance of common model operations"""
        print("\n--- Model Operations Performance ---")
        
        # Test node lookup performance
        for i in range(100):
            self.model.control_structure.add_node(f"node_{i}", name=f"Node {i}")
            
        _, lookup_time = self.measure_time(
            lambda: [self.model.control_structure.nodes[f"node_{i}"] for i in range(100)]
        )
        print(f"100 node lookups: {lookup_time:.3f} seconds")
        
        # Test ID generation performance
        _, id_gen_time = self.measure_time(
            lambda: [self.model.get_next_node_id() for _ in range(100)]
        )
        print(f"100 node ID generations: {id_gen_time:.3f} seconds")
        
        # Add some edges for link ID testing
        for i in range(50):
            self.model.control_structure.add_edge(
                f"node_{i}", f"node_{i+1}", key=f"e{i}"
            )
            
        _, link_id_gen_time = self.measure_time(
            lambda: [self.model.get_next_link_id() for _ in range(100)]
        )
        print(f"100 link ID generations: {link_id_gen_time:.3f} seconds")
        
        # Performance assertions
        self.assertLess(lookup_time, 0.1, "Node lookups should be very fast")
        self.assertLess(id_gen_time, 0.1, "ID generation should be very fast")
        self.assertLess(link_id_gen_time, 0.1, "Link ID generation should be very fast")
        
    def test_validation_performance(self):
        """Test performance of input validation"""
        print("\n--- Validation Performance ---")
        
        from core.validation import InputValidator
        
        # Test node name validation performance
        valid_names = [f"Node_{i}" for i in range(1000)]
        _, validation_time = self.measure_time(
            lambda: [InputValidator.validate_node_name(name) for name in valid_names]
        )
        print(f"1000 node name validations: {validation_time:.3f} seconds")
        
        # Test severity validation performance
        severities = ["High", "Medium", "Low", "Critical", ""] * 200
        _, severity_validation_time = self.measure_time(
            lambda: [InputValidator.validate_severity(sev) for sev in severities]
        )
        print(f"1000 severity validations: {severity_validation_time:.3f} seconds")
        
        # Performance assertions
        self.assertLess(validation_time, 0.5, "Validation should be fast")
        self.assertLess(severity_validation_time, 0.1, "Severity validation should be very fast")


class TestScalability(unittest.TestCase):
    """Scalability tests for various model sizes"""
    
    def test_model_scaling(self):
        """Test how performance scales with model size"""
        print("\n--- Model Scaling Test ---")
        
        sizes = [10, 50, 100, 500]
        times = []
        
        for size in sizes:
            model = STPAModel()
            
            # Measure time to create model of given size
            start_time = time.time()
            
            # Add nodes
            for i in range(size):
                model.control_structure.add_node(f"node_{i}", name=f"Node {i}")
                
            # Add edges (create a chain)
            for i in range(size - 1):
                model.control_structure.add_edge(
                    f"node_{i}", f"node_{i+1}", key=f"edge_{i}"
                )
                
            # Add losses and hazards
            for i in range(size // 10):  # 10% ratio
                model.add_loss(f"Loss {i}", "High", f"Rationale {i}")
                model.add_hazard(f"Hazard {i}", "Medium", f"Rationale {i}")
                
            creation_time = time.time() - start_time
            times.append(creation_time)
            
            print(f"Model with {size} nodes: {creation_time:.3f} seconds")
            
            # Test serialization time
            start_time = time.time()
            data = STPAModelIO._model_to_dict(model)
            serialization_time = time.time() - start_time
            
            print(f"  Serialization: {serialization_time:.3f} seconds")
            
            # Verify model integrity
            self.assertEqual(len(model.control_structure.nodes), size)
            self.assertEqual(len(model.control_structure.edges), size - 1)
            
        # Check that scaling is reasonable (should be roughly linear)
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            size_ratio = sizes[i] / sizes[i-1]
            print(f"Size ratio {sizes[i-1]} -> {sizes[i]}: {size_ratio:.1f}x, Time ratio: {ratio:.1f}x")
            
            # Time should scale no worse than quadratic
            self.assertLess(ratio, size_ratio * 2, "Scaling should be reasonable")


if __name__ == '__main__':
    # Run performance tests with detailed output
    unittest.main(verbosity=2)
