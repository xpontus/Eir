"""
Help System for Eir.
"""

import os
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
    QLineEdit, QListWidget, QListWidgetItem, QSplitter, QPushButton,
    QLabel, QTabWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QIcon, QPixmap


class HelpContentManager:
    """Manages help content and provides context-sensitive information."""
    
    def __init__(self):
        self.content_cache = {}
        self._load_help_content()
    
    def _load_help_content(self):
        """Load all help content into memory."""
        self.content_cache = {
            "getting_started": {
                "title": "Getting Started with Eir",
                "content": """
<h2>Welcome to Eir!</h2>

<p>This interactive tool helps you conduct comprehensive Systems-Theoretic Process Analysis (STPA) for safety-critical systems.</p>

<h3>🚀 Quick Start</h3>
<ol>
<li><strong>System Description</strong>: Define your system boundaries, purpose, and upload supporting documents</li>
<li><strong>Losses & Hazards</strong>: Identify what must be prevented</li>
<li><strong>Control Structure</strong>: Build your interactive system model</li>
<li><strong>UCA Analysis</strong>: Identify unsafe control actions</li>
</ol>

<h3>✨ New in v0.4.6</h3>
<ul>
<li><strong>Document Management</strong>: Upload PDFs and images to the System Description tab</li>
<li><strong>Drag & Drop</strong>: Easy file uploads with format validation</li>
<li><strong>Project Integration</strong>: Documents saved with your STPA project</li>
</ul>

<h3>💡 Pro Tips</h3>
<ul>
<li>Use <kbd>Ctrl+Z</kbd> to undo any operation</li>
<li>Click directly on nodes/edges to edit their names</li>
<li>Hold <kbd>C</kbd> over a node and move to another to create edges quickly</li>
<li>Upload system diagrams and requirements to the System Description tab</li>
<li>Ask the AI assistant questions about STPA methodology</li>
</ul>
                """,
                "keywords": ["start", "begin", "intro", "overview"]
            },
            
            "system_description": {
                "title": "System Description & Document Management",
                "content": """
<h2>System Description Tab</h2>

<p>The System Description tab is where you define your system boundaries, upload supporting documents, and establish the foundation for your STPA analysis.</p>

<h3>📋 Basic Information</h3>
<ul>
<li><strong>System Name</strong>: Give your project a clear, descriptive name</li>
<li><strong>Version</strong>: Track different versions of your analysis</li>
<li><strong>Author(s)</strong>: Record who is conducting the analysis</li>
</ul>

<h3>📖 System Description Fields</h3>
<ul>
<li><strong>Purpose and Overview</strong>: High-level description of what the system does</li>
<li><strong>System Boundaries</strong>: Define what is included and excluded from analysis</li>
<li><strong>Key Assumptions</strong>: Document assumptions made during analysis</li>
<li><strong>Safety Objectives</strong>: What are the main safety goals?</li>
<li><strong>Regulatory Context</strong>: Relevant standards and compliance requirements</li>
</ul>

<h3>📄 Document Management System</h3>
<p><strong>New in v0.4.6!</strong> Upload and manage supporting documents for your STPA project.</p>

<h4>🔄 Uploading Documents</h4>
<ul>
<li><strong>Upload Button</strong>: Click "Upload Document" to browse and select files</li>
<li><strong>Drag & Drop</strong>: Simply drag files from your computer into the document area</li>
<li><strong>Supported Formats</strong>: PDF documents and images (PNG, JPG, JPEG, GIF, BMP, SVG, WebP)</li>
<li><strong>File Size Limit</strong>: Maximum 50MB per file with automatic validation</li>
</ul>

<h4>📚 Managing Documents</h4>
<ul>
<li><strong>Document List</strong>: View all uploaded documents with metadata</li>
<li><strong>View Details</strong>: Double-click documents to view/edit descriptions</li>
<li><strong>Context Menu</strong>: Right-click for options (view details, remove)</li>
<li><strong>Project Integration</strong>: Documents are saved with your project files</li>
</ul>

<h4>💡 Document Management Tips</h4>
<ul>
<li>Add descriptions to help organize and find documents later</li>
<li>Upload system diagrams, requirements, and reference materials</li>
<li>Documents are automatically stored in your project's documents folder</li>
<li>Remove unused documents to keep your project organized</li>
</ul>

<h3>💾 Auto-Save Features</h3>
<ul>
<li><strong>System Name</strong>: Updates window title immediately</li>
<li><strong>Document Changes</strong>: Saved automatically when modified</li>
<li><strong>Manual Save</strong>: Use "Save Changes" button or tab switching to save all fields</li>
</ul>
                """,
                "keywords": ["system", "description", "document", "upload", "boundary", "purpose", "files", "pdf", "images"]
            },
            
            "control_structure": {
                "title": "Control Structure Editor",
                "content": """
<h2>Interactive Control Structure Modeling</h2>

<h3>🎯 Interaction Modes</h3>
<ul>
<li><strong>Add Node</strong>: Click anywhere to create nodes, drag existing nodes to move them</li>
<li><strong>Connect</strong>: Click source then target node, or use C+drag method</li>
<li><strong>Move/Select</strong>: Pure movement and selection mode</li>
<li><strong>Delete</strong>: Click to remove nodes or edges</li>
</ul>

<h3>✏️ Inline Editing</h3>
<p>Click directly on any node or edge label to edit the text. Use:</p>
<ul>
<li><kbd>Enter</kbd>: Save changes</li>
<li><kbd>Escape</kbd>: Cancel editing</li>
<li>Click elsewhere: Auto-save and close editor</li>
</ul>

<h3>🔄 Undo/Redo System</h3>
<p>Every action is tracked and reversible:</p>
<ul>
<li><kbd>Ctrl+Z</kbd>: Undo last operation</li>
<li><kbd>Ctrl+Y</kbd>: Redo next operation</li>
<li>50-operation history maintained</li>
<li>All changes (text, properties, movement) are undoable</li>
</ul>

<h3>📊 Multi-Edge Support</h3>
<p>Create multiple edges between the same nodes to model complex relationships. Edges automatically curve to prevent overlap.</p>
                """,
                "keywords": ["control", "structure", "graph", "nodes", "edges", "editor"]
            },
            
            "uca_analysis": {
                "title": "Unsafe Control Actions (UCA) Analysis",
                "content": """
<h2>UCA Analysis - STPA Step 2</h2>

<h3>🎯 Purpose</h3>
<p>Systematically identify when control actions become unsafe by analyzing four categories:</p>

<h3>📋 UCA Categories</h3>
<ol>
<li><strong>Not Provided</strong>: Control action not given when needed</li>
<li><strong>Provided Incorrectly</strong>: Wrong control action given</li>
<li><strong>Wrong Timing</strong>: Correct action at wrong time (too early/late)</li>
<li><strong>Stopped Too Soon/Applied Too Long</strong>: Duration problems</li>
</ol>

<h3>🔍 Analysis Process</h3>
<ol>
<li>Extract control actions from your control structure</li>
<li>Define system contexts (operational modes, environmental conditions)</li>
<li>For each control action + context combination, ask: "Could this be unsafe?"</li>
<li>Link identified UCAs to system hazards</li>
<li>Document rationale for each UCA</li>
</ol>

<h3>💡 Best Practices</h3>
<ul>
<li>Be systematic - check every control action in every relevant context</li>
<li>Consider edge cases and failure modes</li>
<li>Link UCAs clearly to specific hazards</li>
<li>Document your reasoning for future reference</li>
</ul>
                """,
                "keywords": ["uca", "unsafe", "control", "actions", "analysis", "step2"]
            },
            
            "stpa_methodology": {
                "title": "STPA Methodology Overview",
                "content": """
<h2>Systems-Theoretic Process Analysis (STPA)</h2>

<h3>🎯 What is STPA?</h3>
<p>STPA is a modern hazard analysis technique that focuses on unsafe interactions and inadequate control rather than just component failures.</p>

<h3>📋 STPA Process</h3>

<h4>Step 0: System Definition</h4>
<ul>
<li>Define system purpose and boundaries</li>
<li>Identify stakeholders and assumptions</li>
<li>Document high-level requirements</li>
</ul>

<h4>Step 1: Hazard Analysis</h4>
<ul>
<li>Identify system losses (what must be prevented)</li>
<li>Define hazards (system states that can lead to losses)</li>
<li>Create control structure model</li>
</ul>

<h4>Step 2: UCA Analysis</h4>
<ul>
<li>Identify unsafe control actions</li>
<li>Analyze timing, sequence, and context</li>
<li>Link UCAs to hazards</li>
</ul>

<h4>Step 3: Loss Scenario Analysis</h4>
<ul>
<li>Develop causal scenarios for each UCA</li>
<li>Analyze process model flaws</li>
<li>Identify contributing factors</li>
</ul>

<h3>🎯 Key Benefits</h3>
<ul>
<li>Handles complex system interactions</li>
<li>Considers human factors and software</li>
<li>Proactive rather than reactive analysis</li>
<li>Systematic and thorough approach</li>
</ul>
                """,
                "keywords": ["stpa", "methodology", "process", "steps", "hazard", "analysis"]
            },
            
            "keyboard_shortcuts": {
                "title": "Keyboard Shortcuts & Tips",
                "content": """
<h2>Keyboard Shortcuts & Quick Tips</h2>

<h3>⌨️ Essential Shortcuts</h3>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tr><th>Action</th><th>Shortcut</th><th>Description</th></tr>
<tr><td>Undo</td><td><kbd>Ctrl+Z</kbd></td><td>Undo last operation</td></tr>
<tr><td>Redo</td><td><kbd>Ctrl+Y</kbd></td><td>Redo next operation</td></tr>
<tr><td>New Project</td><td><kbd>Ctrl+N</kbd></td><td>Create new analysis</td></tr>
<tr><td>Save</td><td><kbd>Ctrl+S</kbd></td><td>Save current project</td></tr>
<tr><td>Open</td><td><kbd>Ctrl+O</kbd></td><td>Load existing project</td></tr>
<tr><td>Quick Connect</td><td><kbd>C + Mouse</kbd></td><td>Hold C over source, move to target</td></tr>
<tr><td>Confirm Edit</td><td><kbd>Enter</kbd></td><td>Save inline text changes</td></tr>
<tr><td>Cancel Edit</td><td><kbd>Escape</kbd></td><td>Cancel inline editing</td></tr>
<tr><td>Send Chat</td><td><kbd>Ctrl+Enter</kbd></td><td>Send message to AI assistant</td></tr>
</table>

<h3>🎯 Workflow Tips</h3>
<ul>
<li><strong>Start in Add Node Mode</strong>: Create all nodes first, then connect them</li>
<li><strong>Use C-Key Method</strong>: Faster than switching to Connect mode</li>
<li><strong>Edit as You Go</strong>: Click text immediately after creation to rename</li>
<li><strong>Properties Later</strong>: Use properties panel for detailed attributes</li>
<li><strong>Save Frequently</strong>: Use Ctrl+S to preserve your work</li>
</ul>

<h3>🔧 Professional Features</h3>
<ul>
<li><strong>Multiple Edges</strong>: Create several connections between same nodes</li>
<li><strong>Node Shapes</strong>: Use circles for processes, rectangles for controllers</li>
<li><strong>State Machines</strong>: Define dynamic behavior in properties</li>
<li><strong>Export Options</strong>: Save as JSON for sharing and backup</li>
</ul>
                """,
                "keywords": ["shortcuts", "keyboard", "tips", "quick", "reference"]
            },
            
            "troubleshooting": {
                "title": "Troubleshooting & Common Issues",
                "content": """
<h2>Troubleshooting Guide</h2>

<h3>🐛 Common Issues & Solutions</h3>

<h4>Text Editor Won't Close</h4>
<p><strong>Problem</strong>: Inline text editor remains open after editing</p>
<p><strong>Solution</strong>: Press <kbd>Escape</kbd> or click elsewhere to close the editor</p>

<h4>Undo/Redo Not Working</h4>
<p><strong>Problem</strong>: Undo button is grayed out</p>
<p><strong>Solution</strong>: Check if there are operations in history - buttons auto-disable when no operations available</p>

<h4>Properties Not Updating</h4>
<p><strong>Problem</strong>: Changes in properties panel not visible</p>
<p><strong>Solution</strong>: Properties refresh automatically after undo/redo operations</p>

<h4>Node Movement Issues</h4>
<p><strong>Problem</strong>: Can't move nodes or they jump unexpectedly</p>
<p><strong>Solution</strong>: Ensure you're in Add Node or Move mode - nodes can be dragged in both modes</p>

<h4>Multiple Edges Overlap</h4>
<p><strong>Problem</strong>: Multiple edges between same nodes appear on top of each other</p>
<p><strong>Solution</strong>: This is automatically handled - edges should curve to avoid overlap</p>

<h3>⚡ Performance Tips</h3>
<ul>
<li><strong>Large Graphs</strong>: For 100+ nodes, use Auto Layout for initial positioning</li>
<li><strong>Memory Management</strong>: Close and reopen the app for very long sessions</li>
<li><strong>File Size</strong>: Large projects may take longer to save/load</li>
</ul>

<h3>💾 Data Safety</h3>
<ul>
<li><strong>Auto-Save</strong>: No auto-save feature - remember to use Ctrl+S</li>
<li><strong>Backups</strong>: Keep multiple versions of important analyses</li>
<li><strong>File Format</strong>: JSON files are human-readable and recoverable</li>
</ul>

<h3>🆘 Getting More Help</h3>
<ul>
<li>Ask the AI assistant specific questions about your analysis</li>
<li>Check the methodology guides in this help system</li>
<li>Review example projects in the data folder</li>
</ul>
                """,
                "keywords": ["troubleshooting", "problems", "issues", "fixes", "help", "error"]
            }
        }
    
    def get_help_for_context(self, context: str) -> Dict:
        """Get help content for a specific context."""
        if context in self.content_cache:
            return self.content_cache[context]
        
        # Try to find by keyword match
        for key, content in self.content_cache.items():
            if any(keyword in context.lower() for keyword in content.get("keywords", [])):
                return content
        
        # Default to getting started
        return self.content_cache["getting_started"]
    
    def search_content(self, query: str) -> List[Dict]:
        """Search help content for a query."""
        results = []
        query_lower = query.lower()
        
        for key, content in self.content_cache.items():
            # Check title
            if query_lower in content["title"].lower():
                results.append({"key": key, "content": content, "match_type": "title"})
                continue
            
            # Check keywords
            if any(query_lower in keyword for keyword in content.get("keywords", [])):
                results.append({"key": key, "content": content, "match_type": "keyword"})
                continue
            
            # Check content (simple text search)
            if query_lower in content["content"].lower():
                results.append({"key": key, "content": content, "match_type": "content"})
        
        return results


