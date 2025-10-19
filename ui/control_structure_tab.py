"""
Control Structure tab - Interactive graph editor.
"""

from typing import Dict, List, Optional, Tuple, Set
import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QSplitter, QTextEdit, QScrollArea,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, 
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QInputDialog, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QCheckBox, QToolBar,
    QFileDialog, QGraphicsProxyWidget, QApplication, QPlainTextEdit
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QLineF
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainter, QPolygonF, QPainterPath, QFont,
    QAction, QTransform, QCursor, QActionGroup
)

import networkx as nx

from core.models import STPAModel, SystemNode, ControlLink
from core.constants import (
    DEFAULT_NODE_SIZE, DEFAULT_EDGE_WEIGHT, NODE_SELECTION_COLOR, 
    NODE_SELECTION_WIDTH, EDGE_DEFAULT_WIDTH, FONT_SIZE_DEFAULT, 
    FONT_FAMILY_DEFAULT, MAX_UNDO_HISTORY, MIN_ZOOM_FACTOR, 
    MAX_ZOOM_FACTOR, DEFAULT_PADDING
)
from ui.shared_components import PropertiesPane, TabChatPanel


# Command Pattern for Undo/Redo
class Command(ABC):
    """Abstract base class for undoable commands"""
    
    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self):
        """Undo the command"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return a description of the command"""
        pass


class CommandManager:
    """Manages undo/redo operations using the command pattern"""
    
    def __init__(self, max_history: int = MAX_UNDO_HISTORY):
        self.max_history = max_history
        self.history: List[Command] = []
        self.current_index = -1
    
    def execute_command(self, command: Command):
        """Execute a command and add it to history"""
        command.execute()
        
        # Remove any commands after current index (when we're not at the end)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
        
        # Update UI if parent has the update method
        if hasattr(self, '_update_callback'):
            self._update_callback()
    
    def set_update_callback(self, callback):
        """Set a callback to be called after command execution"""
        self._update_callback = callback
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def undo(self):
        """Undo the last command"""
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            # Update UI if parent has the update method
            if hasattr(self, '_update_callback'):
                self._update_callback()
    
    def redo(self):
        """Redo the next command"""
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            # Update UI if parent has the update method
            if hasattr(self, '_update_callback'):
                self._update_callback()
    
    def clear(self):
        """Clear all command history"""
        self.history.clear()
        self.current_index = -1


class AddNodeCommand(Command):
    """Command to add a node"""
    
    def __init__(self, scene, position: QPointF, node_data: 'NodeData' = None):
        self.scene = scene
        self.position = position
        self.node_data = node_data or NodeData()
        self.node_item = None
        self.node_id = None
    
    def execute(self):
        self.node_item, self.node_id = self.scene._create_node_internal(self.position, self.node_data)
    
    def undo(self):
        if self.node_item:
            self.scene._delete_node_item_internal(self.node_item)
    
    def description(self) -> str:
        return f"Add Node '{self.node_data.name}'"


class DeleteNodeCommand(Command):
    """Command to delete a node"""
    
    def __init__(self, scene, node_item: 'NodeItem'):
        self.scene = scene
        self.node_item = node_item
        self.node_id = node_item.node_id
        self.node_data = node_item.data
        self.position = node_item.scenePos()
        self.connected_edges = []
    
    def execute(self):
        # Store connected edges for restoration
        self.connected_edges = []
        for edge in self.scene.iter_edges():
            if edge.src == self.node_item or edge.dst == self.node_item:
                edge_info = {
                    'src_id': edge.src.node_id,
                    'dst_id': edge.dst.node_id,
                    'data': edge.data,
                    'key': edge.edge_key
                }
                self.connected_edges.append(edge_info)
        
        self.scene._delete_node_item_internal(self.node_item)
    
    def undo(self):
        # Recreate the node
        self.node_item, _ = self.scene._create_node_internal(self.position, self.node_data, self.node_id)
        
        # Recreate connected edges
        for edge_info in self.connected_edges:
            src_node = self.scene._find_node_by_id(edge_info['src_id'])
            dst_node = self.scene._find_node_by_id(edge_info['dst_id'])
            if src_node and dst_node:
                self.scene._create_edge_internal(src_node, dst_node, edge_info['data'], edge_info['key'])
    
    def description(self) -> str:
        return f"Delete Node '{self.node_data.name}'"


class RenameNodeCommand(Command):
    """Command to rename a node"""
    
    def __init__(self, node_item: 'NodeItem', old_name: str, new_name: str):
        self.node_item = node_item
        self.old_name = old_name
        self.new_name = new_name
    
    def execute(self):
        self.node_item.data.name = self.new_name
        self.node_item.update()
    
    def undo(self):
        self.node_item.data.name = self.old_name
        self.node_item.update()
    
    def description(self) -> str:
        return f"Rename Node '{self.old_name}' to '{self.new_name}'"


class RenameEdgeCommand(Command):
    """Command to rename an edge"""
    
    def __init__(self, edge_item: 'EdgeItem', old_name: str, new_name: str):
        self.edge_item = edge_item
        self.old_name = old_name
        self.new_name = new_name
    
    def execute(self):
        self.edge_item.data.name = self.new_name
        self.edge_item.update()
    
    def undo(self):
        self.edge_item.data.name = self.old_name
        self.edge_item.update()
    
    def description(self) -> str:
        return f"Rename Edge '{self.old_name}' to '{self.new_name}'"


class AddEdgeCommand(Command):
    """Command to add an edge"""
    
    def __init__(self, scene, src_node: 'NodeItem', dst_node: 'NodeItem', edge_data: 'EdgeData' = None):
        self.scene = scene
        self.src_node = src_node
        self.dst_node = dst_node
        self.src_id = src_node.node_id
        self.dst_id = dst_node.node_id
        self.edge_data = edge_data
        self.edge_item = None
        self.edge_key = None
    
    def execute(self):
        if not self.edge_data:
            # Determine edge properties based on current mode
            if self.scene._edge_mode == 'undirected':
                undirected = True
                bidirectional = False
            elif self.scene._edge_mode == 'bidirectional':
                undirected = False
                bidirectional = True
            else:  # directed
                undirected = False
                bidirectional = False
            
            # Find next available key
            if self.scene.G.has_edge(self.src_id, self.dst_id):
                existing = list(self.scene.G[self.src_id][self.dst_id].keys())
                next_key = (max(existing) + 1) if existing else 0
            else:
                next_key = 0
            
            self.edge_key = next_key
            self.edge_data = EdgeData(
                name=f"e{self.src_id}_{self.dst_id}_{next_key}",
                weight=1.0,
                undirected=undirected,
                bidirectional=bidirectional
            )
        
        self.edge_item = self.scene._create_edge_internal(
            self.src_node, self.dst_node, self.edge_data, self.edge_key
        )
    
    def undo(self):
        if self.edge_item:
            self.scene._delete_edge_item_internal(self.edge_item)
    
    def description(self) -> str:
        return f"Add Edge '{self.edge_data.name if self.edge_data else 'edge'}'"


