"""
Test suite for document management functionality.
"""

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.models import Document, STPAModel
from core.document_manager import DocumentManager
from core.file_io import STPAModelIO


class TestDocument(unittest.TestCase):
    """Test the Document dataclass"""
    
    def test_document_creation(self):
        """Test creating a Document with all fields"""
        doc = Document(
            filename="test_doc_12345.pdf",
            original_name="test document.pdf",
            file_type="pdf",
            file_size=1024000,
            upload_date="2024-01-15T10:30:00",
            description="Test document description"
        )
        
        self.assertEqual(doc.filename, "test_doc_12345.pdf")
        self.assertEqual(doc.original_name, "test document.pdf")
        self.assertEqual(doc.file_type, "pdf")
        self.assertEqual(doc.file_size, 1024000)
        self.assertEqual(doc.upload_date, "2024-01-15T10:30:00")
        self.assertEqual(doc.description, "Test document description")
    
    def test_document_is_pdf(self):
        """Test PDF file type detection"""
        pdf_doc = Document("test.pdf", "test.pdf", "pdf", 1000, "2024-01-01", "")
        self.assertTrue(pdf_doc.is_pdf)
        self.assertFalse(pdf_doc.is_image)
        
        non_pdf_doc = Document("test.png", "test.png", "png", 1000, "2024-01-01", "")
        self.assertFalse(non_pdf_doc.is_pdf)
    
    def test_document_is_image(self):
        """Test image file type detection"""
        image_types = ["png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"]
        
        for img_type in image_types:
            doc = Document(f"test.{img_type}", f"test.{img_type}", img_type, 1000, "2024-01-01", "")
            self.assertTrue(doc.is_image, f"{img_type} should be detected as image")
            self.assertFalse(doc.is_pdf)
        
        # Test non-image type
        doc = Document("test.txt", "test.txt", "txt", 1000, "2024-01-01", "")
        self.assertFalse(doc.is_image)


class TestDocumentManager(unittest.TestCase):
    """Test the DocumentManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.document_manager = DocumentManager()
        
        # Create test files
        self.test_pdf_file = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_file, 'wb') as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n")  # Minimal PDF
        
        self.test_image_file = os.path.join(self.temp_dir, "test.png")
        with open(self.test_image_file, 'wb') as f:
            # PNG header
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde')
        
        self.test_text_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_text_file, 'w') as f:
            f.write("This is a test text file")
        
        # Large file for testing size limits
        self.large_file = os.path.join(self.temp_dir, "large.pdf")
        with open(self.large_file, 'wb') as f:
            f.write(b'0' * (60 * 1024 * 1024))  # 60MB file
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_file_success(self):
        """Test successful file validation"""
        # Test PDF
        result = self.document_manager.validate_file(self.test_pdf_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, "pdf")
        
        # Test image
        result = self.document_manager.validate_file(self.test_image_file)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, "png")
    
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file"""
        result = self.document_manager.validate_file("/nonexistent/file.pdf")
        self.assertFalse(result.is_valid)
        self.assertIn("does not exist", result.error_message)
    
    def test_validate_file_unsupported_type(self):
        """Test validation of unsupported file type"""
        result = self.document_manager.validate_file(self.test_text_file)
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported file type", result.error_message)
    
    def test_validate_file_too_large(self):
        """Test validation of file too large"""
        result = self.document_manager.validate_file(self.large_file)
        self.assertFalse(result.is_valid)
        self.assertIn("too large", result.error_message)
    
    def test_get_file_type(self):
        """Test file type detection"""
        # Test with extension only - method returns the extension itself for supported types
        self.assertEqual(self.document_manager._get_file_type("pdf"), "pdf")
        self.assertEqual(self.document_manager._get_file_type("png"), "png")
        self.assertEqual(self.document_manager._get_file_type("jpeg"), "jpeg")
        self.assertIsNone(self.document_manager._get_file_type("unknown"))  # Returns None for unsupported
    
    def test_generate_unique_filename(self):
        """Test unique filename generation via upload method"""
        # Upload the same file twice to test unique naming
        success1, message1, doc_info1 = self.document_manager.upload_document(self.test_pdf_file)
        success2, message2, doc_info2 = self.document_manager.upload_document(self.test_pdf_file)
        
        if success1 and success2:
            self.assertNotEqual(doc_info1.filename, doc_info2.filename)
            self.assertTrue(doc_info1.filename.endswith(".pdf"))
            self.assertTrue(doc_info2.filename.endswith(".pdf"))
    
    def test_upload_document_success(self):
        """Test successful document upload"""
        success, message, doc_info = self.document_manager.upload_document(self.test_pdf_file)
        
        self.assertTrue(success)
        self.assertIn("successfully", message.lower())
        self.assertIsNotNone(doc_info)
        self.assertEqual(doc_info.original_name, "test.pdf")
        self.assertEqual(doc_info.file_type, "pdf")
        
        # Verify file was actually copied
        dest_path = self.document_manager.get_document_path(doc_info)
        self.assertTrue(dest_path.exists())
    
    def test_upload_document_invalid_file(self):
        """Test upload of invalid file"""
        success, message, doc_info = self.document_manager.upload_document(self.test_text_file)
        
        self.assertFalse(success)
        self.assertIn("Unsupported file type", message)
        self.assertIsNone(doc_info)
    
    def test_remove_document_file_success(self):
        """Test successful document file removal"""
        # First upload a document
        success, message, doc_info = self.document_manager.upload_document(self.test_pdf_file)
        self.assertTrue(success)
        
        # Verify file exists
        dest_path = self.document_manager.get_document_path(doc_info)
        self.assertTrue(dest_path.exists())
        
        # Remove the document
        success, message = self.document_manager.remove_document_file(doc_info)
        self.assertTrue(success)
        self.assertIn("removed", message.lower())
        
        # Verify file is gone
        self.assertFalse(dest_path.exists())
    
    def test_remove_document_file_not_found(self):
        """Test removal of non-existent document file"""
        doc = Document("nonexistent_123.pdf", "test.pdf", "pdf", 1000, "2024-01-01", "")
        success, message = self.document_manager.remove_document_file(doc)
        
        # According to the implementation, it returns True even if file doesn't exist
        self.assertTrue(success)
        self.assertIn("already removed", message.lower())


