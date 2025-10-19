"""
Core data models for STPA.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from datetime import datetime
from enum import Enum
import json
import networkx as nx
import logging

# Import version from constants for consistency
from core.constants import VERSION

# Get logger for this module
logger = logging.getLogger(__name__)


class HazardConditionOperator(Enum):
    """Logical operators for hazard conditions"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class State:
    """State in a node's state machine"""
    name: str
    description: str = ""
    is_initial: bool = False


@dataclass
class SystemNode:
    """Enhanced node with state machine support"""
    id: str
    name: str
    position: Tuple[float, float] = (0.0, 0.0)
    shape: str = "circle"  # "circle", "rectangle", "hexagon"
    size: float = 24.0
    description: str = ""
    states: List[State] = field(default_factory=list)
    
    def add_state(self, name: str, description: str = "", is_initial: bool = False) -> None:
        """Add a new state to this node's state machine"""
        if is_initial:
            # Clear other initial states
            for state in self.states:
                state.is_initial = False
        self.states.append(State(name=name, description=description, is_initial=is_initial))
    
    def get_initial_state(self) -> Optional[State]:
        """Get the initial state of this node"""
        for state in self.states:
            if state.is_initial:
                return state
        return None


@dataclass
class ControlLink:
    """Control/feedback link between nodes"""
    id: str
    source_id: str
    target_id: str
    name: str = ""
    description: str = ""
    weight: float = 1.0
    undirected: bool = False
    bidirectional: bool = False


@dataclass
class HazardCondition:
    """Logical condition for hazards (e.g., Node N1 in State S1 AND Node N2 in State S2)"""
    # For now, keep it simple with a text description
    # Later can be enhanced with a proper logical expression tree
    description: str
    # Future: structured representation for automated analysis


@dataclass
class Loss:
    """STPA Loss definition"""
    description: str
    severity: str = ""
    rationale: str = ""


@dataclass
class Hazard:
    """STPA Hazard definition"""
    description: str
    severity: str = ""
    rationale: str = ""
    related_losses: List[str] = field(default_factory=list)  # Loss IDs
    condition: Optional[HazardCondition] = None


@dataclass
class LossScenario:
    """STPA Loss Scenario"""
    id: str
    name: str
    description: str
    related_uca_ids: List[str] = field(default_factory=list)


@dataclass
class UCAContext:
    """Operational context for UCA analysis"""
    id: str
    name: str
    description: str
    conditions: List[str] = field(default_factory=list)


@dataclass
class UCACategory(Enum):
    """Categories of unsafe control actions"""
    NOT_PROVIDED = "Not Provided"
    PROVIDED_INCORRECTLY = "Provided Incorrectly"
    WRONG_TIMING = "Wrong Timing"
    STOPPED_TOO_SOON_OR_TOO_LONG = "Stopped Too Soon/Applied Too Long"


@dataclass
class UnsafeControlAction:
    """Unsafe Control Action identified in STPA Step 2"""
    id: str
    control_action: str  # Reference to control action
    context: str  # Reference to context
    category: str  # UCA category value
    hazard_links: List[str] = field(default_factory=list)
    rationale: str = ""
    severity: int = 1  # 1-5 scale
    likelihood: int = 1  # 1-5 scale
    
    @property
    def risk_score(self) -> int:
        """Calculate risk score (severity × likelihood)"""
        return self.severity * self.likelihood


