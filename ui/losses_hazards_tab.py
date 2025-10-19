"""
Losses & Hazards tab.
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QTextEdit, QLabel,
    QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal

from core.models import STPAModel, Loss, Hazard
from core.validation import InputValidator, ValidationError
from ui.shared_components import TabChatPanel


class LossesHazardsTab(QWidget):
    """Tab for managing losses and hazards"""
    
    # Signals
    model_changed = Signal()
    
    def __init__(self, model: STPAModel, main_window=None):
        super().__init__()
        
        self.model = model
        self.main_window = main_window
        
        self._setup_ui()
        self._refresh_lists()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QHBoxLayout(self)  # Changed to horizontal layout
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left side: Losses and Hazards content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Header
        header_label = QLabel("Losses & Hazards")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(header_label)
        
        # Create splitter for losses and hazards
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # Losses section
        losses_widget = self._create_losses_widget()
        splitter.addWidget(losses_widget)
        
        # Hazards section  
        hazards_widget = self._create_hazards_widget()
        splitter.addWidget(hazards_widget)
        
        # Set equal sizes
        splitter.setSizes([700, 700])
        
        # Status
        self.status_label = QLabel("Manage losses and hazards - Double-click to edit")
        content_layout.addWidget(self.status_label)
        
        main_splitter.addWidget(content_widget)
        
        # Right side: Chat panel
        self.chat_panel = TabChatPanel("Losses & Hazards", self.model, self)
        main_splitter.addWidget(self.chat_panel)
        
        # Set main splitter sizes (70% content, 30% chat)
        main_splitter.setSizes([700, 300])
        
        # Update status
        self._update_status()
    
    def _create_losses_widget(self) -> QWidget:
        """Create the losses management widget"""
        losses_group = QGroupBox("Losses")
        layout = QVBoxLayout(losses_group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_loss_btn = QPushButton("Add Loss")
        add_loss_btn.clicked.connect(self.add_loss)
        toolbar.addWidget(add_loss_btn)
        
        edit_loss_btn = QPushButton("Edit Loss")
        edit_loss_btn.clicked.connect(self.edit_selected_loss)
        toolbar.addWidget(edit_loss_btn)
        
        del_loss_btn = QPushButton("Delete Loss")
        del_loss_btn.clicked.connect(self.delete_selected_loss)
        toolbar.addWidget(del_loss_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Loss list
        self.losses_list = QListWidget()
        self.losses_list.itemDoubleClicked.connect(self.edit_selected_loss)
        layout.addWidget(self.losses_list)
        
        # Loss details
        self.loss_details = QTextEdit()
        self.loss_details.setReadOnly(True)
        self.loss_details.setMaximumHeight(150)
        self.loss_details.setPlaceholderText("Select a loss to view details...")
        layout.addWidget(QLabel("Loss Details:"))
        layout.addWidget(self.loss_details)
        
        # Connect selection change
        self.losses_list.currentItemChanged.connect(self._on_loss_selection_changed)
        
        return losses_group
    
    def _create_hazards_widget(self) -> QWidget:
        """Create the hazards management widget"""
        hazards_group = QGroupBox("Hazards") 
        layout = QVBoxLayout(hazards_group)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_hazard_btn = QPushButton("Add Hazard")
        add_hazard_btn.clicked.connect(self.add_hazard)
        toolbar.addWidget(add_hazard_btn)
        
        edit_hazard_btn = QPushButton("Edit Hazard")
        edit_hazard_btn.clicked.connect(self.edit_selected_hazard)
        toolbar.addWidget(edit_hazard_btn)
        
        del_hazard_btn = QPushButton("Delete Hazard")
        del_hazard_btn.clicked.connect(self.delete_selected_hazard)
        toolbar.addWidget(del_hazard_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Hazard list
        self.hazards_list = QListWidget()
        self.hazards_list.itemDoubleClicked.connect(self.edit_selected_hazard)
        layout.addWidget(self.hazards_list)
        
        # Hazard details
        self.hazard_details = QTextEdit()
        self.hazard_details.setReadOnly(True)
        self.hazard_details.setMaximumHeight(150)
        self.hazard_details.setPlaceholderText("Select a hazard to view details...")
        layout.addWidget(QLabel("Hazard Details:"))
        layout.addWidget(self.hazard_details)
        
        # Connect selection change
        self.hazards_list.currentItemChanged.connect(self._on_hazard_selection_changed)
        
        return hazards_group
    
    def set_model(self, model: STPAModel):
        """Set a new model and refresh the view"""
        self.model = model
        self._refresh_lists()
    
    def sync_to_model(self):
        """Sync current state to model (already synced via direct editing)"""
        # Save chat transcript
        if hasattr(self, 'chat_panel'):
            self.chat_panel._save_chat_transcript()
    
    def _refresh_lists(self):
        """Refresh both losses and hazards lists"""
        # Clear lists
        self.losses_list.clear()
        self.hazards_list.clear()
        
        # Populate losses
        for i, loss in enumerate(self.model.losses):
            item = QListWidgetItem(f"L-{i+1}: {loss.description[:50]}...")
            item.setData(Qt.UserRole, i)  # Store index
            self.losses_list.addItem(item)
        
        # Populate hazards
        for i, hazard in enumerate(self.model.hazards):
            item = QListWidgetItem(f"H-{i+1}: {hazard.description[:50]}...")
            item.setData(Qt.UserRole, i)  # Store index
            self.hazards_list.addItem(item)
        
        # Clear details
        self.loss_details.clear()
        self.hazard_details.clear()
        
        self._update_status()
    
    def _update_status(self):
        """Update status label"""
        loss_count = len(self.model.losses)
        hazard_count = len(self.model.hazards)
        self.status_label.setText(f"Losses: {loss_count}, Hazards: {hazard_count} - Double-click to edit")
    
    def _on_loss_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle loss selection change"""
        if current is None:
            self.loss_details.clear()
            return
        
        loss_index = current.data(Qt.UserRole)
        if 0 <= loss_index < len(self.model.losses):
            loss = self.model.losses[loss_index]
            details = f"<b>Description:</b><br>{loss.description}<br><br>"
            if loss.severity:
                details += f"<b>Severity:</b> {loss.severity}<br><br>"
            if loss.rationale:
                details += f"<b>Rationale:</b><br>{loss.rationale}"
            
            self.loss_details.setHtml(details)
    
    def _on_hazard_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle hazard selection change"""
        if current is None:
            self.hazard_details.clear()
            return
        
        hazard_index = current.data(Qt.UserRole)
        if 0 <= hazard_index < len(self.model.hazards):
            hazard = self.model.hazards[hazard_index]
            details = f"<b>Description:</b><br>{hazard.description}<br><br>"
            if hazard.severity:
                details += f"<b>Severity:</b> {hazard.severity}<br><br>"
            if hazard.rationale:
                details += f"<b>Rationale:</b><br>{hazard.rationale}<br><br>"
            
            # Show related losses
            if hazard.related_losses:
                details += f"<b>Related Losses:</b> {', '.join(hazard.related_losses)}"
            
            self.hazard_details.setHtml(details)
    
    def add_loss(self):
        """Add a new loss"""
        dialog = LossDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            loss_data = dialog.get_result()
            loss = Loss(**loss_data)
            self.model.losses.append(loss)
            
            self._refresh_lists()
            self.model_changed.emit()
    
    def edit_selected_loss(self):
        """Edit the selected loss"""
        current = self.losses_list.currentItem()
        if current is None:
            QMessageBox.information(self, "Edit Loss", "Please select a loss to edit.")
            return
        
        loss_index = current.data(Qt.UserRole)
        if 0 <= loss_index < len(self.model.losses):
            loss = self.model.losses[loss_index]
            
            dialog = LossDialog(loss_data=loss.__dict__, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_result()
                
                # Update the loss
                for key, value in updated_data.items():
                    setattr(loss, key, value)
                
                self._refresh_lists()
                self.model_changed.emit()
    
    def delete_selected_loss(self):
        """Delete the selected loss"""
        current = self.losses_list.currentItem()
        if current is None:
            QMessageBox.information(self, "Delete Loss", "Please select a loss to delete.")
            return
        
        loss_index = current.data(Qt.UserRole)
        if 0 <= loss_index < len(self.model.losses):
            loss = self.model.losses[loss_index]
            
            reply = QMessageBox.question(
                self, "Delete Loss",
                f"Are you sure you want to delete this loss?\n\n{loss.description[:100]}...",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.model.losses[loss_index]
                self._refresh_lists()
                self.model_changed.emit()
    
    def add_hazard(self):
        """Add a new hazard"""
        dialog = HazardDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            hazard_data = dialog.get_result()
            hazard = Hazard(**hazard_data)
            self.model.hazards.append(hazard)
            
            self._refresh_lists()
            self.model_changed.emit()
    
    def edit_selected_hazard(self):
        """Edit the selected hazard"""
        current = self.hazards_list.currentItem()
        if current is None:
            QMessageBox.information(self, "Edit Hazard", "Please select a hazard to edit.")
            return
        
        hazard_index = current.data(Qt.UserRole)
        if 0 <= hazard_index < len(self.model.hazards):
            hazard = self.model.hazards[hazard_index]
            
            dialog = HazardDialog(hazard_data=hazard.__dict__, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_result()
                
                # Update the hazard
                for key, value in updated_data.items():
                    setattr(hazard, key, value)
                
                self._refresh_lists()
                self.model_changed.emit()
    
    def delete_selected_hazard(self):
        """Delete the selected hazard"""
        current = self.hazards_list.currentItem()
        if current is None:
            QMessageBox.information(self, "Delete Hazard", "Please select a hazard to delete.")
            return
        
        hazard_index = current.data(Qt.UserRole)
        if 0 <= hazard_index < len(self.model.hazards):
            hazard = self.model.hazards[hazard_index]
            
            reply = QMessageBox.question(
                self, "Delete Hazard",
                f"Are you sure you want to delete this hazard?\n\n{hazard.description[:100]}...",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.model.hazards[hazard_index]
                self._refresh_lists()
                self.model_changed.emit()


class LossDialog(QDialog):
    """Dialog for adding/editing losses"""
    
    def __init__(self, loss_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Edit Loss" if loss_data else "Add Loss")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QFormLayout(self)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe the loss (e.g., 'Loss of life or injury to people')")
        if loss_data:
            self.description_edit.setPlainText(loss_data.get('description', ''))
        layout.addRow("Description:", self.description_edit)
        
        # Severity
        self.severity_edit = QLineEdit()
        self.severity_edit.setPlaceholderText("e.g., 'High', 'Medium', 'Low'")
        if loss_data:
            self.severity_edit.setText(loss_data.get('severity', ''))
        layout.addRow("Severity:", self.severity_edit)
        
        # Rationale
        self.rationale_edit = QTextEdit()
        self.rationale_edit.setPlaceholderText("Why is this considered a loss? What makes it significant?")
        if loss_data:
            self.rationale_edit.setPlainText(loss_data.get('rationale', ''))
        layout.addRow("Rationale:", self.rationale_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _validate_and_accept(self):
        """Validate input before accepting the dialog"""
        try:
            # Validate required fields
            description = InputValidator.validate_required_text(
                self.description_edit.toPlainText(), "Description"
            )
            severity = InputValidator.validate_severity(self.severity_edit.text())
            rationale = InputValidator.validate_description(
                self.rationale_edit.toPlainText(), 1000
            )
            self.accept()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
    
    def get_result(self) -> dict:
        """Get the dialog result"""
        return {
            'description': self.description_edit.toPlainText().strip(),
            'severity': self.severity_edit.text().strip(),
            'rationale': self.rationale_edit.toPlainText().strip()
        }


class HazardDialog(QDialog):
    """Dialog for adding/editing hazards"""
    
    def __init__(self, hazard_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Edit Hazard" if hazard_data else "Add Hazard")
        self.setModal(True)
        self.resize(500, 500)
        
        layout = QFormLayout(self)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe the hazard (e.g., 'Vehicle collides with another object')")
        if hazard_data:
            self.description_edit.setPlainText(hazard_data.get('description', ''))
        layout.addRow("Description:", self.description_edit)
        
        # Severity
        self.severity_edit = QLineEdit()
        self.severity_edit.setPlaceholderText("e.g., 'High', 'Medium', 'Low'")
        if hazard_data:
            self.severity_edit.setText(hazard_data.get('severity', ''))
        layout.addRow("Severity:", self.severity_edit)
        
        # Rationale
        self.rationale_edit = QTextEdit()
        self.rationale_edit.setPlaceholderText("Why is this a hazard? What conditions lead to this hazard?")
        if hazard_data:
            self.rationale_edit.setPlainText(hazard_data.get('rationale', ''))
        layout.addRow("Rationale:", self.rationale_edit)
        
        # Related losses
        self.losses_edit = QLineEdit()
        self.losses_edit.setPlaceholderText("Comma-separated list of related loss IDs (e.g., 'L-1, L-3')")
        if hazard_data and hazard_data.get('related_losses'):
            self.losses_edit.setText(', '.join(hazard_data['related_losses']))
        layout.addRow("Related Losses:", self.losses_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_result(self) -> dict:
        """Get the dialog result"""
        # Parse related losses
        losses_text = self.losses_edit.text().strip()
        related_losses = []
        if losses_text:
            related_losses = [loss.strip() for loss in losses_text.split(',') if loss.strip()]
        
        return {
            'description': self.description_edit.toPlainText().strip(),
            'severity': self.severity_edit.text().strip(),
            'rationale': self.rationale_edit.toPlainText().strip(),
            'related_losses': related_losses
        }
