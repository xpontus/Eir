"""
Document manager for handling file operations and validation.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from core.models import Document


@dataclass
class DocumentValidationResult:
    """Result of document validation"""
    is_valid: bool
    error_message: str = ""
    file_type: str = ""
    file_size: int = 0


class DocumentManager:
    """Manages document upload, validation, and file operations"""
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {
        'pdf': ['pdf'],
        'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp']
    }
    
    # Maximum file size (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, project_directory: Optional[str] = None):
        """Initialize document manager
        
        Args:
            project_directory: Base directory for storing project documents
                              If None, will use current working directory + 'documents'
        """
        if project_directory is None:
            project_directory = os.path.join(os.getcwd(), 'documents')
        
        self.project_directory = Path(project_directory)
        self.documents_dir = self.project_directory / 'documents'
        
        # Create documents directory if it doesn't exist
        self.documents_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file_path: str) -> DocumentValidationResult:
        """Validate if a file can be uploaded as a document
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            DocumentValidationResult with validation status and details
        """
        if not os.path.exists(file_path):
            return DocumentValidationResult(
                is_valid=False,
                error_message="File does not exist"
            )
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return DocumentValidationResult(
                is_valid=False,
                error_message=f"File too large ({size_mb:.1f} MB). Maximum size is {self.MAX_FILE_SIZE // (1024 * 1024)} MB"
            )
        
        # Check file extension
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        file_type = self._get_file_type(file_extension)
        
        if not file_type:
            supported_exts = []
            for ext_list in self.SUPPORTED_EXTENSIONS.values():
                supported_exts.extend(ext_list)
            return DocumentValidationResult(
                is_valid=False,
                error_message=f"Unsupported file type '.{file_extension}'. Supported types: {', '.join(supported_exts)}"
            )
        
        return DocumentValidationResult(
            is_valid=True,
            file_type=file_extension,
            file_size=file_size
        )
    
    def _get_file_type(self, extension: str) -> Optional[str]:
        """Get the file type category for an extension"""
        extension = extension.lower()
        
        for category, extensions in self.SUPPORTED_EXTENSIONS.items():
            if extension in extensions:
                return extension
        
        return None
    
    def upload_document(self, source_path: str, original_name: Optional[str] = None) -> Tuple[bool, str, Optional[Document]]:
        """Upload a document to the project documents directory
        
        Args:
            source_path: Path to the source file
            original_name: Original filename (if different from source)
            
        Returns:
            Tuple of (success, message, document_info)
        """
        # Validate file first
        validation = self.validate_file(source_path)
        if not validation.is_valid:
            return False, validation.error_message, None
        
        try:
            # Generate unique filename to avoid conflicts
            if original_name is None:
                original_name = os.path.basename(source_path)
            
            file_extension = Path(source_path).suffix.lower()
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            destination_path = self.documents_dir / unique_filename
            
            # Copy file to documents directory
            shutil.copy2(source_path, destination_path)
            
            # Create document info
            document = Document(
                filename=unique_filename,
                original_name=original_name,
                file_type=validation.file_type,
                file_size=validation.file_size,
                upload_date="",  # Will be set by the model when added
                description=""
            )
            
            return True, f"Document '{original_name}' uploaded successfully", document
            
        except Exception as e:
            return False, f"Failed to upload document: {str(e)}", None
    
    def get_document_path(self, document: Document) -> Path:
        """Get the full path to a document file"""
        return self.documents_dir / document.filename
    
    def document_exists(self, document: Document) -> bool:
        """Check if a document file exists on disk"""
        return self.get_document_path(document).exists()
    
    def remove_document_file(self, document: Document) -> Tuple[bool, str]:
        """Remove a document file from disk
        
        Args:
            document: Document to remove
            
        Returns:
            Tuple of (success, message)
        """
        try:
            document_path = self.get_document_path(document)
            if document_path.exists():
                document_path.unlink()
                return True, f"Document '{document.original_name}' removed successfully"
            else:
                return True, f"Document '{document.original_name}' was already removed"
                
        except Exception as e:
            return False, f"Failed to remove document: {str(e)}"
    
    def get_document_info(self, document: Document) -> dict:
        """Get detailed information about a document"""
        document_path = self.get_document_path(document)
        
        info = {
            'original_name': document.original_name,
            'filename': document.filename,
            'file_type': document.file_type,
            'file_size': document.file_size,
            'file_size_mb': document.file_size / (1024 * 1024),
            'upload_date': document.upload_date,
            'description': document.description,
            'exists_on_disk': document_path.exists(),
            'full_path': str(document_path),
            'is_image': document.is_image,
            'is_pdf': document.is_pdf
        }
        
        return info
    
    def cleanup_orphaned_files(self, valid_documents: List[Document]) -> Tuple[int, List[str]]:
        """Remove files in documents directory that are not referenced in the model
        
        Args:
            valid_documents: List of documents that should be kept
            
        Returns:
            Tuple of (number_removed, list_of_removed_filenames)
        """
        valid_filenames = {doc.filename for doc in valid_documents}
        removed_files = []
        
        try:
            for file_path in self.documents_dir.iterdir():
                if file_path.is_file() and file_path.name not in valid_filenames:
                    file_path.unlink()
                    removed_files.append(file_path.name)
            
            return len(removed_files), removed_files
            
        except Exception as e:
            # Return partial results if cleanup fails partway through
            return len(removed_files), removed_files
    
    def set_project_directory(self, project_directory: str):
        """Update the project directory for document storage"""
        self.project_directory = Path(project_directory)
        self.documents_dir = self.project_directory / 'documents'
        self.documents_dir.mkdir(parents=True, exist_ok=True)