class HelpSearchWidget(QWidget):
    """Search widget for the help system."""
    
    search_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search help content...")
        self.search_input.returnPressed.connect(self._on_search)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)
        
        layout.addWidget(QLabel("Search:"))
        layout.addWidget(self.search_input)
        layout.addWidget(search_btn)
        layout.setContentsMargins(5, 5, 5, 5)
    
    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)


class HelpBrowser(QTextBrowser):
    """Enhanced text browser for displaying help content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # Set up fonts and styling
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)
        
        # Enable HTML and links
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)
        
        # Set initial content
        self.display_welcome()
    
    def display_welcome(self):
        """Display welcome message."""
        html = """
        <h2>🆘 Eir Help System</h2>
        <p>Welcome to the integrated help system! Here you can find:</p>
        <ul>
        <li><strong>Getting Started</strong>: Quick introduction to the tool</li>
        <li><strong>Methodology Guides</strong>: STPA process and best practices</li>
        <li><strong>Feature Documentation</strong>: Detailed feature explanations</li>
        <li><strong>Troubleshooting</strong>: Solutions to common issues</li>
        </ul>
        
        <h3>🔍 How to Use This Help</h3>
        <ul>
        <li>Browse topics in the list on the left</li>
        <li>Use the search box to find specific information</li>
        <li>Content updates based on what you're working on</li>
        <li>Click on any topic to get detailed information</li>
        </ul>
        
        <p><em>💡 Tip: The help content is context-sensitive - it will show relevant information based on which tab you're currently using!</em></p>
        """
        self.setHtml(html)
    
    def display_content(self, content: Dict):
        """Display help content."""
        if content:
            html = f"<h1>{content['title']}</h1>{content['content']}"
            self.setHtml(html)
        else:
            self.display_welcome()


class HelpTopicList(QListWidget):
    """List widget showing available help topics."""
    
    topic_selected = Signal(str)
    
    def __init__(self, content_manager: HelpContentManager, parent=None):
        super().__init__(parent)
        self.content_manager = content_manager
        self._setup_topics()
        self.itemClicked.connect(self._on_topic_clicked)
    
    def _setup_topics(self):
        """Setup the topic list."""
        topics = [
            ("getting_started", "🚀 Getting Started"),
            ("system_description", "📄 System Description & Documents"),
            ("stpa_methodology", "📚 STPA Methodology"),
            ("control_structure", "🎯 Control Structure Editor"),
            ("uca_analysis", "⚠️ UCA Analysis"),
            ("keyboard_shortcuts", "⌨️ Keyboard Shortcuts"),
            ("troubleshooting", "🐛 Troubleshooting")
        ]
        
        for key, title in topics:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, key)
            self.addItem(item)
    
    def _on_topic_clicked(self, item: QListWidgetItem):
        key = item.data(Qt.UserRole)
        if key:
            self.topic_selected.emit(key)


class HelpPanel(QDockWidget):
    """Main help panel widget."""
    
    def __init__(self, parent=None):
        super().__init__("STPA Help", parent)
        self.content_manager = HelpContentManager()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        # Layout
        layout = QVBoxLayout(main_widget)
        
        # Search widget
        self.search_widget = HelpSearchWidget()
        layout.addWidget(self.search_widget)
        
        # Splitter for topics and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Topic list
        self.topic_list = HelpTopicList(self.content_manager)
        self.topic_list.setMaximumWidth(200)
        splitter.addWidget(self.topic_list)
        
        # Content browser
        self.help_browser = HelpBrowser()
        splitter.addWidget(self.help_browser)
        
        # Set splitter proportions
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)
        
        # Set dock properties
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.topic_list.topic_selected.connect(self._show_topic)
        self.search_widget.search_requested.connect(self._perform_search)
    
    def _show_topic(self, topic_key: str):
        """Show a specific help topic."""
        content = self.content_manager.get_help_for_context(topic_key)
        self.help_browser.display_content(content)
    
    def _perform_search(self, query: str):
        """Perform a search and display results."""
        results = self.content_manager.search_content(query)
        
        if not results:
            html = f"<h2>Search Results for '{query}'</h2><p>No results found.</p>"
            self.help_browser.setHtml(html)
            return
        
        # Display search results
        html = f"<h2>Search Results for '{query}'</h2>"
        for result in results[:10]:  # Limit to top 10 results
            content = result["content"]
            match_type = result["match_type"]
            html += f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                <h3>{content['title']}</h3>
                <p><em>Match type: {match_type}</em></p>
                <p>{self._get_content_preview(content['content'], query)}</p>
            </div>
            """
        
        self.help_browser.setHtml(html)
    
    def _get_content_preview(self, content: str, query: str) -> str:
        """Get a preview of content around the search term."""
        # Simple preview - find query in content and show surrounding text
        content_text = content.replace('<', '&lt;').replace('>', '&gt;')
        query_lower = query.lower()
        content_lower = content_text.lower()
        
        pos = content_lower.find(query_lower)
        if pos == -1:
            return content_text[:200] + "..." if len(content_text) > 200 else content_text
        
        start = max(0, pos - 100)
        end = min(len(content_text), pos + 100)
        preview = content_text[start:end]
        
        if start > 0:
            preview = "..." + preview
        if end < len(content_text):
            preview = preview + "..."
        
        return preview
    
    def show_contextual_help(self, context: str):
        """Show help for a specific context (e.g., current tab)."""
        content = self.content_manager.get_help_for_context(context)
        self.help_browser.display_content(content)
        
        # Highlight the relevant topic in the list
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            if item.data(Qt.UserRole) == context:
                self.topic_list.setCurrentItem(item)
                break