class DeleteEdgeCommand(Command):
    """Command to delete an edge"""
    
    def __init__(self, scene, edge_item: 'EdgeItem'):
        self.scene = scene
        self.edge_item = edge_item
        self.src_id = edge_item.src.node_id
        self.dst_id = edge_item.dst.node_id
        self.edge_data = edge_item.data
        self.edge_key = edge_item.edge_key
        self.src_node = None
        self.dst_node = None
    
    def execute(self):
        # Store references to nodes before deletion
        self.src_node = self.edge_item.src
        self.dst_node = self.edge_item.dst
        self.scene._delete_edge_item_internal(self.edge_item)
    
    def undo(self):
        # Find the nodes again (they should still exist)
        src_node = self.scene._find_node_by_id(self.src_id)
        dst_node = self.scene._find_node_by_id(self.dst_id)
        
        if src_node and dst_node:
            self.edge_item = self.scene._create_edge_internal(
                src_node, dst_node, self.edge_data, self.edge_key
            )
    
    def description(self) -> str:
        return f"Delete Edge '{self.edge_data.name}'"


class ChangeNodePropertyCommand(Command):
    """Command to change a node property"""
    
    def __init__(self, scene, node_item: 'NodeItem', property_name: str, old_value, new_value):
        self.scene = scene
        self.node_item = node_item
        self.node_id = node_item.node_id
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        self._apply_property(self.new_value)
    
    def undo(self):
        self._apply_property(self.old_value)
    
    def _apply_property(self, value):
        """Apply the property change"""
        if self.property_name == 'name':
            self.node_item.data.name = str(value)
            self.scene.G.nodes[self.node_id]['name'] = str(value)
            self.node_item.update_text_rect()
            self.node_item.update()
        elif self.property_name == 'states':
            self.node_item.data.states = list(value) if isinstance(value, (list, tuple)) else [str(value)]
            self.scene.G.nodes[self.node_id]['states'] = self.node_item.data.states
        elif self.property_name == 'shape':
            self.node_item.data.shape = str(value)
            self.scene.G.nodes[self.node_id]['shape'] = str(value)
            self.node_item.update()
        elif self.property_name == 'size':
            try:
                self.node_item.data.size = float(value)
                self.scene.G.nodes[self.node_id]['size'] = float(value)
                self.node_item._rect = QRectF(-self.node_item.data.size, -self.node_item.data.size, 
                                            2*self.node_item.data.size, 2*self.node_item.data.size)
                self.node_item.update()
            except (ValueError, TypeError):
                pass
        elif self.property_name == 'node_type':
            self.scene.G.nodes[self.node_id]['node_type'] = value
        elif self.property_name == 'description':
            self.scene.G.nodes[self.node_id]['description'] = value
    
    def description(self) -> str:
        return f"Change Node '{self.node_item.data.name}' {self.property_name}: {self.old_value} → {self.new_value}"


class ChangeEdgePropertyCommand(Command):
    """Command to change an edge property"""
    
    def __init__(self, scene, edge_item: 'EdgeItem', property_name: str, old_value, new_value):
        self.scene = scene
        self.edge_item = edge_item
        self.src_id = edge_item.src.node_id
        self.dst_id = edge_item.dst.node_id
        self.edge_key = edge_item.edge_key
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        self._apply_property(self.new_value)
    
    def undo(self):
        self._apply_property(self.old_value)
    
    def _apply_property(self, value):
        """Apply the property change"""
        if self.property_name == 'label':
            self.edge_item.data.name = str(value)
            self.scene.G[self.src_id][self.dst_id][self.edge_key]['name'] = str(value)
        elif self.property_name == 'link_type':
            self.scene.G[self.src_id][self.dst_id][self.edge_key]['link_type'] = value
        elif self.property_name == 'description':
            self.scene.G[self.src_id][self.dst_id][self.edge_key]['description'] = value
        elif self.property_name == 'undirected':
            self.edge_item.data.undirected = bool(value)
            self.scene.G[self.src_id][self.dst_id][self.edge_key]['undirected'] = bool(value)
            self.edge_item.update_path()
        elif self.property_name == 'bidirectional':
            self.edge_item.data.bidirectional = bool(value)
            self.scene.G[self.src_id][self.dst_id][self.edge_key]['bidirectional'] = bool(value)
            self.edge_item.update_path()
        elif self.property_name == 'weight':
            try:
                self.edge_item.data.weight = float(value)
                self.scene.G[self.src_id][self.dst_id][self.edge_key]['weight'] = float(value)
            except (ValueError, TypeError):
                pass
    
    def description(self) -> str:
        return f"Change Edge '{self.edge_item.data.name}' {self.property_name}: {self.old_value} → {self.new_value}"


class MoveNodeCommand(Command):
    """Command to move a node"""
    
    def __init__(self, node_item: 'NodeItem', old_pos: QPointF, new_pos: QPointF):
        self.node_item = node_item
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        self.node_item.scene()._applying_command = True
        self.node_item.setPos(self.new_pos)
        self._update_graph_position(self.new_pos)
        self.node_item.scene()._applying_command = False
    
    def undo(self):
        self.node_item.scene()._applying_command = True
        self.node_item.setPos(self.old_pos)
        self._update_graph_position(self.old_pos)
        self.node_item.scene()._applying_command = False
    
    def _update_graph_position(self, pos: QPointF):
        """Update the position in the NetworkX graph"""
        scene = self.node_item.scene()
        if scene and hasattr(scene, 'G'):
            scene.G.nodes[self.node_item.node_id]['position'] = (pos.x(), pos.y())
    
    def description(self) -> str:
        return f"Move Node '{self.node_item.data.name}'"


