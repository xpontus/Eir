"""
Unsafe Control Actions (UCA) Analysis Tab.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, 
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QComboBox, QGroupBox, QListWidget, QListWidgetItem, QTabWidget,
    QScrollArea, QFrame, QCheckBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from core.models import STPAModel
from ui.shared_components import TabChatPanel


class UCACategory(Enum):
    """Categories of unsafe control actions."""
    NOT_PROVIDED = "Not Provided"
    PROVIDED_INCORRECTLY = "Provided Incorrectly" 
    WRONG_TIMING = "Wrong Timing"
    STOPPED_TOO_SOON_OR_TOO_LONG = "Stopped Too Soon/Applied Too Long"


@dataclass
class ControlAction:
    """Represents a control action extracted from the control structure."""
    id: str
    name: str
    source_node: str
    target_node: str
    description: str = ""
    
    def __str__(self):
        return f"{self.source_node} → {self.target_node}: {self.name}"


@dataclass 
class Context:
    """Represents an operational context or system state."""
    id: str
    name: str
    description: str
    conditions: List[str] = field(default_factory=list)
    
    def __str__(self):
        return self.name


@dataclass
class UnsafeControlAction:
    """Represents an identified unsafe control action."""
    id: str
    control_action: ControlAction
    context: Context
    category: UCACategory
    hazard_links: List[str] = field(default_factory=list)
    rationale: str = ""
    severity: int = 1  # 1-5 scale
    likelihood: int = 1  # 1-5 scale
    
    @property
    def risk_score(self) -> int:
        """Calculate risk score (severity × likelihood)."""
        return self.severity * self.likelihood
    
    def __str__(self):
        return f"UCA-{self.id}: {self.control_action.name} [{self.category.value}] in {self.context.name}"


class ControlActionExtractor:
    """Extracts control actions from the control structure graph."""
    
    @staticmethod
    def extract_from_model(model: STPAModel) -> List[ControlAction]:
        """Extract control actions from the control structure."""
        control_actions = []
        
        # Get the NetworkX graph from the control structure
        G = model.control_structure  # ControlStructure IS the graph
        
        for u, v, key, data in G.edges(keys=True, data=True):
            # Get node names
            source_name = G.nodes[u].get('name', f'n{u}')
            target_name = G.nodes[v].get('name', f'n{v}')
            
            # Create control action
            ca_id = f"CA-{u}-{v}-{key}"
            ca_name = data.get('name', f"{source_name}_to_{target_name}")
            
            control_action = ControlAction(
                id=ca_id,
                name=ca_name,
                source_node=source_name,
                target_node=target_name,
                description=data.get('description', '')
            )
            
            control_actions.append(control_action)
        
        return control_actions


class ContextManager(QWidget):
    """Widget for managing system contexts."""
    
    contexts_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contexts: List[Context] = []
        self._setup_ui()
        self._setup_default_contexts()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("System Contexts")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Context list
        self.context_list = QListWidget()
        self.context_list.itemSelectionChanged.connect(self._on_context_selected)
        layout.addWidget(self.context_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Context")
        add_btn.clicked.connect(self._add_context)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_context)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_context)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        # Context details
        details_group = QGroupBox("Context Details")
        details_layout = QVBoxLayout(details_group)
        
        self.context_name_edit = QTextEdit()
        self.context_name_edit.setMaximumHeight(60)
        self.context_name_edit.setPlaceholderText("Context name...")
        
        self.context_desc_edit = QTextEdit()
        self.context_desc_edit.setPlaceholderText("Context description...")
        
        details_layout.addWidget(QLabel("Name:"))
        details_layout.addWidget(self.context_name_edit)
        details_layout.addWidget(QLabel("Description:"))
        details_layout.addWidget(self.context_desc_edit)
        
        layout.addWidget(details_group)
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_context_changes)
        layout.addWidget(save_btn)
    
    def _setup_default_contexts(self):
        """Add some default contexts."""
        default_contexts = [
            Context("normal", "Normal Operation", "System operating under normal conditions"),
            Context("startup", "System Startup", "System initialization and startup phase"), 
            Context("shutdown", "System Shutdown", "Controlled system shutdown sequence"),
            Context("emergency", "Emergency Mode", "Emergency or fault conditions"),
            Context("maintenance", "Maintenance Mode", "System maintenance and testing")
        ]
        
        for context in default_contexts:
            self.contexts.append(context)
        
        self._refresh_context_list()
    
    def _refresh_context_list(self):
        """Refresh the context list widget."""
        self.context_list.clear()
        
        for context in self.contexts:
            item = QListWidgetItem(f"{context.name}")
            item.setData(Qt.UserRole, context.id)
            item.setToolTip(context.description)
            self.context_list.addItem(item)
    
    def _on_context_selected(self):
        """Handle context selection."""
        current_item = self.context_list.currentItem()
        if current_item:
            context_id = current_item.data(Qt.UserRole)
            context = self._get_context_by_id(context_id)
            if context:
                self.context_name_edit.setPlainText(context.name)
                self.context_desc_edit.setPlainText(context.description)
    
    def _get_context_by_id(self, context_id: str) -> Optional[Context]:
        """Get context by ID."""
        for context in self.contexts:
            if context.id == context_id:
                return context
        return None
    
    def _add_context(self):
        """Add a new context."""
        # Generate unique ID
        context_id = f"ctx_{len(self.contexts)}"
        
        new_context = Context(
            id=context_id,
            name="New Context",
            description="Description of the new context"
        )
        
        self.contexts.append(new_context)
        self._refresh_context_list()
        self.contexts_changed.emit()
    
    def _edit_context(self):
        """Edit the selected context."""
        current_item = self.context_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a context to edit.")
            return
        
        # Enable editing (already handled by selection)
        pass
    
    def _delete_context(self):
        """Delete the selected context."""
        current_item = self.context_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a context to delete.")
            return
        
        context_id = current_item.data(Qt.UserRole)
        context = self._get_context_by_id(context_id)
        
        if context:
            reply = QMessageBox.question(
                self, "Confirm Delete", 
                f"Delete context '{context.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.contexts.remove(context)
                self._refresh_context_list()
                self.contexts_changed.emit()
    
    def _save_context_changes(self):
        """Save changes to the selected context."""
        current_item = self.context_list.currentItem()
        if not current_item:
            return
        
        context_id = current_item.data(Qt.UserRole)
        context = self._get_context_by_id(context_id)
        
        if context:
            context.name = self.context_name_edit.toPlainText().strip()
            context.description = self.context_desc_edit.toPlainText().strip()
            
            self._refresh_context_list()
            self.contexts_changed.emit()
    
    def get_contexts(self) -> List[Context]:
        """Get all contexts."""
        return self.contexts


class UCAMatrix(QTableWidget):
    """Interactive matrix for UCA analysis."""
    
    uca_created = Signal(UnsafeControlAction)
    uca_updated = Signal(UnsafeControlAction)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.control_actions: List[ControlAction] = []
        self.contexts: List[Context] = []
        self.ucas: Dict[str, UnsafeControlAction] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the matrix UI."""
        # Enable sorting and selection
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # Setup headers
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(80)
        
        # Connect signals
        self.itemChanged.connect(self._on_item_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def setup_matrix(self, control_actions: List[ControlAction], contexts: List[Context]):
        """Setup the matrix with control actions and contexts."""
        self.control_actions = control_actions
        self.contexts = contexts
        
        # Calculate matrix dimensions
        # Rows: Control Actions × UCA Categories
        # Columns: Contexts
        num_rows = len(control_actions) * len(UCACategory)
        num_cols = len(contexts)
        
        self.setRowCount(num_rows)
        self.setColumnCount(num_cols)
        
        # Set column headers (contexts)
        context_headers = [ctx.name for ctx in contexts]
        self.setHorizontalHeaderLabels(context_headers)
        
        # Set row headers (control action + category combinations)
        row_headers = []
        for ca in control_actions:
            for category in UCACategory:
                header = f"{ca.name}\n[{category.value}]"
                row_headers.append(header)
        
        self.setVerticalHeaderLabels(row_headers)
        
        # Initialize matrix cells
        self._initialize_cells()
    
    def _initialize_cells(self):
        """Initialize matrix cells with default states."""
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                # Create cell item
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                
                # Set background color (white = not analyzed, other colors for UCA states)
                item.setBackground(QColor(255, 255, 255))  # White
                
                self.setItem(row, col, item)
    
    def _get_control_action_and_category_for_row(self, row: int) -> tuple[ControlAction, UCACategory]:
        """Get control action and category for a given row."""
        categories = list(UCACategory)
        ca_index = row // len(categories)
        cat_index = row % len(categories)
        
        return self.control_actions[ca_index], categories[cat_index]
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle item changes."""
        row, col = item.row(), item.column()
        control_action, category = self._get_control_action_and_category_for_row(row)
        context = self.contexts[col]
        
        # Interpret cell content
        cell_text = item.text().strip().upper()
        
        if cell_text in ['Y', 'YES', 'UCA', '1']:
            # Mark as UCA
            self._create_or_update_uca(control_action, context, category, True)
            item.setBackground(QColor(255, 200, 200))  # Light red
            item.setText("UCA")
        elif cell_text in ['N', 'NO', 'SAFE', '0', '']:
            # Mark as safe
            self._create_or_update_uca(control_action, context, category, False)
            item.setBackground(QColor(200, 255, 200))  # Light green
            item.setText("Safe")
        else:
            # Unknown state
            item.setBackground(QColor(255, 255, 200))  # Light yellow
    
    def _create_or_update_uca(self, control_action: ControlAction, context: Context, 
                             category: UCACategory, is_unsafe: bool):
        """Create or update a UCA entry."""
        uca_key = f"{control_action.id}_{context.id}_{category.value}"
        
        if is_unsafe:
            if uca_key not in self.ucas:
                # Create new UCA
                uca = UnsafeControlAction(
                    id=f"UCA-{len(self.ucas)+1}",
                    control_action=control_action,
                    context=context,
                    category=category,
                    rationale="User marked as unsafe in matrix"
                )
                self.ucas[uca_key] = uca
                self.uca_created.emit(uca)
            else:
                # Update existing UCA
                self.uca_updated.emit(self.ucas[uca_key])
        else:
            # Remove UCA if it exists
            if uca_key in self.ucas:
                del self.ucas[uca_key]
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle double-click for detailed editing."""
        row, col = item.row(), item.column()
        control_action, category = self._get_control_action_and_category_for_row(row)
        context = self.contexts[col]
        
        # Open detailed UCA editor (simplified for now)
        uca_key = f"{control_action.id}_{context.id}_{category.value}"
        
        if uca_key in self.ucas:
            uca = self.ucas[uca_key]
            # TODO: Open detailed UCA editor dialog
            QMessageBox.information(
                self, "UCA Details",
                f"UCA: {uca}\n\nRationale: {uca.rationale}\n\nClick OK to continue."
            )
    
    def get_ucas(self) -> List[UnsafeControlAction]:
        """Get all identified UCAs."""
        return list(self.ucas.values())


class UCAAnalysisTab(QWidget):
    """Main UCA Analysis tab widget."""
    
    # Signals
    model_changed = Signal()
    
    def __init__(self, model: STPAModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.control_actions: List[ControlAction] = []
        self.ucas: List[UnsafeControlAction] = []
        self._setup_ui()
        self._refresh_data()
    
    def _setup_ui(self):
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Unsafe Control Actions (UCA) Analysis - STPA Step 2")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Systematically identify when control actions become unsafe by analyzing "
            "four categories in different system contexts."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Context management
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Context manager
        self.context_manager = ContextManager()
        self.context_manager.contexts_changed.connect(self._refresh_matrix)
        self.context_manager.contexts_changed.connect(self.model_changed.emit)
        left_layout.addWidget(self.context_manager)
        
        # Control actions list
        ca_group = QGroupBox("Control Actions")
        ca_layout = QVBoxLayout(ca_group)
        
        refresh_btn = QPushButton("Refresh from Control Structure")
        refresh_btn.clicked.connect(self._refresh_data)
        ca_layout.addWidget(refresh_btn)
        
        self.ca_list = QListWidget()
        ca_layout.addWidget(self.ca_list)
        
        left_layout.addWidget(ca_group)
        
        left_panel.setMaximumWidth(300)
        main_splitter.addWidget(left_panel)
        
        # Right panel: UCA Matrix and results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Matrix section
        matrix_group = QGroupBox("UCA Analysis Matrix")
        matrix_layout = QVBoxLayout(matrix_group)
        
        matrix_help = QLabel(
            "Instructions: Click cells to mark as 'UCA' (unsafe) or 'Safe'. "
            "Double-click for detailed editing."
        )
        matrix_help.setWordWrap(True)
        matrix_help.setStyleSheet("color: #666; font-style: italic;")
        matrix_layout.addWidget(matrix_help)
        
        # Scroll area for matrix
        scroll_area = QScrollArea()
        self.uca_matrix = UCAMatrix()
        self.uca_matrix.uca_created.connect(self._on_uca_created)
        self.uca_matrix.uca_updated.connect(self._on_uca_updated)
        scroll_area.setWidget(self.uca_matrix)
        scroll_area.setWidgetResizable(True)
        matrix_layout.addWidget(scroll_area)
        
        right_layout.addWidget(matrix_group)
        
        # UCA Results section
        results_group = QGroupBox("Identified UCAs")
        results_layout = QVBoxLayout(results_group)
        
        self.uca_results = QListWidget()
        results_layout.addWidget(self.uca_results)
        
        export_btn = QPushButton("Export UCA Report")
        export_btn.clicked.connect(self._export_uca_report)
        results_layout.addWidget(export_btn)
        
        right_layout.addWidget(results_group)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 800])
        
        layout.addWidget(main_splitter)
        
        # Chat panel
        self.chat_panel = TabChatPanel("UCA Analysis", self.model, self)
        layout.addWidget(self.chat_panel)
    
    def _refresh_data(self):
        """Refresh control actions from the model."""
        # Extract control actions from control structure
        self.control_actions = ControlActionExtractor.extract_from_model(self.model)
        
        # Update control actions list
        self.ca_list.clear()
        for ca in self.control_actions:
            item = QListWidgetItem(str(ca))
            item.setToolTip(f"Description: {ca.description}")
            self.ca_list.addItem(item)
        
        # Refresh matrix
        self._refresh_matrix()
    
    def _refresh_matrix(self):
        """Refresh the UCA matrix."""
        contexts = self.context_manager.get_contexts()
        if self.control_actions and contexts:
            self.uca_matrix.setup_matrix(self.control_actions, contexts)
    
    def _on_uca_created(self, uca: UnsafeControlAction):
        """Handle new UCA creation."""
        self.ucas.append(uca)
        self._refresh_uca_results()
    
    def _on_uca_updated(self, uca: UnsafeControlAction):
        """Handle UCA updates."""
        self._refresh_uca_results()
    
    def _refresh_uca_results(self):
        """Refresh the UCA results list."""
        self.uca_results.clear()
        
        # Get all UCAs from matrix
        all_ucas = self.uca_matrix.get_ucas()
        
        for uca in all_ucas:
            item_text = f"{uca.id}: {uca.control_action.name} [{uca.category.value}] in {uca.context.name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, uca.id)
            item.setToolTip(f"Rationale: {uca.rationale}")
            self.uca_results.addItem(item)
    
    def _export_uca_report(self):
        """Export UCA analysis report."""
        # Simple export to show functionality
        all_ucas = self.uca_matrix.get_ucas()
        
        if not all_ucas:
            QMessageBox.information(self, "No UCAs", "No unsafe control actions identified yet.")
            return
        
        report = "STPA UCA Analysis Report\n"
        report += "=" * 50 + "\n\n"
        
        for uca in all_ucas:
            report += f"ID: {uca.id}\n"
            report += f"Control Action: {uca.control_action.name}\n"
            report += f"Category: {uca.category.value}\n"
            report += f"Context: {uca.context.name}\n"
            report += f"Rationale: {uca.rationale}\n"
            report += f"Risk Score: {uca.risk_score}\n"
            report += "-" * 30 + "\n"
        
        QMessageBox.information(self, "UCA Report", f"Report generated:\n\n{report[:500]}...")
    
    def get_model_data(self) -> Dict:
        """Get data for saving to model."""
        return {
            "ucas": [
                {
                    "id": uca.id,
                    "control_action_id": uca.control_action.id,
                    "context_id": uca.context.id,
                    "category": uca.category.value,
                    "rationale": uca.rationale,
                    "severity": uca.severity,
                    "likelihood": uca.likelihood,
                    "hazard_links": uca.hazard_links
                }
                for uca in self.uca_matrix.get_ucas()
            ],
            "contexts": [
                {
                    "id": ctx.id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "conditions": ctx.conditions
                }
                for ctx in self.context_manager.get_contexts()
            ]
        }
    
    def set_model(self, model: STPAModel):
        """Set a new model and refresh the view"""
        self.model = model
        self._refresh_data()
    
    def sync_to_model(self):
        """Sync current state to model"""
        # Import the model classes we need
        from core.models import UnsafeControlAction as ModelUCA, UCAContext as ModelUCAContext
        
        # Update model with current UCAs and contexts
        # This method ensures all UCA data is saved to the model
        all_ucas = self.uca_matrix.get_ucas()
        all_contexts = self.context_manager.get_contexts()
        
        # Convert UCAs to model format
        self.model.unsafe_control_actions = []
        for uca in all_ucas:
            model_uca = ModelUCA(
                id=uca.id,
                control_action=uca.control_action.name,
                context=uca.context.name,
                category=uca.category.value,
                hazard_links=uca.hazard_links,
                rationale=uca.rationale,
                severity=uca.severity,
                likelihood=uca.likelihood
            )
            self.model.unsafe_control_actions.append(model_uca)
        
        # Convert contexts to model format  
        self.model.uca_contexts = []
        for ctx in all_contexts:
            model_ctx = ModelUCAContext(
                id=ctx.id,
                name=ctx.name,
                description=ctx.description,
                conditions=ctx.conditions
            )
            self.model.uca_contexts.append(model_ctx)
        
        # Save chat transcript
        if hasattr(self, 'chat_panel'):
            self.chat_panel._save_chat_transcript()
        
        # Emit signal to notify of model changes
        self.model_changed.emit()
