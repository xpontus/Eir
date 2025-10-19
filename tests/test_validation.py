"""
Unit tests for core.validation module
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.validation import InputValidator, ValidationError


class TestInputValidator(unittest.TestCase):
    """Test cases for the InputValidator class"""
    
    def test_validate_required_text_valid(self):
        """Test validate_required_text with valid input"""
        # Test normal text
        result = InputValidator.validate_required_text("Valid text", "Test Field")
        self.assertEqual(result, "Valid text")
        
        # Test text with leading/trailing whitespace
        result = InputValidator.validate_required_text("  Valid text  ", "Test Field")
        self.assertEqual(result, "Valid text")
        
    def test_validate_required_text_invalid(self):
        """Test validate_required_text with invalid input"""
        # Test empty string
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_required_text("", "Test Field")
        self.assertIn("Test Field is required", str(context.exception))
        
        # Test whitespace only
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_required_text("   ", "Test Field")
        self.assertIn("Test Field is required", str(context.exception))
        
    def test_validate_node_name_valid(self):
        """Test validate_node_name with valid input"""
        valid_names = [
            "Node1",
            "My Node",
            "controller-1",
            "sensor_data",
            "Node 123",
            "A"
        ]
        
        for name in valid_names:
            with self.subTest(name=name):
                result = InputValidator.validate_node_name(name)
                self.assertEqual(result, name)
                
    def test_validate_node_name_invalid(self):
        """Test validate_node_name with invalid input"""
        # Test empty name
        with self.assertRaises(ValidationError):
            InputValidator.validate_node_name("")
            
        # Test invalid characters
        invalid_names = [
            "Node@1",
            "Node$",
            "Node!",
            "Node#1",
            "Node%",
            "Node&"
        ]
        
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError) as context:
                    InputValidator.validate_node_name(name)
                self.assertIn("can only contain", str(context.exception))
                
        # Test too long name
        long_name = "a" * 51
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_node_name(long_name)
        self.assertIn("cannot exceed 50 characters", str(context.exception))
        
    def test_validate_severity_valid(self):
        """Test validate_severity with valid input"""
        valid_severities = ["Low", "Medium", "High", "Critical", ""]
        
        for severity in valid_severities:
            with self.subTest(severity=severity):
                result = InputValidator.validate_severity(severity)
                self.assertEqual(result, severity)
                
        # Test with whitespace
        result = InputValidator.validate_severity("  High  ")
        self.assertEqual(result, "High")
        
    def test_validate_severity_invalid(self):
        """Test validate_severity with invalid input"""
        invalid_severities = ["VeryHigh", "low", "MEDIUM", "Invalid"]
        
        for severity in invalid_severities:
            with self.subTest(severity=severity):
                with self.assertRaises(ValidationError) as context:
                    InputValidator.validate_severity(severity)
                self.assertIn("must be one of", str(context.exception))
                
    def test_validate_risk_score_valid(self):
        """Test validate_risk_score with valid input"""
        valid_scores = [1, 2, 3, 4, 5]
        
        for score in valid_scores:
            with self.subTest(score=score):
                result = InputValidator.validate_risk_score(score, "Test Score")
                self.assertEqual(result, score)
                
    def test_validate_risk_score_invalid(self):
        """Test validate_risk_score with invalid input"""
        invalid_scores = [0, 6, -1, 10, "5", 3.5, None]
        
        for score in invalid_scores:
            with self.subTest(score=score):
                with self.assertRaises(ValidationError) as context:
                    InputValidator.validate_risk_score(score, "Test Score")
                self.assertIn("must be an integer between 1 and 5", str(context.exception))
                
    def test_validate_description_valid(self):
        """Test validate_description with valid input"""
        # Test normal description
        desc = "This is a valid description."
        result = InputValidator.validate_description(desc)
        self.assertEqual(result, desc)
        
        # Test with whitespace
        result = InputValidator.validate_description("  Valid description  ")
        self.assertEqual(result, "Valid description")
        
        # Test empty description (should be allowed)
        result = InputValidator.validate_description("")
        self.assertEqual(result, "")
        
    def test_validate_description_invalid(self):
        """Test validate_description with invalid input"""
        # Test too long description
        long_desc = "a" * 1001
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_description(long_desc)
        self.assertIn("cannot exceed 1000 characters", str(context.exception))
        
        # Test custom max length
        desc = "a" * 101
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_description(desc, max_length=100)
        self.assertIn("cannot exceed 100 characters", str(context.exception))
        
    def test_validate_file_path_valid(self):
        """Test validate_file_path with valid input"""
        valid_paths = [
            "model.json",
            "/path/to/model.json",
            "C:\\path\\to\\model.json",
            "my_model.json"
        ]
        
        for path in valid_paths:
            with self.subTest(path=path):
                result = InputValidator.validate_file_path(path)
                self.assertEqual(result, path)
                
    def test_validate_file_path_invalid(self):
        """Test validate_file_path with invalid input"""
        # Test empty path
        with self.assertRaises(ValidationError) as context:
            InputValidator.validate_file_path("")
        self.assertIn("cannot be empty", str(context.exception))
        
        # Test invalid extension
        invalid_paths = ["model.txt", "model.xml", "model", "model.graphml"]
        
        for path in invalid_paths:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError) as context:
                    InputValidator.validate_file_path(path)
                self.assertIn("must have a .json extension", str(context.exception))


class TestValidationError(unittest.TestCase):
    """Test cases for the ValidationError exception"""
    
    def test_validation_error_creation(self):
        """Test ValidationError can be created and raised"""
        error_msg = "Test validation error"
        error = ValidationError(error_msg)
        self.assertEqual(str(error), error_msg)
        
        # Test raising the error
        with self.assertRaises(ValidationError) as context:
            raise ValidationError(error_msg)
        self.assertEqual(str(context.exception), error_msg)


if __name__ == '__main__':
    unittest.main()