class InlineTextEdit(QLineEdit):
    """Inline text editor for node/edge labels"""
    
    def __init__(self, initial_text: str = "", parent=None):
        super().__init__(initial_text, parent)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #4A90E2;
                border-radius: 4px;
                padding: 2px 4px;
                background-color: white;
                selection-background-color: #4A90E2;
                font-weight: bold;
            }
        """)
        self.selectAll()
        self.original_text = initial_text
    
    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key_Escape:
            # Cancel editing - restore original text
            self.setText(self.original_text)
            self.editingFinished.emit()
            event.accept()
            return
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Finish editing
            self.editingFinished.emit()
            event.accept()
            return
        
        super().keyPressEvent(event)


# Data classes for node and edge information
@dataclass
class NodeData:
    name: str = "Node"
    states: List[str] = field(default_factory=list)
    shape: str = "circle"  # "circle", "rectangle", "hexagon"
    size: float = DEFAULT_NODE_SIZE     # radius for circle, half-width/height for others

@dataclass
class EdgeData:
    name: str = "Edge"
    weight: float = DEFAULT_EDGE_WEIGHT
    undirected: bool = False  # if True, drawn without arrowheads
    bidirectional: bool = False  # if True, represents both A->B and B->A as single edge

# Visual constants
NODE_RADIUS = DEFAULT_NODE_SIZE  # For backward compatibility


class NodeItem(QGraphicsItem):
    def __init__(self, node_id: int, data: NodeData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_id = node_id
        self.data = data
        self.text_editor = None
        self._editing = False
        
        self.setFlags(QGraphicsItem.ItemIsSelectable | 
                     QGraphicsItem.ItemIsMovable | 
                     QGraphicsItem.ItemSendsGeometryChanges)
        
        # Visual appearance will be painted in paint()
        self._rect = QRectF(-data.size, -data.size, 2*data.size, 2*data.size)
        
        # Text rect for click detection
        font = QFont(FONT_FAMILY_DEFAULT, FONT_SIZE_DEFAULT, QFont.Bold)
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(self.data.name)
        self._text_rect = QRectF(-text_rect.width()/2, -text_rect.height()/2,
                                text_rect.width(), text_rect.height())
        
    def boundingRect(self) -> QRectF:
        return self._rect.adjusted(-2, -2, 2, 2)  # Add small margin for pen
        
    def paint(self, painter: QPainter, option, widget=None):
        # Draw based on shape
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set colors
        if self.isSelected():
            pen = QPen(QColor(NODE_SELECTION_COLOR), NODE_SELECTION_WIDTH)  # Red when selected
            brush = QBrush(QColor(255, 200, 200))  # Light red fill
        else:
            pen = QPen(QColor(0, 0, 139), 2)  # Dark blue
            brush = QBrush(QColor(173, 216, 230))  # Light blue fill
            
        painter.setPen(pen)
        painter.setBrush(brush)
        
        if self.data.shape == "circle":
            painter.drawEllipse(self._rect)
        elif self.data.shape == "rectangle":
            painter.drawRect(self._rect)
        elif self.data.shape == "hexagon":
            # Draw hexagon
            size = self.data.size
            hexagon = QPolygonF([
                QPointF(size, 0),
                QPointF(size/2, size * 0.866),
                QPointF(-size/2, size * 0.866),
                QPointF(-size, 0),
                QPointF(-size/2, -size * 0.866),
                QPointF(size/2, -size * 0.866)
            ])
            painter.drawPolygon(hexagon)
        
        # Draw text (only if not editing)
        if not self._editing:
            painter.setPen(QPen(Qt.black))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(self._rect, Qt.AlignCenter, self.data.name)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Store start position for move command
            self._drag_start_pos = self.scenePos()
            
            # Check if click is on text area for inline editing
            local_pos = event.pos()
            if self._text_rect.contains(local_pos) and not self._editing:
                self.start_inline_edit()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, '_drag_start_pos'):
            # Create move command only at the end of drag if position changed significantly
            old_pos = self._drag_start_pos
            new_pos = self.scenePos()
            
            if (abs(new_pos.x() - old_pos.x()) > 1 or abs(new_pos.y() - old_pos.y()) > 1):
                # Don't create move commands during undo/redo operations
                if not getattr(self.scene(), '_applying_command', False):
                    command = MoveNodeCommand(self, old_pos, new_pos)
                    if hasattr(self.scene(), 'command_manager'):
                        self.scene().command_manager.execute_command(command)
            
            delattr(self, '_drag_start_pos')
        
        super().mouseReleaseEvent(event)
    
    def start_inline_edit(self):
        """Start inline text editing"""
        if self._editing:
            return
            
        self._editing = True
        scene = self.scene()
        if not scene:
            return
            
        # Create text editor
        self.text_editor = InlineTextEdit(self.data.name)
        self.text_proxy = QGraphicsProxyWidget(self)
        self.text_proxy.setWidget(self.text_editor)
        
        # Position the editor over the text
        editor_rect = self.text_editor.sizeHint()
        self.text_proxy.setPos(-editor_rect.width()/2, -editor_rect.height()/2)
        
        # Connect signals
        self.text_editor.editingFinished.connect(self.finish_inline_edit)
        self.text_editor.returnPressed.connect(self.finish_inline_edit)
        
        # Handle focus loss by connecting to focus out event
        self.text_editor.focusOutEvent = self._on_editor_focus_out
        
        # Focus and select all
        self.text_editor.setFocus()
        self.text_editor.selectAll()
        
        self.update()
    
    def _on_editor_focus_out(self, event):
        """Handle when the editor loses focus"""
        # Call the original focusOutEvent first
        InlineTextEdit.focusOutEvent(self.text_editor, event)
        # Then finish editing
        self.finish_inline_edit()
    
    def finish_inline_edit(self):
        """Finish inline text editing"""
        if not self._editing or not self.text_editor:
            return
        
        # Prevent multiple calls
        self._editing = False
            
        new_name = self.text_editor.text().strip()
        if new_name and new_name != self.data.name:
            # Create rename command
            old_name = self.data.name
            command = RenameNodeCommand(self, old_name, new_name)
            if hasattr(self.scene(), 'command_manager'):
                self.scene().command_manager.execute_command(command)
            else:
                # Fallback: direct rename
                self.data.name = new_name
        
        # Disconnect signals to prevent issues
        try:
            self.text_editor.editingFinished.disconnect()
            self.text_editor.returnPressed.disconnect()
        except:
            pass
        
        # Clean up proxy widget
        if hasattr(self, 'text_proxy') and self.text_proxy:
            self.text_proxy.hide()
            self.text_proxy.deleteLater()
            self.text_proxy = None
        
        self.text_editor = None
        self.update()
        
        # Update text rect
        self.update_text_rect()
    
    def update_text_rect(self):
        """Update the text rectangle after name changes"""
        font = QFont("Arial", 10, QFont.Bold)
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(self.data.name)
        self._text_rect = QRectF(-text_rect.width()/2, -text_rect.height()/2,
                                text_rect.width(), text_rect.height())
    
    def itemChange(self, change, value):
        # Update connected edges when position changes
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Update connected edges
            for item in self.scene().items():
                if isinstance(item, EdgeItem):
                    if item.src == self or item.dst == self:
                        item.update_path()
        
        return super().itemChange(change, value)
    
    def mouseDoubleClickEvent(self, event):
        """Double-click to rename node"""
        if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), '_rename_node'):
            self.scene().parent()._rename_node(self)
        super().mouseDoubleClickEvent(event)


class EdgeItem(QGraphicsPathItem):
    def __init__(self, src: NodeItem, dst: NodeItem, data: EdgeData, edge_key: int = 0, curve_offset: float = 0.0):
        super().__init__()
        self.src = src
        self.dst = dst
        self.data = data
        self.edge_key = edge_key
        self.curve_offset = curve_offset
        self.text_editor = None
        self._editing = False
        
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)  # Behind nodes
        
        self.update_path()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if click is near the label area for inline editing
            if self._is_click_on_label(event.pos()):
                self.start_inline_edit()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def _is_click_on_label(self, pos: QPointF) -> bool:
        """Check if click position is on the edge label"""
        if not self.src or not self.dst:
            return False
        
        # Get midpoint of edge for label position
        start_pos = self.src.scenePos()
        end_pos = self.dst.scenePos()
        mid_pos = QPointF((start_pos.x() + end_pos.x()) / 2, (start_pos.y() + end_pos.y()) / 2)
        
        # Convert to item coordinates
        scene_click = self.scenePos() + pos
        distance = math.hypot(scene_click.x() - mid_pos.x(), scene_click.y() - mid_pos.y())
        
        # Allow clicks within 20 pixels of the midpoint
        return distance <= 20
    
    def start_inline_edit(self):
        """Start inline text editing"""
        if self._editing:
            return
            
        self._editing = True
        scene = self.scene()
        if not scene:
            return
            
        # Get midpoint for editor position
        start_pos = self.src.scenePos()
        end_pos = self.dst.scenePos()
        mid_pos = QPointF((start_pos.x() + end_pos.x()) / 2, (start_pos.y() + end_pos.y()) / 2)
        
        # Create text editor
        self.text_editor = InlineTextEdit(self.data.name)
        self.text_proxy = QGraphicsProxyWidget()
        self.text_proxy.setWidget(self.text_editor)
        scene.addItem(self.text_proxy)
        
        # Position the editor at the midpoint
        editor_rect = self.text_editor.sizeHint()
        self.text_proxy.setPos(mid_pos.x() - editor_rect.width()/2, 
                              mid_pos.y() - editor_rect.height()/2)
        
        # Connect signals
        self.text_editor.editingFinished.connect(self.finish_inline_edit)
        self.text_editor.returnPressed.connect(self.finish_inline_edit)
        
        # Handle focus loss
        self.text_editor.focusOutEvent = self._on_editor_focus_out
        
        # Focus and select all
        self.text_editor.setFocus()
        self.text_editor.selectAll()
    
    def _on_editor_focus_out(self, event):
        """Handle when the editor loses focus"""
        # Call the original focusOutEvent first
        InlineTextEdit.focusOutEvent(self.text_editor, event)
        # Then finish editing
        self.finish_inline_edit()
    
    def finish_inline_edit(self):
        """Finish inline text editing"""
        if not self._editing or not self.text_editor:
            return
        
        # Prevent multiple calls
        self._editing = False
            
        new_name = self.text_editor.text().strip()
        if new_name and new_name != self.data.name:
            # Create rename command
            old_name = self.data.name
            command = RenameEdgeCommand(self, old_name, new_name)
            if hasattr(self.scene(), 'command_manager'):
                self.scene().command_manager.execute_command(command)
            else:
                # Fallback: direct rename
                self.data.name = new_name
        
        # Disconnect signals
        try:
            self.text_editor.editingFinished.disconnect()
            self.text_editor.returnPressed.disconnect()
        except:
            pass
        
        # Clean up proxy widget
        if hasattr(self, 'text_proxy') and self.text_proxy:
            if self.scene():
                self.scene().removeItem(self.text_proxy)
            self.text_proxy.hide()
            self.text_proxy.deleteLater()
            self.text_proxy = None
        
        self.text_editor = None
    
    def update_path(self):
        """Update the edge path based on current node positions"""
        if not self.src or not self.dst:
            return
            
        p1 = self.src.scenePos()
        p2 = self.dst.scenePos()
        v = p2 - p1
        dist = math.hypot(v.x(), v.y()) or 1e-9
        ux, uy = v.x()/dist, v.y()/dist

        node_size = self.src.data.size
        start = QPointF(p1.x() + ux*node_size, p1.y() + uy*node_size)
        end = QPointF(p2.x() - ux*node_size, p2.y() - uy*node_size)
        
        path = QPainterPath()
        path.moveTo(start)
        
        if abs(self.curve_offset) < 0.1:
            # Straight line
            path.lineTo(end)
        else:
            # Curved line - use consistent perpendicular direction
            mid = QPointF((start.x()+end.x())/2.0, (start.y()+end.y())/2.0)
            
            # Use CONSISTENT perpendicular direction for all edges between same node pair
            # Base it on the canonical direction (lower ID → higher ID)
            node1, node2 = self.src.node_id, self.dst.node_id
            if min(node1, node2) == node1 and max(node1, node2) == node2:
                # Use forward direction for perpendicular calculation
                canonical_ux, canonical_uy = ux, uy
            else:
                # Use reverse direction for perpendicular calculation  
                canonical_ux, canonical_uy = -ux, -uy
            
            # Consistent perpendicular (always 90° CCW from canonical direction)
            nx_, ny_ = -canonical_uy, canonical_ux
                
            ctrl = QPointF(mid.x() + nx_*self.curve_offset, mid.y() + ny_*self.curve_offset)
            path.quadTo(ctrl, end)
        
        # Add arrowhead if not undirected
        if not self.data.undirected:
            self._add_arrowhead(path, end.x(), end.y(), ux, uy)
            
        # Add reverse arrowhead if bidirectional
        if self.data.bidirectional:
            self._add_arrowhead(path, start.x(), start.y(), -ux, -uy)
        
        self.setPath(path)
        
        # Set colors
        if self.isSelected():
            self.setPen(QPen(QColor(255, 0, 0), 2))  # Red when selected
        else:
            self.setPen(QPen(QColor(100, 100, 100), 2))  # Gray
    
    def _add_arrowhead(self, path: QPainterPath, tip_x: float, tip_y: float, ux: float, uy: float):
        """Add arrowhead to the path"""
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30 degrees
        
        # Calculate arrowhead points
        base_angle = math.atan2(uy, ux)
        arrow_x1 = tip_x - arrow_length * math.cos(base_angle - arrow_angle)
        arrow_y1 = tip_y - arrow_length * math.sin(base_angle - arrow_angle)
        arrow_x2 = tip_x - arrow_length * math.cos(base_angle + arrow_angle)
        arrow_y2 = tip_y - arrow_length * math.sin(base_angle + arrow_angle)
        
        # Add arrowhead lines
        path.moveTo(tip_x, tip_y)
        path.lineTo(arrow_x1, arrow_y1)
        path.moveTo(tip_x, tip_y)
        path.lineTo(arrow_x2, arrow_y2)
    
    def mouseDoubleClickEvent(self, event):
        """Double-click to rename edge"""
        if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), '_rename_edge'):
            self.scene().parent()._rename_edge(self)
        super().mouseDoubleClickEvent(event)


class GraphScene(QGraphicsScene):
    """Enhanced scene with full interaction modes"""
    
    def __init__(self, graph: nx.MultiDiGraph, parent=None):
        super().__init__(parent)
        self.G = graph
        
        # Command manager for undo/redo
        self.command_manager = CommandManager()
        
        # Flag to prevent command recursion
        self._applying_command = False
        
        # Interaction modes
        self._adding_node = False
        self._connecting = False
        self._deleting = False
        self._c_key_held = False
        
        # Edge creation mode
        self._edge_mode = 'directed'  # 'directed', 'undirected', 'bidirectional'
        
        # Temporary graphics for previews
        self._temp_line: Optional[QGraphicsPathItem] = None
        self._connect_start_node: Optional[NodeItem] = None
    
    def iter_nodes(self):
        """Iterate over all NodeItem objects in the scene"""
        for item in self.items():
            if isinstance(item, NodeItem):
                yield item
    
    def iter_edges(self):
        """Iterate over all EdgeItem objects in the scene"""
        for item in self.items():
            if isinstance(item, EdgeItem):
                yield item
    
    def _as_node(self, item) -> Optional[NodeItem]:
        """Convert item to NodeItem if it is one"""
        return item if isinstance(item, NodeItem) else None
    
    def _node_under_mouse(self) -> Optional[NodeItem]:
        """Get node under current mouse position"""
        if not self.views():
            return None
        view = self.views()[0]
        mouse_pos = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
        item = self.itemAt(mouse_pos, view.transform())
        return self._as_node(item)
    
    # Public API for toolbar interactions
    def set_adding_node(self, enabled: bool):
        self._adding_node = enabled
        if enabled:
            self._connecting = False
            self._deleting = False
            self._set_nodes_movable(False)
        else:
            self._set_nodes_movable(True)
    
    def set_connecting(self, enabled: bool):
        self._connecting = enabled
        if enabled:
            self._adding_node = False
            self._deleting = False
            self._set_nodes_movable(False)
        else:
            self._set_nodes_movable(True)
    
    def set_deleting(self, enabled: bool):
        self._deleting = enabled
        if enabled:
            self._adding_node = False
            self._connecting = False
            self._set_nodes_movable(False)
        else:
            self._set_nodes_movable(True)
    
    def set_edge_mode(self, mode: str):
        """Set edge creation mode: 'directed', 'undirected', 'bidirectional'"""
        self._edge_mode = mode
    
    def _set_nodes_movable(self, enabled: bool):
        """Enable/disable node movement"""
        for node in self.iter_nodes():
            flags = QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges
            if enabled:
                flags |= QGraphicsItem.ItemIsMovable
            node.setFlags(flags)
    
    # Event handling
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and not self._c_key_held:
            self._c_key_held = True
            # Prevent accidental drags during C-key connection
            if not self._adding_node and not self._connecting:
                self._set_nodes_movable(False)
            # Start connection preview if over a node
            start = self._node_under_mouse()
            if start is not None:
                self._connect_start_node = start
                view = self.views()[0] if self.views() else None
                if view is not None:
                    scene_pos = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
                    self._ensure_temp_line(start.scenePos(), scene_pos)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_C and self._c_key_held:
            # Complete connection on C release
            target = self._node_under_mouse()
            if (target is not None and self._connect_start_node is not None 
                and target is not self._connect_start_node):
                self._create_edge(self._connect_start_node, target)
            self._cleanup_temp()
            self._connect_start_node = None
            self._c_key_held = False
            # Restore movability
            if not self._adding_node and not self._connecting:
                self._set_nodes_movable(True)
        super().keyReleaseEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform() if view else QTransform())
            node = self._as_node(item)
            
            # Delete mode: click to delete
            if self._deleting:
                if isinstance(item, EdgeItem):
                    self._delete_edge_item(item)
                    event.accept()
                    return
                if node is not None:
                    self._delete_node_item(node)
                    event.accept()
                    return
                event.accept()
                return
            
            # C-key connection: click start node
            if node is not None and self._c_key_held:
                self._connect_start_node = node
                self._ensure_temp_line(node.scenePos(), event.scenePos())
                event.accept()
                return
            
            # Add Node mode: click empty space to add node, but allow dragging existing nodes
            if self._adding_node:
                if item is None:  # Clicked on empty space
                    self._close_any_inline_editors()
                    self._create_node(event.scenePos())
                    event.accept()
                    return
                elif isinstance(item, NodeItem):
                    # Allow dragging of existing nodes even in Add Node mode
                    item.setSelected(True)
                    if hasattr(self.parent(), '_show_properties_for_item'):
                        self.parent()._show_properties_for_item(item)
                    # Don't create node, let the drag operation proceed
                    super().mousePressEvent(event)
                    return
                elif isinstance(item, EdgeItem):
                    # Allow selection of edges
                    item.setSelected(True)
                    if hasattr(self.parent(), '_show_properties_for_item'):
                        self.parent()._show_properties_for_item(item)
                    event.accept()
                    return
            
            # Connect mode: click node to start connection
            if node is not None and self._connecting:
                self._connect_start_node = node
                self._ensure_temp_line(node.scenePos(), event.scenePos())
                event.accept()
                return
        
        elif event.button() == Qt.RightButton:
            # Right-click to show properties
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform() if view else QTransform())
            if isinstance(item, (NodeItem, EdgeItem)):
                item.setSelected(True)
                # Notify parent to show properties
                if hasattr(self.parent(), '_show_properties_for_item'):
                    self.parent()._show_properties_for_item(item)
                event.accept()
                return
        
        # Close any inline editors when clicking elsewhere
        if item is None:
            self._close_any_inline_editors()
        
        super().mousePressEvent(event)
    
    def _close_any_inline_editors(self):
        """Close any active inline editors"""
        for item in self.items():
            if isinstance(item, NodeItem) and item._editing:
                item.finish_inline_edit()
            elif isinstance(item, EdgeItem) and item._editing:
                item.finish_inline_edit()
    
    def mouseMoveEvent(self, event):
        # Handle connection preview during C-key hold
        if self._c_key_held:
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform() if view else QTransform())
            node = self._as_node(item)
            
            if node is not None:
                if self._connect_start_node is None:
                    self._connect_start_node = node
                    self._ensure_temp_line(node.scenePos(), event.scenePos())
                else:
                    self._ensure_temp_line(self._connect_start_node.scenePos(), node.scenePos())
            else:
                if self._connect_start_node is not None:
                    self._ensure_temp_line(self._connect_start_node.scenePos(), event.scenePos())
            event.accept()
            return
        
        # Handle normal connect mode preview
        if self._connect_start_node and self._connecting:
            self._ensure_temp_line(self._connect_start_node.scenePos(), event.scenePos())
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        # Complete connection in connect mode
        if (self._connect_start_node and event.button() == Qt.LeftButton 
            and (self._connecting or self._c_key_held)):
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform() if view else QTransform())
            target_node = self._as_node(item)
            if target_node is not None and target_node is not self._connect_start_node:
                self._create_edge(self._connect_start_node, target_node)
            self._cleanup_temp()
            self._connect_start_node = None
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    # Helper methods for temporary graphics
    def _ensure_temp_line(self, p1: QPointF, p2: QPointF):
        """Show temporary line during connection preview"""
        path = QPainterPath(p1)
        path.lineTo(p2)
        if self._temp_line is None:
            self._temp_line = QGraphicsPathItem()
            self._temp_line.setZValue(-2)
            self._temp_line.setPen(QPen(Qt.darkGray, 1, Qt.DashLine))
            self.addItem(self._temp_line)
        self._temp_line.setPath(path)
    
    def _cleanup_temp(self):
        """Remove temporary graphics"""
        if self._temp_line is not None:
            self.removeItem(self._temp_line)
            self._temp_line = None
    
    # Creation and deletion methods
    def _find_node_by_id(self, node_id: int) -> Optional[NodeItem]:
        """Find a node item by its ID"""
        for node in self.iter_nodes():
            if node.node_id == node_id:
                return node
        return None
    
    def _create_node_internal(self, pos: QPointF, data: NodeData, node_id: int = None) -> Tuple[NodeItem, int]:
        """Internal method to create a node (used by commands)"""
        if node_id is None:
            node_id = 0
            if len(self.G.nodes) > 0:
                try:
                    node_id = max(n for n in self.G.nodes if isinstance(n, int)) + 1
                except ValueError:
                    node_id = len(self.G.nodes)
        
        item = NodeItem(node_id=node_id, data=data)
        
        # Add to NetworkX graph first
        self.G.add_node(node_id, name=data.name, states=list(data.states), 
                       shape=data.shape, size=data.size, position=(pos.x(), pos.y()))
        
        # Add to scene and set position
        self.addItem(item)
        item.setPos(pos)
        
        return item, node_id
    
    def _delete_node_item_internal(self, node_item: NodeItem):
        """Internal method to delete a node (used by commands)"""
        node_id = node_item.node_id
        
        # Remove connected edges first
        edges_to_remove = []
        for edge in self.iter_edges():
            if edge.src == node_item or edge.dst == node_item:
                edges_to_remove.append(edge)
        
        for edge in edges_to_remove:
            self.removeItem(edge)
        
        # Remove from NetworkX graph
        if self.G.has_node(node_id):
            self.G.remove_node(node_id)
        
        # Remove from scene
        self.removeItem(node_item)
    
    def _create_edge_internal(self, src: NodeItem, dst: NodeItem, data: EdgeData, edge_key: int = None) -> EdgeItem:
        """Internal method to create an edge (used by commands)"""
        u, v = src.node_id, dst.node_id
        
        # Use provided key or find next available
        if edge_key is None:
            if self.G.has_edge(u, v):
                existing = list(self.G[u][v].keys())
                edge_key = (max(existing) + 1) if existing else 0
            else:
                edge_key = 0
        
        # Add to NetworkX graph
        self.G.add_edge(u, v, key=edge_key, name=data.name, weight=data.weight, 
                       undirected=data.undirected, bidirectional=data.bidirectional)
        
        # Create visual edge
        edge_item = EdgeItem(src, dst, data, edge_key)
        self.addItem(edge_item)
        
        # Reflow multi-edges
        self._reflow_all_edges_between_nodes(u, v)
        
        return edge_item
    
    def _delete_edge_item_internal(self, edge_item: EdgeItem):
        """Internal method to delete an edge (used by commands)"""
        src_id = edge_item.src.node_id
        dst_id = edge_item.dst.node_id
        edge_key = edge_item.edge_key
        
        # Remove from NetworkX graph
        if self.G.has_edge(src_id, dst_id, key=edge_key):
            self.G.remove_edge(src_id, dst_id, key=edge_key)
        
        # Remove from scene
        self.removeItem(edge_item)
        
        # Reflow remaining multi-edges between these nodes
        self._reflow_all_edges_between_nodes(src_id, dst_id)
    
    def _create_node(self, pos: QPointF):
        """Create a new node at the given position using command system"""
        data = NodeData(name=f"n{len(self.G.nodes)}")
        command = AddNodeCommand(self, pos, data)
        self.command_manager.execute_command(command)
    
    def _create_edge(self, src: NodeItem, dst: NodeItem):
        """Create a new edge between two nodes using command system"""
        command = AddEdgeCommand(self, src, dst)
        self.command_manager.execute_command(command)
    
    def _reflow_all_edges_between_nodes(self, u: int, v: int):
        """Reflow all edges between two nodes using symmetric spacing approach"""
        # Get ALL edges between these two nodes (both directions)
        items_uv = [it for it in self.items()
                   if isinstance(it, EdgeItem) and it.src.node_id == u and it.dst.node_id == v]
        items_vu = [it for it in self.items()
                   if isinstance(it, EdgeItem) and it.src.node_id == v and it.dst.node_id == u]
        
        # Collect ALL edges between these nodes and sort consistently
        all_edges = []
        
        # Add u->v edges first (consistent ordering)
        for edge in sorted(items_uv, key=lambda e: e.edge_key):
            all_edges.append(edge)
            
        # Add v->u edges second  
        for edge in sorted(items_vu, key=lambda e: e.edge_key):
            all_edges.append(edge)
        
        total_edges = len(all_edges)
        
        if total_edges == 0:
            return
        elif total_edges == 1:
            # Single edge: keep straight
            all_edges[0].curve_offset = 0.0
            all_edges[0].update_path()
            return
        
        # Multiple edges: space symmetrically around center
        base_spacing = 50.0  # Increased for more visible separation
        
        if total_edges % 2 == 1:
            # Odd number: one edge gets 0, others get ±base, ±2*base, etc.
            mid_index = total_edges // 2
            for i, edge in enumerate(all_edges):
                offset = (i - mid_index) * base_spacing
                edge.curve_offset = offset
                edge.update_path()
        else:
            # Even number: no edge gets 0, use ±0.5*base, ±1.5*base, etc.
            mid_point = (total_edges - 1) / 2.0
            for i, edge in enumerate(all_edges):
                offset = (i - mid_point) * base_spacing
                edge.curve_offset = offset
                edge.update_path()
    
    def _delete_node_item(self, node: NodeItem):
        """Delete a node and all its connected edges using command system"""
        command = DeleteNodeCommand(self, node)
        self.command_manager.execute_command(command)
    
    def _delete_edge_item(self, edge: EdgeItem):
        """Delete an edge using command system"""
        command = DeleteEdgeCommand(self, edge)
        self.command_manager.execute_command(command)
    
    def delete_selected(self):
        """Delete all selected items"""
        # Delete edges first, then nodes
        for item in list(self.selectedItems()):
            if isinstance(item, EdgeItem):
                self._delete_edge_item(item)
        for item in list(self.selectedItems()):
            if isinstance(item, NodeItem):
                self._delete_node_item(item)
    
    def _sync_node_to_graph(self, node: NodeItem):
        """Sync a node item's position back to the graph"""
        if node.node_id in self.G.nodes:
            pos = node.scenePos()
            self.G.nodes[node.node_id]['position'] = (pos.x(), pos.y())