@dataclass
class Document:
    """Document reference for project documentation"""
    filename: str
    original_name: str  # Original filename when uploaded
    file_type: str  # "pdf", "png", "jpg", "jpeg", "gif", "svg", etc.
    file_size: int  # File size in bytes
    upload_date: str  # ISO format date string
    description: str = ""  # User-provided description
    
    @property
    def is_image(self) -> bool:
        """Check if document is an image type"""
        image_types: Set[str] = {"png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"}
        return self.file_type.lower() in image_types
    
    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF"""
        return self.file_type.lower() == "pdf"


class IDGenerator:
    """Optimized ID generation with caching for better performance"""
    
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self._node_counter: int = 1
        self._link_counter: int = 1
        self._cached_node_ids: Optional[Set[str]] = None
        self._cached_link_ids: Optional[Set[str]] = None
        self._dirty_node_cache: bool = True
        self._dirty_link_cache: bool = True
    
    def invalidate_cache(self) -> None:
        """Invalidate ID caches when structure changes"""
        self._dirty_node_cache = True
        self._dirty_link_cache = True
        if self.enable_cache:
            logger.debug("ID cache invalidated")
    
    def _scan_existing_node_ids(self, control_structure: 'ControlStructure') -> Set[str]:
        """Scan existing node IDs and update counter"""
        existing_ids: Set[str] = set()
        max_id = 0
        
        for node_id in control_structure.nodes.keys():
            existing_ids.add(node_id)
            if isinstance(node_id, str) and node_id.startswith('n') and node_id[1:].isdigit():
                num = int(node_id[1:])
                max_id = max(max_id, num)
        
        # Set counter to one higher than max found
        self._node_counter = max_id + 1
        return existing_ids
    
    def _scan_existing_link_ids(self, control_structure: 'ControlStructure') -> Set[str]:
        """Scan existing link IDs and update counter"""
        existing_ids: Set[str] = set()
        max_id = 0
        
        for u, v, key in control_structure.edges(keys=True):
            if isinstance(key, str):
                existing_ids.add(key)
                if key.startswith('e') and key[1:].isdigit():
                    num = int(key[1:])
                    max_id = max(max_id, num)
            elif isinstance(key, int):
                existing_ids.add(str(key))
                max_id = max(max_id, key)
        
        # Set counter to one higher than max found
        self._link_counter = max_id + 1
        return existing_ids
    
    def get_next_node_id(self, control_structure: 'ControlStructure') -> str:
        """Generate the next available node ID with optimized caching"""
        if not self.enable_cache:
            # Fallback to scanning every time
            existing_ids = [int(nid[1:]) for nid in control_structure.nodes.keys() 
                           if isinstance(nid, str) and nid.startswith('n') and nid[1:].isdigit()]
            next_num = max(existing_ids, default=0) + 1
            return f"n{next_num}"
        
        # Use cached approach
        if self._dirty_node_cache or self._cached_node_ids is None:
            self._cached_node_ids = self._scan_existing_node_ids(control_structure)
            self._dirty_node_cache = False
        
        # Find next available ID using counter
        while f"n{self._node_counter}" in self._cached_node_ids:
            self._node_counter += 1
        
        node_id = f"n{self._node_counter}"
        self._node_counter += 1
        
        # Update cache
        self._cached_node_ids.add(node_id)
        
        logger.debug(f"Generated node ID: {node_id}")
        return node_id
    
    def get_next_link_id(self, control_structure: 'ControlStructure') -> str:
        """Generate the next available link ID with optimized caching"""
        if not self.enable_cache:
            # Fallback to scanning every time
            existing_ids = []
            for u, v, key in control_structure.edges(keys=True):
                if isinstance(key, str) and key.startswith('e') and key[1:].isdigit():
                    existing_ids.append(int(key[1:]))
                elif isinstance(key, int):
                    existing_ids.append(key)
            next_num = max(existing_ids, default=0) + 1
            return f"e{next_num}"
        
        # Use cached approach
        if self._dirty_link_cache or self._cached_link_ids is None:
            self._cached_link_ids = self._scan_existing_link_ids(control_structure)
            self._dirty_link_cache = False
        
        # Find next available ID using counter
        while f"e{self._link_counter}" in self._cached_link_ids:
            self._link_counter += 1
        
        link_id = f"e{self._link_counter}"
        self._link_counter += 1
        
        # Update cache
        self._cached_link_ids.add(link_id)
        
        logger.debug(f"Generated link ID: {link_id}")
        return link_id
    
    def register_node_id(self, node_id: str) -> None:
        """Register a new node ID (when loading from file)"""
        if self.enable_cache and self._cached_node_ids is not None:
            self._cached_node_ids.add(node_id)
            # Update counter if this ID is higher
            if isinstance(node_id, str) and node_id.startswith('n') and node_id[1:].isdigit():
                num = int(node_id[1:])
                if num >= self._node_counter:
                    self._node_counter = num + 1
    
    def register_link_id(self, link_id: Union[str, int]) -> None:
        """Register a new link ID (when loading from file)"""
        if self.enable_cache and self._cached_link_ids is not None:
            str_id = str(link_id)
            self._cached_link_ids.add(str_id)
            # Update counter if this ID is higher
            if isinstance(link_id, str) and link_id.startswith('e') and link_id[1:].isdigit():
                num = int(link_id[1:])
                if num >= self._link_counter:
                    self._link_counter = num + 1
            elif isinstance(link_id, int):
                if link_id >= self._link_counter:
                    self._link_counter = link_id + 1


class ControlStructure(nx.MultiDiGraph):
    """System of Systems / Control Structure representation using NetworkX MultiDiGraph"""
    
    def __init__(self):
        super().__init__()
        self._id_generator = IDGenerator()
    
    def add_node_with_data(self, node_id: str, name: str, **kwargs) -> SystemNode:
        """Add a new node to the control structure with SystemNode data"""
        node = SystemNode(id=node_id, name=name, **kwargs)
        # Add to NetworkX graph with node data as attributes (excluding id to avoid duplication)
        node_attrs = {k: v for k, v in node.__dict__.items() if k != 'id'}
        super().add_node(node_id, **node_attrs)
        
        # Register ID with generator
        self._id_generator.register_node_id(node_id)
        
        return node
    
    def add_node(self, node_id: str, name: str, **kwargs) -> SystemNode:
        """Add a new node to the control structure (for file I/O compatibility)"""
        return self.add_node_with_data(node_id, name, **kwargs)
    
    def add_link(self, link_id: str, source_id: str, target_id: str, **kwargs) -> ControlLink:
        """Add a new link to the control structure"""
        link = ControlLink(id=link_id, source_id=source_id, target_id=target_id, **kwargs)
        # Add to NetworkX graph with link data as attributes
        super().add_edge(source_id, target_id, key=link_id, **link.__dict__)
        
        # Register ID with generator
        self._id_generator.register_link_id(link_id)
        
        return link
    
    def get_node_data(self, node_id: str) -> Optional[SystemNode]:
        """Get a node's data as SystemNode object"""
        if node_id in self.nodes:
            node_attrs = self.nodes[node_id]
            return SystemNode(id=node_id, **node_attrs)
        return None
    
    def remove_node_with_links(self, node_id: str) -> None:
        """Remove a node and all its connected links"""
        if node_id in self.nodes:
            super().remove_node(node_id)  # NetworkX automatically removes connected edges
            # Invalidate ID cache since structure changed
            self._id_generator.invalidate_cache()
    
    def remove_edge(self, u, v, key=None) -> None:
        """Remove an edge and invalidate cache"""
        super().remove_edge(u, v, key)
        self._id_generator.invalidate_cache()
    
    def clear(self) -> None:
        """Clear all nodes and edges"""
        super().clear()
        self._id_generator.invalidate_cache()
    
    def get_next_node_id(self) -> str:
        """Generate the next available node ID"""
        return self._id_generator.get_next_node_id(self)
    
    def get_next_link_id(self) -> str:
        """Generate the next available link ID"""
        return self._id_generator.get_next_link_id(self)


