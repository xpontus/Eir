"""
Shared UI components.
"""

from typing import Optional, Dict, Any
import json
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QFormLayout, QGroupBox, QPlainTextEdit,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QTextCursor, QColor

from core.models import STPAModel
from core.ai_integration import get_ai_manager


class AIResponseWorker(QThread):
    """Worker thread for generating AI responses without blocking UI"""
    response_ready = Signal(str)
    
    def __init__(self, user_input: str, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.user_input = user_input
        self.context = context
        
    def run(self):
        """Generate AI response in background thread"""
        try:
            ai_manager = get_ai_manager()
            response = ai_manager.generate_response(self.user_input, self.context)
            self.response_ready.emit(response)
        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {str(e)}\n\nI'm still here to help with STPA methodology questions!"
            self.response_ready.emit(error_response)


class ChatConsole(QPlainTextEdit):
    """Chat console with input/output merged for AI interaction"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # AI integration
        self.context_provider = None  # Will be set by parent tab
        self.ai_worker = None
        
        # Setup appearance
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        # Configuration
        self.setMaximumBlockCount(1000)  # Limit history
        self.setPlaceholderText("Type your message and press Ctrl+Enter to send...")
        
        # State
        self.transcript = ""
        self.input_start_pos = 0
        self.waiting_for_response = False
        
        # Initialize with welcome message
        self._add_system_message("STPA Assistant: Hello! I'm here to help with your STPA analysis. Ask me about:\n• Control structure design\n• Identifying losses and hazards\n• STPA methodology\n• Safety analysis techniques\n\nType your questions below and press Ctrl+Enter, Shift+Enter, or Cmd+Enter to send.")
    
    def keyPressEvent(self, event):
        """Handle key press events for chat input"""
        # Handle Ctrl+Enter, Shift+Enter, or Cmd+Enter for sending
        if (event.key() == Qt.Key_Return and 
            (event.modifiers() == Qt.ControlModifier or 
             event.modifiers() == Qt.ShiftModifier or 
             event.modifiers() == Qt.MetaModifier)):  # Meta is Cmd on macOS
            self._send_message()
            return
        
        # Handle normal typing (only allow at the end)
        if not self.waiting_for_response:
            cursor = self.textCursor()
            if cursor.position() < self.input_start_pos:
                # Move cursor to end if trying to type in history
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
        
        super().keyPressEvent(event)
    
    def _add_system_message(self, message: str):
        """Add a system message to the chat"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if self.toPlainText():
            cursor.insertText("\n\n")
        
        # Format system message
        cursor.insertText(f"{message}\n")
        cursor.insertText("-" * 50 + "\n")
        
        self._update_input_position()
        self.ensureCursorVisible()
    
    def _add_user_message(self, message: str):
        """Add a user message to the chat"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"\nUser: {message}\n")
        self._update_input_position()
    
    def _add_assistant_message(self, message: str):
        """Add an assistant response to the chat"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"\nAssistant: {message}\n")
        cursor.insertText("-" * 30 + "\n")
        self._update_input_position()
        self.ensureCursorVisible()
    
    def _update_input_position(self):
        """Update the position where new input should start"""
        self.input_start_pos = len(self.toPlainText())
    
    def _send_message(self):
        """Send the current message"""
        if self.waiting_for_response:
            return
        
        # Get the input text (everything after input_start_pos)
        full_text = self.toPlainText()
        if len(full_text) <= self.input_start_pos:
            return
        
        user_input = full_text[self.input_start_pos:].strip()
        if not user_input:
            return
        
        # Add user message to transcript
        self._add_user_message(user_input)
        
        # Set waiting state
        self.waiting_for_response = True
        
        # Generate AI response using real AI
        self._generate_ai_response(user_input)
    
    def _generate_ai_response(self, user_input: str):
        """Generate AI response using Ollama"""
        # Get context from parent tab if available
        context = self._get_current_context()
        
        # Start AI worker thread
        self.ai_worker = AIResponseWorker(user_input, context)
        self.ai_worker.response_ready.connect(self._on_ai_response_ready)
        self.ai_worker.start()
    
    def _get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current context from parent tab"""
        if not self.context_provider:
            return None
            
        try:
            return self.context_provider()
        except Exception as e:
            print(f"Error getting context: {e}")
            return None
    
    def _on_ai_response_ready(self, response: str):
        """Handle AI response when ready"""
        self._add_assistant_message(response)
        self.waiting_for_response = False
        
        # Clean up worker
        if self.ai_worker:
            self.ai_worker.deleteLater()
            self.ai_worker = None
    
    def set_context_provider(self, provider_func):
        """Set function to provide context information to AI"""
        self.context_provider = provider_func
    
    def get_transcript(self) -> str:
        """Get the full chat transcript"""
        return self.toPlainText()
    
    def set_transcript(self, transcript: str):
        """Set the chat transcript"""
        self.setPlainText(transcript)
        self._update_input_position()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)


class PropertiesPane(QWidget):
    """Properties panel for editing selected items"""
    
    # Signals
    property_changed = Signal(str, str, object)  # item_id, property_name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_item_id: Optional[str] = None
        self.current_item_type: Optional[str] = None  # 'node' or 'edge'
        self.current_item_data: Optional[dict] = None
        
        self._setup_ui()
        self.clear_properties()
    
    def _setup_ui(self):
        """Set up the properties UI"""
        layout = QVBoxLayout(self)
        
        # Title
        self.title = QLabel("Properties")
        self.title.setStyleSheet("font-weight: 600; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(self.title)
        
        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(600)  # Increased from 400
        
        # Properties widget
        self.props_widget = QWidget()
        self.props_layout = QVBoxLayout(self.props_widget)
        scroll.setWidget(self.props_widget)
        layout.addWidget(scroll)
        
        # Status
        self.status_label = QLabel("Select an item to edit its properties")
        self.status_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def clear_properties(self):
        """Clear all property editors"""
        # Clear layout
        for i in reversed(range(self.props_layout.count())):
            item = self.props_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.title.setText("Properties")
        self.status_label.setText("Select an item to edit its properties")
        self.current_item_id = None
        self.current_item_type = None
        self.current_item_data = None
    
    def show_node_properties(self, node_id: str, node_data: dict):
        """Show properties for a node"""
        self.current_item_id = node_id
        self.current_item_type = 'node'
        self.current_item_data = node_data.copy()
        
        self._clear_layout()
        self.title.setText(f"Node Properties: {node_id}")
        self.status_label.setText(f"Editing node: {node_id}")
        
        # Create property editors
        form_layout = QFormLayout()
        
        # Name
        name_edit = QLineEdit(node_data.get('name', ''))
        name_edit.editingFinished.connect(lambda: self._property_changed('name', name_edit.text()))
        form_layout.addRow("Name:", name_edit)
        
        # Node Type
        type_combo = QComboBox()
        type_combo.addItems(['controller', 'controlled_process', 'actuator', 'sensor', 'other'])
        current_type = node_data.get('node_type', 'other')
        index = type_combo.findText(current_type)
        if index >= 0:
            type_combo.setCurrentIndex(index)
        type_combo.currentTextChanged.connect(lambda text: self._property_changed('node_type', text))
        form_layout.addRow("Type:", type_combo)
        
        # Shape selector
        shape_combo = QComboBox()
        shape_combo.addItems(['circle', 'rectangle', 'hexagon'])
        current_shape = node_data.get('shape', 'circle')
        index = shape_combo.findText(current_shape)
        if index >= 0:
            shape_combo.setCurrentIndex(index)
        shape_combo.currentTextChanged.connect(lambda text: self._property_changed('shape', text))
        form_layout.addRow("Shape:", shape_combo)
        
        # Size selector
        size_edit = QLineEdit(str(node_data.get('size', 24.0)))
        size_edit.editingFinished.connect(lambda: self._property_changed('size', size_edit.text()))
        form_layout.addRow("Size:", size_edit)
        
        # Description
        desc_edit = QTextEdit()
        desc_edit.setPlainText(node_data.get('description', ''))
        desc_edit.setMaximumHeight(80)
        desc_edit.textChanged.connect(lambda: self._property_changed('description', desc_edit.toPlainText()))
        form_layout.addRow("Description:", desc_edit)
        
        # Position (read-only)
        position = node_data.get('position', (0, 0))
        pos_label = QLabel(f"({position[0]:.1f}, {position[1]:.1f})")
        pos_label.setStyleSheet("color: #6c757d;")
        form_layout.addRow("Position:", pos_label)
        
        # State Machine section
        states_group = QGroupBox("State Machine")
        states_layout = QVBoxLayout(states_group)
        
        # States list
        states = node_data.get('states', [])
        self.states_edit = QTextEdit()
        if isinstance(states, list) and len(states) > 0:
            if isinstance(states[0], str):
                # Simple string list
                states_text = '\n'.join([f"- {state}" for state in states])
            else:
                # Dictionary list with names and descriptions
                states_text = '\n'.join([f"- {state.get('name', '')}: {state.get('description', '')}" for state in states])
        else:
            states_text = ""
        self.states_edit.setPlainText(states_text)
        self.states_edit.setMaximumHeight(100)
        self.states_edit.setPlaceholderText("No states defined yet...\nClick 'Edit States' to add states.")
        self.states_edit.textChanged.connect(lambda: self._states_text_changed())
        states_layout.addWidget(QLabel("Current States:"))
        states_layout.addWidget(self.states_edit)
        
        # Add state button
        add_state_btn = QPushButton("Edit States...")
        add_state_btn.clicked.connect(self._edit_states)
        states_layout.addWidget(add_state_btn)
        
        form_layout.addRow(states_group)
        
        # Add form to layout
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.props_layout.addWidget(form_widget)
    
    def show_edge_properties(self, edge_id: str, edge_data: dict):
        """Show properties for an edge"""
        self.current_item_id = edge_id
        self.current_item_type = 'edge'
        self.current_item_data = edge_data.copy()
        
        self._clear_layout()
        self.title.setText(f"Link Properties: {edge_id}")
        self.status_label.setText(f"Editing link: {edge_id}")
        
        # Create property editors
        form_layout = QFormLayout()
        
        # Label
        label_edit = QLineEdit(edge_data.get('label', ''))
        label_edit.editingFinished.connect(lambda: self._property_changed('label', label_edit.text()))
        form_layout.addRow("Label:", label_edit)
        
        # Link Type
        type_combo = QComboBox()
        type_combo.addItems(['control_action', 'feedback', 'disturbance', 'information', 'other'])
        current_type = edge_data.get('link_type', 'control_action')
        index = type_combo.findText(current_type)
        if index >= 0:
            type_combo.setCurrentIndex(index)
        type_combo.currentTextChanged.connect(lambda text: self._property_changed('link_type', text))
        form_layout.addRow("Type:", type_combo)
        
        # Description
        desc_edit = QTextEdit()
        desc_edit.setPlainText(edge_data.get('description', ''))
        desc_edit.setMaximumHeight(80)
        desc_edit.textChanged.connect(lambda: self._property_changed('description', desc_edit.toPlainText()))
        form_layout.addRow("Description:", desc_edit)
        
        # Source and Target (read-only)
        source_label = QLabel(edge_data.get('source_id', 'Unknown'))
        source_label.setStyleSheet("color: #6c757d;")
        form_layout.addRow("Source:", source_label)
        
        target_label = QLabel(edge_data.get('target_id', 'Unknown'))
        target_label.setStyleSheet("color: #6c757d;")
        form_layout.addRow("Target:", target_label)
        
        # Add form to layout
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.props_layout.addWidget(form_widget)
    
    def _clear_layout(self):
        """Clear the properties layout"""
        for i in reversed(range(self.props_layout.count())):
            item = self.props_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
    
    def _property_changed(self, property_name: str, value):
        """Handle property changes"""
        if self.current_item_id and self.current_item_data is not None:
            self.current_item_data[property_name] = value
            self.property_changed.emit(self.current_item_id, property_name, value)
    
    def _states_text_changed(self):
        """Handle changes to the states text"""
        if hasattr(self, 'states_edit') and self.current_item_id:
            text = self.states_edit.toPlainText()
            # Parse states from text (simple format: "- state_name")
            states = []
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    state_name = line[2:].strip()
                    if ':' in state_name:
                        name, desc = state_name.split(':', 1)
                        states.append(name.strip())
                    else:
                        states.append(state_name)
            self._property_changed('states', states)
    
    def _edit_states(self):
        """Open state machine editor (placeholder)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "State Machine Editor", 
                              "State machine editor will be implemented in the next iteration.\n\n"
                              "For now, you can edit states directly in the text field above.\n"
                              "Format: '- state_name' (one per line)")