class GraphView(QGraphicsView):
    """Enhanced graphics view with zoom support"""
    
    def __init__(self, scene: GraphScene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    
    def wheelEvent(self, event):
        """Handle zoom with Ctrl+wheel"""
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)


class ControlStructureTab(QWidget):
    """Full-featured control structure editor tab"""
    
    # Signals
    model_changed = Signal()
    
    def __init__(self, model: STPAModel, main_window=None):
        super().__init__()
        
        self.model = model
        self.main_window = main_window
        
        # Create NetworkX graph for this tab
        self.G = nx.MultiDiGraph()
        
        # Graphics components
        self.scene = GraphScene(self.G, self)
        self.view = GraphView(self.scene)
        
        # Set up command manager callback to update UI
        self.scene.command_manager.set_update_callback(self._on_command_executed)
        
        # Prevent scene auto-resizing that causes node jumping
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        
        # Removed last save paths - file I/O now handled by main window
        
        self._setup_ui()
        self._setup_toolbar()
        self._load_from_model()
        
        # Initialize undo/redo button states
        self._update_undo_redo_buttons()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QHBoxLayout(self)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side: Graph view with toolbar
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Toolbar will be added here
        self.toolbar = QToolBar()
        left_layout.addWidget(self.toolbar)
        
        # Graph view
        left_layout.addWidget(self.view)
        
        # Status info
        self.status_label = QLabel("Tip: Double-click items to rename. Hold C over a node, move to another, release C to create an edge.")
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_widget)
        
        # Right side: Properties and Chat
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Properties panel
        self.properties_panel = PropertiesPane(self)
        self.properties_panel.property_changed.connect(self._on_property_changed)
        right_layout.addWidget(self.properties_panel)
        
        # Chat panel
        self.chat_panel = TabChatPanel("Control Structure", self.model, self)
        right_layout.addWidget(self.chat_panel)
        
        # Set stretch factors
        right_layout.setStretchFactor(self.properties_panel, 2)  # Give more space to properties
        right_layout.setStretchFactor(self.chat_panel, 1)
        
        splitter.addWidget(right_widget)
        
        # Set stretch factors (60% graph, 40% properties+chat)
        splitter.setSizes([600, 400])
        
        # Connect signals
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
        # Set default interaction mode to Add Node
        self._set_interaction_mode('add_node')
    
    def _setup_toolbar(self):
        """Set up the full-featured toolbar"""
        # Removed file operations - now handled by main window toolbar
        
        # Undo/Redo operations
        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self.undo)
        
        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(self.redo)
        
        # Interaction modes (mutually exclusive)
        self.act_move = QAction("Move/Select", self)
        self.act_move.setCheckable(True)
        
        self.act_add_node = QAction("Add Node", self)
        self.act_add_node.setCheckable(True)
        self.act_add_node.setChecked(True)  # Make this the default
        
        self.act_connect = QAction("Add Edge", self)
        self.act_connect.setCheckable(True)
        
        self.act_delete = QAction("Delete", self)
        self.act_delete.setCheckable(True)
        
        # Group interaction modes
        mode_group = QActionGroup(self)
        for action in [self.act_move, self.act_add_node, self.act_connect, self.act_delete]:
            mode_group.addAction(action)
        
        # Edge type modes (mutually exclusive)
        self.act_directed = QAction("Directed →", self)
        self.act_directed.setCheckable(True)
        self.act_directed.setChecked(True)
        
        self.act_undirected = QAction("Undirected —", self)
        self.act_undirected.setCheckable(True)
        
        self.act_bidirectional = QAction("Bidirectional ↔", self)
        self.act_bidirectional.setCheckable(True)
        
        # Group edge modes
        edge_group = QActionGroup(self)
        for action in [self.act_directed, self.act_undirected, self.act_bidirectional]:
            edge_group.addAction(action)
        
        # Additional tools
        self.act_autolayout = QAction("Auto Layout", self)
        self.act_autolayout.triggered.connect(self.auto_layout)
        
        self.act_zoom_fit = QAction("Zoom to Fit", self)
        self.act_zoom_fit.triggered.connect(self.zoom_to_fit)
        
        # Connect mode change signals
        self.act_move.triggered.connect(lambda: self._set_interaction_mode('move'))
        self.act_add_node.triggered.connect(lambda: self._set_interaction_mode('add_node'))
        self.act_connect.triggered.connect(lambda: self._set_interaction_mode('connect'))
        self.act_delete.triggered.connect(lambda: self._set_interaction_mode('delete'))
        
        self.act_directed.triggered.connect(lambda: self.scene.set_edge_mode('directed'))
        self.act_undirected.triggered.connect(lambda: self.scene.set_edge_mode('undirected'))
        self.act_bidirectional.triggered.connect(lambda: self.scene.set_edge_mode('bidirectional'))
        
        # Add actions to toolbar
        # Removed file operations - handled by main window
        
        # Undo/Redo
        self.toolbar.addAction(self.act_undo)
        self.toolbar.addAction(self.act_redo)
        self.toolbar.addSeparator()
        
        # Interaction modes
        self.toolbar.addAction(self.act_move)
        self.toolbar.addAction(self.act_add_node)
        self.toolbar.addAction(self.act_connect)
        self.toolbar.addAction(self.act_delete)
        self.toolbar.addSeparator()
        
        # Edge modes
        self.toolbar.addAction(self.act_directed)
        self.toolbar.addAction(self.act_undirected)
        self.toolbar.addAction(self.act_bidirectional)
        self.toolbar.addSeparator()
        
        # Tools
        self.toolbar.addAction(self.act_autolayout)
        self.toolbar.addAction(self.act_zoom_fit)
    
    def _set_interaction_mode(self, mode: str):
        """Set the current interaction mode"""
        # Reset all modes
        self.scene.set_adding_node(False)
        self.scene.set_connecting(False)
        self.scene.set_deleting(False)
        
        # Set the requested mode
        if mode == 'add_node':
            self.scene.set_adding_node(True)
            self.status_label.setText("Add Node mode: Click empty space to add node")
        elif mode == 'connect':
            self.scene.set_connecting(True)
            self.status_label.setText("Connect mode: Click nodes to connect them")
        elif mode == 'delete':
            self.scene.set_deleting(True)
            self.status_label.setText("Delete mode: Click items to delete them")
        else:  # move
            self.status_label.setText("Tip: Double-click items to rename. Hold C over a node, move to another, release C to create an edge.")
    
    def set_model(self, model: STPAModel):
        """Set a new model and refresh the view"""
        self.model = model
        self._load_from_model()
        if self.main_window:
            self.main_window._update_window_title()
    
    def sync_to_model(self):
        """Update the model with current graph state"""
        # Sync node positions to graph
        for node in self.scene.iter_nodes():
            self.scene._sync_node_to_graph(node)
        
        # Update the STPA model's control structure
        self.model.control_structure.clear()
        
        # Add nodes to STPA model
        for node_id, data in self.G.nodes(data=True):
            # Remove 'id' from data to avoid conflict with node_id parameter
            node_data = {k: v for k, v in data.items() if k != 'id'}
            
            # Ensure 'name' field exists - required by add_node method
            if 'name' not in node_data:
                node_data['name'] = f"Node {node_id}"
            
            self.model.control_structure.add_node(node_id, **node_data)
        
        # Add edges to STPA model
        for u, v, key, data in self.G.edges(data=True, keys=True):
            self.model.control_structure.add_edge(u, v, key=key, **data)
        
        # Save chat transcript
        if hasattr(self, 'chat_panel'):
            self.chat_panel._save_chat_transcript()
    
    def _load_from_model(self):
        """Load graph from the STPA model"""
        # Clear current graph with proper cleanup
        self._clear_scene_safely()
        self.G.clear()
        
        # Load nodes from model
        for node_id, node_data in self.model.control_structure.nodes(data=True):
            # Create node data
            data = NodeData(
                name=node_data.get('name', f'n{node_id}'),
                states=node_data.get('states', []),
                shape=node_data.get('shape', 'circle'),
                size=node_data.get('size', 24.0)
            )
            
            # Create visual item
            item = NodeItem(node_id=node_id, data=data)
            # Get position from the saved data (support both 'position' and 'pos' for compatibility)
            pos = node_data.get('position', node_data.get('pos', (0, 0)))
            item.setPos(pos[0], pos[1])
            self.scene.addItem(item)
            
            # Add to local graph
            self.G.add_node(node_id, **node_data)
        
        # Load edges from model
        for u, v, key, edge_data in self.model.control_structure.edges(data=True, keys=True):
            if u in self.G.nodes and v in self.G.nodes:
                # Find visual nodes
                src_node = None
                dst_node = None
                for node in self.scene.iter_nodes():
                    if node.node_id == u:
                        src_node = node
                    elif node.node_id == v:
                        dst_node = node
                
                if src_node and dst_node:
                    # Create edge data
                    data = EdgeData(
                        name=edge_data.get('name', f'e{u}_{v}_{key}'),
                        weight=edge_data.get('weight', 1.0),
                        undirected=edge_data.get('undirected', False),
                        bidirectional=edge_data.get('bidirectional', False)
                    )
                    
                    # Create visual item
                    edge_item = EdgeItem(src_node, dst_node, data, edge_key=key)
                    self.scene.addItem(edge_item)
                    
                    # Add to local graph
                    self.G.add_edge(u, v, key=key, **edge_data)
        
        # Reflow all multi-edges
        processed_pairs = set()
        for u, v in self.G.edges():
            pair = tuple(sorted([u, v]))
            if pair not in processed_pairs:
                self.scene._reflow_all_edges_between_nodes(u, v)
                processed_pairs.add(pair)
        
        # Auto-zoom to fit the loaded model
        if self.G.nodes:
            self.zoom_to_fit()
        
        self._update_status()
    
    def _clear_scene_safely(self):
        """Safely clear the scene with proper Qt item cleanup"""
        # Get all items before clearing
        items = list(self.scene.items())
        
        # Remove items from scene first
        for item in items:
            self.scene.removeItem(item)
            # Let Qt handle deletion through parent-child relationships
            if hasattr(item, 'deleteLater'):
                item.deleteLater()
        
        # Now clear the scene
        self.scene.clear()
    
    def _update_status(self):
        """Update status information"""
        if not self.scene._adding_node and not self.scene._connecting and not self.scene._deleting:
            node_count = len(self.G.nodes)
            edge_count = self.G.number_of_edges()
            self.status_label.setText(f"Nodes: {node_count}, Edges: {edge_count} - Tip: Hold C over a node, move to another, release C to create edge")
    
    def undo(self):
        """Undo the last operation"""
        if self.scene.command_manager.can_undo():
            self.scene.command_manager.undo()
            self._update_status()
            # Update toolbar button states
            self._update_undo_redo_buttons()
    
    def redo(self):
        """Redo the next operation"""
        if self.scene.command_manager.can_redo():
            self.scene.command_manager.redo()
            self._update_status()
            # Update toolbar button states
            self._update_undo_redo_buttons()
    
    def _update_undo_redo_buttons(self):
        """Update the enabled state of undo/redo buttons"""
        if hasattr(self, 'act_undo'):
            self.act_undo.setEnabled(self.scene.command_manager.can_undo())
        if hasattr(self, 'act_redo'):
            self.act_redo.setEnabled(self.scene.command_manager.can_redo())
    
    def _on_command_executed(self):
        """Called after any command is executed"""
        self._update_undo_redo_buttons()
        self._update_status()
        
        # Refresh properties panel if an item is selected
        selected_items = self.scene.selectedItems()
        if selected_items:
            self._show_properties_for_item(selected_items[-1])
    
    def _on_selection_changed(self):
        """Handle selection changes to update properties panel"""
        items = self.scene.selectedItems()
        if not items:
            self.properties_panel.clear_properties()
            return
        
        # Show properties for the last selected item
        item = items[-1]
        self._show_properties_for_item(item)
    
    def _show_properties_for_item(self, item):
        """Show properties for a specific item"""
        if isinstance(item, NodeItem):
            # Convert to properties format
            node_data = {
                'name': item.data.name,
                'node_type': 'other',  # Default
                'description': '',
                'position': (item.scenePos().x(), item.scenePos().y()),
                'states': item.data.states,
                'shape': item.data.shape,
                'size': item.data.size
            }
            self.properties_panel.show_node_properties(str(item.node_id), node_data)
        elif isinstance(item, EdgeItem):
            # Convert to properties format  
            edge_data = {
                'label': item.data.name,
                'link_type': 'control_action' if not item.data.undirected else 'other',
                'description': '',
                'source_id': str(item.src.node_id),
                'target_id': str(item.dst.node_id),
                'undirected': item.data.undirected,
                'bidirectional': item.data.bidirectional,
                'weight': item.data.weight
            }
            self.properties_panel.show_edge_properties(f"{item.src.node_id}->{item.dst.node_id}", edge_data)
        else:
            self.properties_panel.clear_properties()
    
    def _on_property_changed(self, item_id: str, property_name: str, value):
        """Handle property changes from properties panel using command system"""
        # Find the node and create property change command
        for node in self.scene.iter_nodes():
            if str(node.node_id) == item_id:
                # Get the old value
                old_value = self._get_node_property_value(node, property_name)
                
                # Only create command if value actually changed
                if old_value != value:
                    command = ChangeNodePropertyCommand(self.scene, node, property_name, old_value, value)
                    self.scene.command_manager.execute_command(command)
                    self.model_changed.emit()
                return
        
        # Handle edge property changes
        for edge in self.scene.iter_edges():
            edge_id = f"{edge.src.node_id}->{edge.dst.node_id}"
            if edge_id == item_id:
                # Get the old value
                old_value = self._get_edge_property_value(edge, property_name)
                
                # Only create command if value actually changed
                if old_value != value:
                    command = ChangeEdgePropertyCommand(self.scene, edge, property_name, old_value, value)
                    self.scene.command_manager.execute_command(command)
                    self.model_changed.emit()
                return
    
    def _get_node_property_value(self, node: NodeItem, property_name: str):
        """Get the current value of a node property"""
        if property_name == 'name':
            return node.data.name
        elif property_name == 'states':
            return node.data.states
        elif property_name == 'shape':
            return node.data.shape
        elif property_name == 'size':
            return node.data.size
        elif property_name == 'node_type':
            return self.scene.G.nodes[node.node_id].get('node_type', 'other')
        elif property_name == 'description':
            return self.scene.G.nodes[node.node_id].get('description', '')
        return None
    
    def _get_edge_property_value(self, edge: EdgeItem, property_name: str):
        """Get the current value of an edge property"""
        if property_name == 'label':
            return edge.data.name
        elif property_name == 'link_type':
            return self.scene.G[edge.src.node_id][edge.dst.node_id][edge.edge_key].get('link_type', 'other')
        elif property_name == 'description':
            return self.scene.G[edge.src.node_id][edge.dst.node_id][edge.edge_key].get('description', '')
        elif property_name == 'undirected':
            return edge.data.undirected
        elif property_name == 'bidirectional':
            return edge.data.bidirectional
        elif property_name == 'weight':
            return edge.data.weight
        return None
    
    def _rename_node(self, node: NodeItem):
        """Rename a node via input dialog"""
        new_name, ok = QInputDialog.getText(self, "Rename Node", "Node name:", text=node.data.name)
        if ok and new_name.strip():
            node.data.name = new_name.strip()
            self.G.nodes[node.node_id]['name'] = new_name.strip()
            node.update()  # Trigger repaint
            self.model_changed.emit()
    
    def _rename_edge(self, edge: EdgeItem):
        """Rename an edge via input dialog"""
        new_name, ok = QInputDialog.getText(self, "Rename Edge", "Edge name:", text=edge.data.name)
        if ok and new_name.strip():
            edge.data.name = new_name.strip()
            self.G[edge.src.node_id][edge.dst.node_id][edge.edge_key]['name'] = new_name.strip()
            self.model_changed.emit()
    
    # File operations
    def auto_layout(self):
        """Apply automatic layout to the graph"""
        if not self.G.nodes:
            return
        
        try:
            # Use NetworkX spring layout
            pos = nx.spring_layout(self.G, scale=300, iterations=50)
            
            # Update node positions
            for node in self.scene.iter_nodes():
                if node.node_id in pos:
                    x, y = pos[node.node_id]
                    node.setPos(x, y)
            
            # Update all edge paths
            for edge in self.scene.iter_edges():
                edge.update_path()
            
            self.model_changed.emit()
            self.status_label.setText("Auto-layout applied successfully")
            
        except ImportError:
            QMessageBox.warning(self, "Layout Error", "NetworkX layout algorithms are not available")
        except Exception as e:
            error_msg = f"Could not apply automatic layout: {str(e)}"
            QMessageBox.warning(self, "Layout Error", error_msg)
            self.status_label.setText("Auto-layout failed")
    
    def zoom_to_fit(self):
        """Zoom the view to fit all items in the scene"""
        if not self.scene.items():
            return
            
        # Get the bounding rectangle of all items
        items_rect = self.scene.itemsBoundingRect()
        
        # Add some padding
        padding = DEFAULT_PADDING
        items_rect.adjust(-padding, -padding, padding, padding)
        
        # Fit the view to show all items
        self.view.fitInView(items_rect, Qt.KeepAspectRatio)
        
        # Ensure a reasonable zoom level (not too zoomed in or out)
        current_transform = self.view.transform()
        scale_factor = current_transform.m11()  # Get the scale factor
        
        # Limit zoom level between MIN and MAX zoom factors
        if scale_factor > MAX_ZOOM_FACTOR:
            self.view.setTransform(QTransform().scale(MAX_ZOOM_FACTOR, MAX_ZOOM_FACTOR))
        elif scale_factor < MIN_ZOOM_FACTOR:
            self.view.setTransform(QTransform().scale(MIN_ZOOM_FACTOR, MIN_ZOOM_FACTOR))
    
    def keyPressEvent(self, event):
        """Handle key events for the control structure tab"""
        # Forward delete/backspace to scene for selected item deletion
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if hasattr(self.scene, 'delete_selected'):
                self.scene.delete_selected()
                event.accept()
                return
        
        # Forward other key events to the scene
        if hasattr(self.scene, 'keyPressEvent'):
            self.scene.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        """Handle show event to set proper focus"""
        super().showEvent(event)
        # Only set focus to the graphics view if no other widget in the window has focus
        # This prevents stealing focus from property editors
        if hasattr(self, 'view'):
            focused_widget = QApplication.focusWidget()
            # Don't steal focus if a text editor or combo box already has it
            if (focused_widget is None or 
                not isinstance(focused_widget, (QLineEdit, QTextEdit, QComboBox, QPlainTextEdit))):
                self.view.setFocus(Qt.OtherFocusReason)
