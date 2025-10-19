"""
System Description tab.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QFormLayout, QGroupBox, QPushButton, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, Signal

from core.models import STPAModel
from ui.shared_components import TabChatPanel
from ui.document_widget import DocumentWidget


class SystemDescriptionTab(QWidget):
    """Tab for editing system description and general information"""
    
    # Signals
    model_changed = Signal()
    
    def __init__(self, model: STPAModel, main_window=None):
        super().__init__()
        
        self.model = model
        self.main_window = main_window
        
        self._setup_ui()
        self._load_from_model()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QHBoxLayout(self)  # Changed to horizontal layout
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side: Main content
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Header
        header_label = QLabel("System Description")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        left_layout.addWidget(header_label)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # System name
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("System Name:", self.name_edit)
        
        # Version
        self.version_edit = QLineEdit()
        self.version_edit.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("Version:", self.version_edit)
        
        # Author(s)
        self.author_edit = QLineEdit()
        self.author_edit.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("Author(s):", self.author_edit)
        
        left_layout.addWidget(basic_group)
        
        # System Description Group
        desc_group = QGroupBox("System Description")
        desc_layout = QVBoxLayout(desc_group)
        
        desc_layout.addWidget(QLabel("Purpose and Overview:"))
        self.purpose_edit = QTextEdit()
        self.purpose_edit.setPlaceholderText("Describe the purpose and high-level overview of the system...")
        self.purpose_edit.textChanged.connect(self._on_field_changed)
        desc_layout.addWidget(self.purpose_edit)
        
        desc_layout.addWidget(QLabel("System Boundaries:"))
        self.boundaries_edit = QTextEdit()
        self.boundaries_edit.setPlaceholderText("Define what is included and excluded from the analysis...")
        self.boundaries_edit.textChanged.connect(self._on_field_changed)
        desc_layout.addWidget(self.boundaries_edit)
        
        desc_layout.addWidget(QLabel("Key Assumptions:"))
        self.assumptions_edit = QTextEdit()
        self.assumptions_edit.setPlaceholderText("List key assumptions made in the analysis...")
        self.assumptions_edit.textChanged.connect(self._on_field_changed)
        desc_layout.addWidget(self.assumptions_edit)
        
        left_layout.addWidget(desc_group)
        
        # Safety Context Group
        safety_group = QGroupBox("Safety Context")
        safety_layout = QVBoxLayout(safety_group)
        
        safety_layout.addWidget(QLabel("Safety Objectives:"))
        self.objectives_edit = QTextEdit()
        self.objectives_edit.setPlaceholderText("What are the main safety objectives for this system?...")
        self.objectives_edit.textChanged.connect(self._on_field_changed)
        safety_layout.addWidget(self.objectives_edit)
        
        safety_layout.addWidget(QLabel("Regulatory Context:"))
        self.regulatory_edit = QTextEdit()
        self.regulatory_edit.setPlaceholderText("Relevant standards, regulations, and compliance requirements...")
        self.regulatory_edit.textChanged.connect(self._on_field_changed)
        safety_layout.addWidget(self.regulatory_edit)
        
        left_layout.addWidget(safety_group)
        
        # Documents Group
        docs_group = QGroupBox("Project Documents")
        docs_layout = QVBoxLayout(docs_group)
        
        self.document_widget = DocumentWidget(self.model)
        self.document_widget.documents_changed.connect(self._on_documents_changed)
        docs_layout.addWidget(self.document_widget)
        
        left_layout.addWidget(docs_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_to_model)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._load_from_model)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        left_layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("System description - Changes are auto-saved")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()  # Push everything to the top
        
        splitter.addWidget(left_widget)
        
        # Right side: Chat panel
        self.chat_panel = TabChatPanel("System Description", self.model, self)
        splitter.addWidget(self.chat_panel)
        
        # Set splitter sizes (70% content, 30% chat)
        splitter.setSizes([700, 300])
    
    def set_model(self, model: STPAModel):
        """Set a new model and refresh the view"""
        self.model = model
        self.document_widget.set_model(model)
        self._load_from_model()
        if self.main_window:
            self.main_window._update_window_title()
    
    def _load_from_model(self):
        """Load data from the model into the UI"""
        # Basic information
        self.name_edit.setText(self.model.name)
        self.version_edit.setText(self.model.version)
        
        # Get author from metadata
        author = self.model.metadata.get('author', '')
        self.author_edit.setText(author)
        
        # Description fields from metadata
        self.purpose_edit.setPlainText(self.model.metadata.get('purpose', ''))
        self.boundaries_edit.setPlainText(self.model.metadata.get('boundaries', ''))
        self.assumptions_edit.setPlainText(self.model.metadata.get('assumptions', ''))
        self.objectives_edit.setPlainText(self.model.metadata.get('safety_objectives', ''))
        self.regulatory_edit.setPlainText(self.model.metadata.get('regulatory_context', ''))
        
        self.status_label.setText("System description loaded")
    
    def sync_to_model(self):
        """Update the model with current field values"""
        self.save_to_model()
        # Sync document widget
        self.document_widget.sync_to_model()
        # Save chat transcript
        if hasattr(self, 'chat_panel'):
            self.chat_panel._save_chat_transcript()
    
    def save_to_model(self):
        """Save current field values to the model"""
        # Basic information
        self.model.name = self.name_edit.text().strip() or "Untitled STPA Model"
        self.model.version = self.version_edit.text().strip()
        
        # Store in metadata
        self.model.metadata['author'] = self.author_edit.text().strip()
        self.model.metadata['purpose'] = self.purpose_edit.toPlainText().strip()
        self.model.metadata['boundaries'] = self.boundaries_edit.toPlainText().strip()
        self.model.metadata['assumptions'] = self.assumptions_edit.toPlainText().strip()
        self.model.metadata['safety_objectives'] = self.objectives_edit.toPlainText().strip()
        self.model.metadata['regulatory_context'] = self.regulatory_edit.toPlainText().strip()
        
        # Update main window title if name changed
        if self.main_window:
            self.main_window._update_window_title()
        
        self.status_label.setText("Changes saved to model")
        self.model_changed.emit()
    
    def _on_field_changed(self):
        """Handle field changes for auto-save"""
        # Auto-save after a short delay (could be improved with QTimer)
        # For now, just update the status
        self.status_label.setText("Unsaved changes - click Save or changes auto-save on tab switch")
        
        # Auto-save basic info fields immediately since they affect window title
        if self.sender() == self.name_edit:
            self.model.name = self.name_edit.text().strip() or "Untitled STPA Model"
            if self.main_window:
                self.main_window._update_window_title()
            self.model_changed.emit()
    
    def _on_documents_changed(self):
        """Handle document changes"""
        self.model_changed.emit()
        self.status_label.setText("Document changes saved to model")