class TestSTPAModelDocuments(unittest.TestCase):
    """Test document management in STPAModel"""
    
    def setUp(self):
        """Set up test model"""
        self.model = STPAModel()
    
    def test_add_document(self):
        """Test adding a document to the model"""
        doc = self.model.add_document(
            filename="test_123.pdf",
            original_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            description="Test document"
        )
        
        self.assertEqual(len(self.model.documents), 1)
        self.assertEqual(doc.filename, "test_123.pdf")
        self.assertEqual(doc.original_name, "test.pdf")
        self.assertEqual(doc.description, "Test document")
    
    def test_remove_document(self):
        """Test removing a document from the model"""
        doc = self.model.add_document("test_123.pdf", "test.pdf", "pdf", 1024)
        self.assertEqual(len(self.model.documents), 1)
        
        removed = self.model.remove_document("test_123.pdf")
        self.assertTrue(removed)
        self.assertEqual(len(self.model.documents), 0)
        
        # Try to remove non-existent document
        removed = self.model.remove_document("nonexistent.pdf")
        self.assertFalse(removed)
    
    def test_get_document(self):
        """Test retrieving a document from the model"""
        doc = self.model.add_document("test_123.pdf", "test.pdf", "pdf", 1024)
        
        retrieved = self.model.get_document("test_123.pdf")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.filename, "test_123.pdf")
        
        # Try to get non-existent document
        not_found = self.model.get_document("nonexistent.pdf")
        self.assertIsNone(not_found)


class TestDocumentSerialization(unittest.TestCase):
    """Test document serialization in file I/O"""
    
    def setUp(self):
        """Set up test model with documents"""
        self.model = STPAModel(name="Test Model")
        self.model.add_document(
            filename="doc1_123.pdf",
            original_name="document1.pdf",
            file_type="pdf",
            file_size=1024000,
            description="First test document"
        )
        self.model.add_document(
            filename="img1_456.png",
            original_name="image1.png",
            file_type="png",
            file_size=512000,
            description="Test image"
        )
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up temporary file"""
        os.unlink(self.temp_file.name)
    
    def test_save_and_load_with_documents(self):
        """Test saving and loading a model with documents"""
        # Save model
        STPAModelIO.save_json(self.model, self.temp_file.name)
        
        # Load model
        loaded_model = STPAModelIO.load_json(self.temp_file.name)
        
        # Verify documents were preserved
        self.assertEqual(len(loaded_model.documents), 2)
        
        # Check first document
        doc1 = loaded_model.get_document("doc1_123.pdf")
        self.assertIsNotNone(doc1)
        self.assertEqual(doc1.original_name, "document1.pdf")
        self.assertEqual(doc1.file_type, "pdf")
        self.assertEqual(doc1.file_size, 1024000)
        self.assertEqual(doc1.description, "First test document")
        
        # Check second document
        doc2 = loaded_model.get_document("img1_456.png")
        self.assertIsNotNone(doc2)
        self.assertEqual(doc2.original_name, "image1.png")
        self.assertEqual(doc2.file_type, "png")
        self.assertEqual(doc2.file_size, 512000)
        self.assertEqual(doc2.description, "Test image")
    
    def test_load_model_without_documents(self):
        """Test loading a model file that doesn't have documents section"""
        # Create a minimal model JSON without documents
        data = {
            "version": "0.4.6",
            "name": "Test Model",
            "description": "",
            "control_structure": {"nodes": [], "edges": []},
            "losses": [],
            "hazards": [],
            "unsafe_control_actions": [],
            "uca_contexts": [],
            "loss_scenarios": [],
            "metadata": {},
            "chat_transcripts": {"control_structure": "", "description": "", "losses_hazards": "", "uca": "", "scenarios": ""}
        }
        
        with open(self.temp_file.name, 'w') as f:
            import json
            json.dump(data, f)
        
        # Should load without error and have empty documents list
        loaded_model = STPAModelIO.load_json(self.temp_file.name)
        self.assertEqual(len(loaded_model.documents), 0)


if __name__ == '__main__':
    unittest.main()