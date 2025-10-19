"""
Main window for Eir.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMenuBar, QStatusBar, QMessageBox, 
    QFileDialog, QVBoxLayout, QWidget, QApplication, QLabel, QPushButton,
    QSizePolicy, QToolBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap, QIcon

from core.models import STPAModel
from core.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, DEFAULT_MODEL_NAME, VERSION
from core.file_io import STPAModelIO
from ui.control_structure_tab import ControlStructureTab
from ui.description_tab import SystemDescriptionTab
from ui.losses_hazards_tab import LossesHazardsTab
from ui.uca_analysis_tab import UCAAnalysisTab
from ui.help_system import HelpPanel


class STPAMainWindow(QMainWindow):
    """Main window with tabbed interface for STPA analysis"""
    
    def __init__(self):
        super().__init__()
        
        # Create the data model
        self.model = STPAModel()
        self.model.name = DEFAULT_MODEL_NAME
        self._current_file_format: str = "json"  # "json" or "graphml"
        self._current_file_path: Optional[str] = None
        self._has_unsaved_changes: bool = False
        
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        
        # Set initial window properties
        self.setWindowTitle(f"Eir v{VERSION}")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        self.statusBar().showMessage("Ready - Create a new model or load an existing one")
    
    def _setup_ui(self):
        """Set up the tabbed user interface"""
        # Set up toolbar with logo and help button
        self._setup_toolbar()
        
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tab 1: Control Structure (the current graph editor functionality)
        self.control_structure_tab = ControlStructureTab(self.model, self)
        self.tabs.addTab(self.control_structure_tab, "Control Structure")
        
        # Tab 2: System Description
        self.description_tab = SystemDescriptionTab(self.model, self)
        self.tabs.addTab(self.description_tab, "System Description")
        
        # Tab 3: Losses & Hazards
        self.losses_hazards_tab = LossesHazardsTab(self.model, self)
        self.tabs.addTab(self.losses_hazards_tab, "Losses & Hazards")
        
        # Tab 4: Unsafe Control Actions (NEW!)
        self.uca_analysis_tab = UCAAnalysisTab(self.model, self)
        self.tabs.addTab(self.uca_analysis_tab, "UCA Analysis")
        
        # Tab 5: Loss Scenarios (placeholder for future)
        scenarios_placeholder = QWidget()
        self.tabs.addTab(scenarios_placeholder, "Scenarios (Future)")
        
        # Set up Help System (NEW!)
        self.help_panel = HelpPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.help_panel)
        
        # Connect tab changes to help system for context-sensitive help
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Set the control structure tab as the initial tab
        self.tabs.setCurrentIndex(0)
    
    def _setup_toolbar(self):
        """Set up toolbar with logo and help button"""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)  # Keep toolbar in place
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        
        # Try to load and add logo
        try:
            logo_path = Path(__file__).parent.parent / "eir2.png"
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                # Scale logo to reasonable size
                scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setToolTip("Eir")
                toolbar.addWidget(logo_label)
                
                # Add separator after logo
                toolbar.addSeparator()
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Add title label
        title_label = QLabel("Eir")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 0 10px;")
        toolbar.addWidget(title_label)
        
        # Add stretch to push file operations to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # File operation buttons
        new_btn = QPushButton("New")
        new_btn.setToolTip("Create new model (Ctrl+N)")
        new_btn.clicked.connect(self.new_model)
        toolbar.addWidget(new_btn)
        
        load_btn = QPushButton("Load")
        load_btn.setToolTip("Load model (Ctrl+O)")
        load_btn.clicked.connect(self.load_model)
        toolbar.addWidget(load_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save model (Ctrl+S)")
        save_btn.clicked.connect(self.save_model)
        toolbar.addWidget(save_btn)
        
        save_as_btn = QPushButton("Save As")
        save_as_btn.setToolTip("Save model as... (Ctrl+Shift+S)")
        save_as_btn.clicked.connect(self.save_model_as)
        toolbar.addWidget(save_as_btn)
        
        # Add separator before help button
        toolbar.addSeparator()
        
        # Add spacer to push help button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Help button
        help_button = QPushButton("?")
        help_button.setToolTip("Show Help Panel (F1)")
        help_button.setFixedSize(30, 30)
        help_button.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        help_button.clicked.connect(self.show_help_panel)
        toolbar.addWidget(help_button)
    
    def _setup_menu(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_model)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        # Save
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_model)
        file_menu.addAction(save_action)
        
        # Save As
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_model_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Load
        load_action = QAction("Load", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_model)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # Show Help Panel
        help_panel_action = QAction("Show Help Panel", self)
        help_panel_action.setShortcut("F1")
        help_panel_action.triggered.connect(self.show_help_panel)
        help_menu.addAction(help_panel_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About Eir", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Quick Help Button (as an action)
        quick_help_action = QAction("? Quick Help", self)
        quick_help_action.setShortcut("F1")
        quick_help_action.triggered.connect(self.show_help_panel)
        help_menu.addAction(quick_help_action)
    
    def _connect_signals(self):
        """Connect signals between tabs"""
        # Connect model change signals to track unsaved changes
        self.control_structure_tab.model_changed.connect(self._mark_as_changed)
        self.description_tab.model_changed.connect(self._mark_as_changed)
        self.losses_hazards_tab.model_changed.connect(self._mark_as_changed)
        self.uca_analysis_tab.model_changed.connect(self._mark_as_changed)
    
    def _mark_as_changed(self):
        """Mark the model as having unsaved changes"""
        self._has_unsaved_changes = True
        self._update_window_title()
    
    def _mark_as_saved(self):
        """Mark the model as saved (no unsaved changes)"""
        self._has_unsaved_changes = False
        self._update_window_title()
    
    # File operations
    def new_model(self):
        """Create a new STPA model"""
        if self._confirm_unsaved_changes():
            self.model = STPAModel()
            self._current_file_path = None
            self._current_file_format = "json"
            self._has_unsaved_changes = False
            
            # Notify all tabs of the new model
            self.control_structure_tab.set_model(self.model)
            self.description_tab.set_model(self.model)
            self.losses_hazards_tab.set_model(self.model)
            self.uca_analysis_tab.set_model(self.model)
            
            self._update_window_title()
            self.statusBar().showMessage("New STPA model created")
    
    def save_model(self):
        """Save the current model"""
        if not self._current_file_path:
            return self.save_model_as()
        
        try:
            self._save_model_to_path(self._current_file_path, self._current_file_format)
            self._mark_as_saved()
            self._update_window_title()
            self.statusBar().showMessage(f"Model saved to {self._current_file_path}")
        except Exception as e:
            error_msg = f"Could not save model: {str(e)}"
            QMessageBox.critical(self, "Save Failed", error_msg)
            self.statusBar().showMessage("Save failed")
    
    def save_model_as(self):
        """Save the model as JSON format"""
        # File save dialog - JSON only
        default_path = self._current_file_path if self._current_file_path else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Eir Model", 
            default_path, "JSON Files (*.json)"
        )
        
        if not path:
            return
            
        # Ensure correct extension
        if not path.lower().endswith(".json"):
            path += ".json"
            
        try:
            self._save_model_to_path(path, "json")
            self._current_file_path = path
            self._current_file_format = "json"
            self._mark_as_saved()
            self._update_window_title()
            self.statusBar().showMessage(f"Model saved to {path}")
        except Exception as e:
            error_msg = f"Could not save model: {str(e)}"
            QMessageBox.critical(self, "Save Failed", error_msg)
            self.statusBar().showMessage("Save failed")
    
    def load_model(self):
        """Load an Eir model (JSON format)"""
        if not self._confirm_unsaved_changes():
            return

        # Show file dialog - JSON only
        path, selected_filter = QFileDialog.getOpenFileName(
            self, "Load Eir Model", 
            self._current_file_path or "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not path:
            return
            
        try:
            self._load_model_from_path(path)
            self._current_file_path = path
            self._current_file_format = "json"
            self._has_unsaved_changes = False
            
            self._update_window_title()
            self.statusBar().showMessage(f"Model loaded from {path}")
            
        except FileNotFoundError:
            error_msg = f"File not found: {path}"
            QMessageBox.critical(self, "Load Failed", error_msg)
            self.statusBar().showMessage("Load failed - file not found")
        except ValueError as e:
            error_msg = f"Invalid file format: {str(e)}"
            QMessageBox.critical(self, "Load Failed", error_msg)
            self.statusBar().showMessage("Load failed - invalid format")
        except Exception as e:
            error_msg = f"Could not load model: {str(e)}"
            QMessageBox.critical(self, "Load Failed", error_msg)
            self.statusBar().showMessage("Load failed")
    
    def _save_model_to_path(self, path: str, format_type: str):
        """Save model to specific path (JSON only)"""
        # Update model with current tab states
        self._sync_model_from_tabs()
        
        # Always save as JSON
        STPAModelIO.save_json(self.model, path)
    
    def _load_model_from_path(self, path: str):
        """Load model from path (JSON only)"""
        # Always load as JSON
        self.model = STPAModelIO.load_json(path)
        
        # Update all tabs with the new model
        self.control_structure_tab.set_model(self.model)
        self.description_tab.set_model(self.model)
        self.losses_hazards_tab.set_model(self.model)
        self.uca_analysis_tab.set_model(self.model)
    
    def _sync_model_from_tabs(self):
        """Update the model with current state from all tabs"""
        # Each tab will update its portion of the model
        self.control_structure_tab.sync_to_model()
        self.description_tab.sync_to_model()
        self.losses_hazards_tab.sync_to_model()
        self.uca_analysis_tab.sync_to_model()
    
    def _update_window_title(self):
        """Update window title with current model name and file"""
        title = f"Eir v{VERSION} - {self.model.name}"
        if self._current_file_path:
            title += f" [{Path(self._current_file_path).name}]"
        if self._has_unsaved_changes:
            title += " *"
        self.setWindowTitle(title)
    
    def _confirm_unsaved_changes(self) -> bool:
        """Ask user about unsaved changes. Returns True if it's OK to proceed."""
        if not self._has_unsaved_changes:
            return True
            
        reply = QMessageBox.question(
            self, "Unsaved Changes", 
            "You have unsaved changes. Do you want to continue without saving?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    def show_about(self):
        """Show the About dialog"""
        QMessageBox.about(
            self, "About Eir",
            f"""<h3>Eir v{VERSION}</h3>
            <p>A comprehensive System-Theoretic Process Analysis (STPA) tool for safety analysis.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Interactive control structure modeling with inline editing</li>
            <li>Complete undo/redo system for all operations</li>
            <li>UCA Analysis with interactive matrix</li>
            <li>Integrated help system with context-sensitive content</li>
            <li>Node state machines for dynamic behavior</li>
            <li>Losses and hazards management</li>
            <li>Multi-format file support (JSON, GraphML)</li>
            <li>Integrated chat assistance</li>
            <li>Multi-edge visualization</li>
            </ul>
            <p><b>Version {VERSION}</b> - Enhanced with Help System and UCA Analysis</p>
            """
        )
    
    def show_help_panel(self):
        """Show the help panel"""
        if self.help_panel.isVisible():
            self.help_panel.hide()
        else:
            self.help_panel.show()
            self._update_contextual_help()
    
    def _on_tab_changed(self, index: int):
        """Handle tab change to update contextual help"""
        self._update_contextual_help()
        
        # Set focus to the current tab to ensure it receives key events
        current_widget = self.tabs.currentWidget()
        if current_widget:
            current_widget.setFocus(Qt.TabFocusReason)
    
    def keyPressEvent(self, event):
        """Forward key events to the current tab if it can handle them"""
        current_widget = self.tabs.currentWidget()
        
        # Check if current tab has its own keyPressEvent
        if current_widget and hasattr(current_widget, 'keyPressEvent'):
            current_widget.keyPressEvent(event)
            return
            
        super().keyPressEvent(event)
    
    def _update_contextual_help(self):
        """Update help panel with context-sensitive content"""
        if not self.help_panel.isVisible():
            return
        
        current_index = self.tabs.currentIndex()
        tab_contexts = {
            0: "control_structure",
            1: "system_description",  # System Description
            2: "stpa_methodology",  # Losses & Hazards
            3: "uca_analysis",  # UCA Analysis
            4: "stpa_methodology"   # Scenarios (future)
        }
        
        context = tab_contexts.get(current_index, "getting_started")
        self.help_panel.show_contextual_help(context)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self._confirm_unsaved_changes():
            event.accept()
        else:
            event.ignore()


def main():
    """Main entry point for Eir"""
    app = QApplication(sys.argv)
    
    try:
        window = STPAMainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            QMessageBox.critical(None, "Fatal Error", f"{e}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