class TabChatPanel(QWidget):
    """Chat panel specifically designed for tabs with context awareness"""
    
    def __init__(self, tab_name: str, model: STPAModel, parent=None):
        super().__init__(parent)
        
        self.tab_name = tab_name
        self.model = model
        
        self._setup_ui()
        
        # Load chat transcript for this tab
        self._load_chat_transcript()
    
    def _setup_ui(self):
        """Set up the chat panel UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"{self.tab_name} - AI Assistant")
        header.setStyleSheet("font-weight: 600; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(header)
        
        # Chat console
        self.console = ChatConsole(self)
        layout.addWidget(self.console)
        
        # Set up context provider for AI
        self.console.set_context_provider(self._get_tab_context)
        
        # Connect to model changes to update context
        if hasattr(self.console, 'property_changed'):
            self.console.property_changed.connect(self._save_chat_transcript)
    
    def _get_tab_context(self) -> Dict[str, Any]:
        """Provide context information for AI responses"""
        context = {
            "current_tab": self.tab_name,
            "model_info": {
                "node_count": len(self.model.control_structure.nodes),
                "edge_count": len(self.model.control_structure.edges),
                "losses_count": len(self.model.losses),
                "hazards_count": len(self.model.hazards),
            }
        }
        
        # Add project name if available
        if hasattr(self.model, 'name') and self.model.name:
            context["project_name"] = self.model.name
            
        # Add selected items if parent has selection info
        if hasattr(self.parent(), 'get_selected_items'):
            try:
                selected = self.parent().get_selected_items()
                if selected:
                    context["selected_items"] = selected
            except:
                pass
                
        return context
    
    def _load_chat_transcript(self):
        """Load chat transcript for this tab from model"""
        if hasattr(self.model, 'chat_transcripts') and self.tab_name in self.model.chat_transcripts:
            self.console.set_transcript(self.model.chat_transcripts[self.tab_name])
    
    def _save_chat_transcript(self):
        """Save chat transcript to model"""
        if hasattr(self.model, 'chat_transcripts'):
            self.model.chat_transcripts[self.tab_name] = self.console.get_transcript()
    
    def get_transcript(self) -> str:
        """Get the chat transcript"""
        return self.console.get_transcript()
    
    def set_transcript(self, transcript: str):
        """Set the chat transcript"""
        self.console.set_transcript(transcript)