@dataclass
class STPAModel:
    """Complete STPA model containing all components"""
    name: str = "Untitled STPA Model"
    version: str = VERSION
    description: str = ""
    
    # Core control structure (current functionality)
    control_structure: ControlStructure = field(default_factory=ControlStructure)
    
    # STPA analysis components
    losses: List[Loss] = field(default_factory=list)
    hazards: List[Hazard] = field(default_factory=list)
    
    # UCA Analysis (NEW!)
    uca_contexts: List[UCAContext] = field(default_factory=list)
    unsafe_control_actions: List[UnsafeControlAction] = field(default_factory=list)
    
    # Future: Loss scenarios
    loss_scenarios: List[LossScenario] = field(default_factory=list)
    
    # Document management
    documents: List[Document] = field(default_factory=list)
    
    # Metadata for system description and other general information
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Chat transcripts for each tab
    chat_transcripts: Dict[str, str] = field(default_factory=lambda: {
        "control_structure": "",
        "description": "",
        "losses_hazards": "",
        "uca": "",
        "scenarios": ""
    })
    
    def add_loss(self, description: str, severity: str = "", rationale: str = "") -> Loss:
        """Add a new loss to the model"""
        loss = Loss(description=description, severity=severity, rationale=rationale)
        self.losses.append(loss)
        logger.debug(f"Added loss: {description}")
        return loss
    
    def add_hazard(self, description: str, severity: str = "", rationale: str = "",
                   related_losses: Optional[List[str]] = None, 
                   condition: Optional[HazardCondition] = None) -> Hazard:
        """Add a new hazard to the model"""
        if related_losses is None:
            related_losses = []
        hazard = Hazard(description=description, severity=severity, rationale=rationale,
                       related_losses=related_losses, condition=condition)
        self.hazards.append(hazard)
        logger.debug(f"Added hazard: {description}")
        return hazard
    
    def get_next_node_id(self) -> str:
        """Generate the next available node ID"""
        return self.control_structure.get_next_node_id()
    
    def get_next_link_id(self) -> str:
        """Generate the next available link ID"""
        return self.control_structure.get_next_link_id()
    
    def add_document(self, filename: str, original_name: str, file_type: str, 
                    file_size: int, description: str = "") -> Document:
        """Add a document reference to the model"""
        document = Document(
            filename=filename,
            original_name=original_name,
            file_type=file_type,
            file_size=file_size,
            upload_date=datetime.now().isoformat(),
            description=description
        )
        self.documents.append(document)
        logger.debug(f"Added document: {original_name} ({file_type})")
        return document
    
    def remove_document(self, filename: str) -> bool:
        """Remove a document reference from the model"""
        for i, doc in enumerate(self.documents):
            if doc.filename == filename:
                del self.documents[i]
                logger.debug(f"Removed document: {filename}")
                return True
        return False
    
    def get_document(self, filename: str) -> Optional[Document]:
        """Get a document by filename"""
        for doc in self.documents:
            if doc.filename == filename:
                return doc
        return None
    
    def get_analysis_statistics(self) -> Dict[str, int]:
        """Get statistics about the analysis completeness"""
        return {
            'nodes': len(self.control_structure.nodes),
            'edges': len(self.control_structure.edges),
            'losses': len(self.losses),
            'hazards': len(self.hazards),
            'unsafe_control_actions': len(self.unsafe_control_actions),
            'documents': len(self.documents)
        }
