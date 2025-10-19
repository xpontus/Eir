"""
Document management widget for the System Description tab.
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QGroupBox, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QMenu, QFrame
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QPixmap, QIcon

from core.models import STPAModel, Document
from core.document_manager import DocumentManager


class DocumentDetailsDialog(QDialog):
    """Dialog for viewing/editing document details"""
    
    def __init__(self, document: Document, parent=None):
        super().__init__(parent)
        self.document = document
        self.setWindowTitle(f"Document Details - {document.original_name}")
        self.setMinimumSize(400, 300)
        
        self._setup_ui()
        self._load_document_info()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form layout for document info
        form_layout = QFormLayout()
        
        # Original name (read-only)
        self.name_label = QLabel()
        form_layout.addRow("Original Name:", self.name_label)
        
        # File type (read-only)
        self.type_label = QLabel()
        form_layout.addRow("File Type:", self.type_label)
        
        # File size (read-only)
        self.size_label = QLabel()
        form_layout.addRow("File Size:", self.size_label)
        
        # Upload date (read-only)
        self.date_label = QLabel()
        form_layout.addRow("Upload Date:", self.date_label)
        
        # Description (editable)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_document_info(self):
        """Load document information into the form"""
        self.name_label.setText(self.document.original_name)
        self.type_label.setText(self.document.file_type.upper())
        
        # Format file size
        size_mb = self.document.file_size / (1024 * 1024)
        if size_mb < 1:
            size_kb = self.document.file_size / 1024
            self.size_label.setText(f"{size_kb:.1f} KB")
        else:
            self.size_label.setText(f"{size_mb:.1f} MB")
        
        # Format upload date
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(self.document.upload_date)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            self.date_label.setText(formatted_date)
        except:
            self.date_label.setText(self.document.upload_date)
        
        self.description_edit.setPlainText(self.document.description)
    
    def get_description(self) -> str:
        """Get the updated description"""
        return self.description_edit.toPlainText().strip()


class DocumentWidget(QWidget):
    """Widget for managing project documents"""
    
    # Signals
    documents_changed = Signal()
    
    def __init__(self, model: STPAModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.document_manager = DocumentManager()
        
        self._setup_ui()
        self._refresh_document_list()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Project Documents")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Upload button
        self.upload_btn = QPushButton("Upload Document")
        self.upload_btn.clicked.connect(self._upload_document)
        header_layout.addWidget(self.upload_btn)
        
        layout.addLayout(header_layout)
        
        # Document list
        self.document_list = QListWidget()
        self.document_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.document_list.customContextMenuRequested.connect(self._show_context_menu)
        self.document_list.itemDoubleClicked.connect(self._view_document_details)
        layout.addWidget(self.document_list)
        
        # Info label
        self.info_label = QLabel("Drag and drop files here or use the Upload button")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
    
    def _refresh_document_list(self):
        """Refresh the document list display"""
        self.document_list.clear()
        
        for document in self.model.documents:
            item = QListWidgetItem()
            
            # Create display text
            display_text = document.original_name
            if document.description:
                display_text += f"\n{document.description[:50]}{'...' if len(document.description) > 50 else ''}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, document.filename)  # Store filename for reference
            
            # Add icon based on file type
            if document.is_image:
                item.setToolTip(f"Image file: {document.original_name}")
            elif document.is_pdf:
                item.setToolTip(f"PDF document: {document.original_name}")
            else:
                item.setToolTip(f"Document: {document.original_name}")
            
            self.document_list.addItem(item)
        
        # Update info label
        doc_count = len(self.model.documents)
        if doc_count == 0:
            self.info_label.setText("No documents uploaded. Drag and drop files here or use the Upload button.")
        else:
            self.info_label.setText(f"{doc_count} document{'s' if doc_count != 1 else ''} uploaded")
    
    def _upload_document(self):
        """Handle document upload via file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload Document",
            "",
            "All Supported (*.pdf *.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp);;"
            "PDF Files (*.pdf);;"
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp);;"
            "All Files (*)"
        )
        
        if file_path:
            self._add_document(file_path)
    
    def _add_document(self, file_path: str) -> bool:
        """Add a document to the project
        
        Args:
            file_path: Path to the file to add
            
        Returns:
            True if document was added successfully
        """
        # Upload document through document manager
        success, message, document_info = self.document_manager.upload_document(file_path)
        
        if success and document_info:
            # Add to model
            added_document = self.model.add_document(
                filename=document_info.filename,
                original_name=document_info.original_name,
                file_type=document_info.file_type,
                file_size=document_info.file_size,
                description=document_info.description
            )
            
            self._refresh_document_list()
            self.documents_changed.emit()
            self.status_label.setText(f"✅ {message}")
            return True
        else:
            self.status_label.setText(f"❌ {message}")
            QMessageBox.warning(self, "Upload Failed", message)
            return False
    
    def _show_context_menu(self, position):
        """Show context menu for document list"""
        item = self.document_list.itemAt(position)
        if not item:
            return
        
        filename = item.data(Qt.UserRole)
        document = self.model.get_document(filename)
        if not document:
            return
        
        menu = QMenu(self)
        
        # View details action
        details_action = QAction("View Details...", self)
        details_action.triggered.connect(lambda: self._view_document_details(item))
        menu.addAction(details_action)
        
        menu.addSeparator()
        
        # Remove action
        remove_action = QAction("Remove Document", self)
        remove_action.triggered.connect(lambda: self._remove_document(filename))
        menu.addAction(remove_action)
        
        menu.exec(self.document_list.mapToGlobal(position))
    
    def _view_document_details(self, item):
        """View document details dialog"""
        filename = item.data(Qt.UserRole)
        document = self.model.get_document(filename)
        if not document:
            return
        
        dialog = DocumentDetailsDialog(document, self)
        if dialog.exec() == QDialog.Accepted:
            # Update description if changed
            new_description = dialog.get_description()
            if new_description != document.description:
                document.description = new_description
                self._refresh_document_list()
                self.documents_changed.emit()
                self.status_label.setText("Document description updated")
    
    def _remove_document(self, filename: str):
        """Remove a document from the project"""
        document = self.model.get_document(filename)
        if not document:
            return
        
        reply = QMessageBox.question(
            self,
            "Remove Document",
            f"Are you sure you want to remove '{document.original_name}' from the project?\n\n"
            "This will delete the file from the project documents folder.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove file from disk
            success, message = self.document_manager.remove_document_file(document)
            
            # Remove from model
            self.model.remove_document(filename)
            
            self._refresh_document_list()
            self.documents_changed.emit()
            
            if success:
                self.status_label.setText(f"✅ {message}")
            else:
                self.status_label.setText(f"⚠️ Document removed from project, but file removal failed: {message}")
    
    def set_model(self, model: STPAModel):
        """Set a new model and refresh the display"""
        self.model = model
        self._refresh_document_list()
    
    def sync_to_model(self):
        """Sync any pending changes to the model (placeholder for consistency)"""
        # Document changes are immediately synced to the model
        pass
    
    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    self._add_document(file_path)
            event.acceptProposedAction()