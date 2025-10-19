"""
Input validation utilities.
"""

from typing import Optional, List
import re
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """Utility class for input validation"""
    
    @staticmethod
    def validate_required_text(text: str, field_name: str) -> str:
        """Validate that required text field is not empty"""
        cleaned = text.strip()
        if not cleaned:
            logger.warning(f"Validation failed: {field_name} is empty")
            raise ValidationError(f"{field_name} is required and cannot be empty")
        logger.debug(f"Validated required text for {field_name}")
        return cleaned
    
    @staticmethod
    def validate_node_name(name: str) -> str:
        """Validate node name follows naming conventions"""
        cleaned = InputValidator.validate_required_text(name, "Node name")
        
        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', cleaned):
            logger.warning(f"Invalid node name format: {name}")
            raise ValidationError("Node name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        if len(cleaned) > 50:
            logger.warning(f"Node name too long: {len(cleaned)} characters")
            raise ValidationError("Node name cannot exceed 50 characters")
        
        logger.debug(f"Validated node name: {cleaned}")
        return cleaned
    
    @staticmethod
    def validate_severity(severity: str) -> str:
        """Validate severity level"""
        cleaned = severity.strip()
        valid_severities = ["Low", "Medium", "High", "Critical", ""]
        
        if cleaned and cleaned not in valid_severities:
            raise ValidationError(f"Severity must be one of: {', '.join(valid_severities[:-1])}")
            
        return cleaned
    
    @staticmethod
    def validate_risk_score(score: int, field_name: str) -> int:
        """Validate risk score is within valid range"""
        if not isinstance(score, int) or score < 1 or score > 5:
            raise ValidationError(f"{field_name} must be an integer between 1 and 5")
        return score
    
    @staticmethod
    def validate_description(description: str, max_length: int = 1000) -> str:
        """Validate description text"""
        cleaned = description.strip()
        if len(cleaned) > max_length:
            raise ValidationError(f"Description cannot exceed {max_length} characters")
        return cleaned
    
    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """Validate file path"""
        cleaned = file_path.strip()
        if not cleaned:
            raise ValidationError("File path cannot be empty")
        
        # Check for valid file extension
        if not cleaned.lower().endswith(('.json',)):
            raise ValidationError("File must have a .json extension")
            
        return cleaned
