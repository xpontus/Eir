"""
File I/O operations for the STPA model.
"""

import json
import networkx as nx
from typing import Dict, Any, Tuple, List, Optional, Union
from pathlib import Path
import logging

from core.models import STPAModel, SystemNode, ControlLink, Loss, Hazard, State, HazardCondition, Document, UnsafeControlAction
from core.constants import VERSION

# Get logger for this module
logger = logging.getLogger(__name__)


class STPAModelIO:
    """Input/output operations for STPA model data."""
    
    @staticmethod
    def save_json(model: STPAModel, file_path: Union[str, Path]) -> None:
        """Save the STPA model to JSON format"""
        file_path_str = str(file_path)
        logger.info(f"Saving model to {file_path_str}")
        
        try:
            data = STPAModelIO._model_to_dict(model)
            
            with open(file_path_str, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved model to {file_path_str}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to write to file '{file_path_str}': {str(e)}")
            raise IOError(f"Failed to write to file '{file_path_str}': {str(e)}")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize model data: {str(e)}")
            raise ValueError(f"Failed to serialize model data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error saving model: {str(e)}")
            raise RuntimeError(f"Unexpected error saving model: {str(e)}")
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> STPAModel:
        """Load STPA model from JSON format"""
        file_path_str = str(file_path)
        logger.info(f"Loading model from {file_path_str}")
        
        try:
            with open(file_path_str, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model = STPAModelIO._dict_to_model(data)
            logger.info(f"Successfully loaded model from {file_path_str}")
            return model
        except FileNotFoundError:
            logger.error(f"File not found: '{file_path_str}'")
            raise FileNotFoundError(f"File not found: '{file_path_str}'")
        except (IOError, OSError) as e:
            logger.error(f"Failed to read file '{file_path_str}': {str(e)}")
            raise IOError(f"Failed to read file '{file_path_str}': {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in file '{file_path_str}': {str(e)}")
            raise ValueError(f"Invalid JSON format in file '{file_path_str}': {str(e)}")
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Invalid model data format in file '{file_path_str}': {str(e)}")
            raise ValueError(f"Invalid model data format in file '{file_path_str}': {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading model: {str(e)}")
            raise RuntimeError(f"Unexpected error loading model: {str(e)}")
    
    # GraphML functionality commented out for simplicity
    # @staticmethod
    # def save_graphml(model: STPAModel, file_path: str):
    #     """Save the control structure to GraphML format with STPA data as sidecar"""
    #     pass
    
    # @staticmethod  
    # def load_graphml(file_path: str) -> STPAModel:
    #     """Load STPA model from GraphML format with STPA sidecar data"""
    #     pass
        """Save the control structure to GraphML format with STPA data as sidecar"""
        # Convert control structure to NetworkX graph
        G = nx.MultiDiGraph()
        G.graph['version'] = model.version
        G.graph['model_name'] = model.name
        
        # Add nodes
        for node in model.control_structure.nodes.values():
            states_str = "|".join(state.name for state in node.states)
            G.add_node(
                node.id,
                name=node.name,
                description=node.description,
                shape=node.shape,
                size=node.size,
                states=states_str,
                pos_x=node.position[0],
                pos_y=node.position[1]
            )
        
        # Add edges
        for link in model.control_structure.links.values():
            G.add_edge(
                link.source_id,
                link.target_id,
                key=link.id,
                name=link.name,
                description=link.description,
                weight=link.weight,
                undirected=link.undirected,
                bidirectional=link.bidirectional
            )
        
        # Save GraphML
        nx.write_graphml(G, file_path)
        
        # Save STPA data as sidecar JSON
        stpa_data = {
            'model_name': model.name,
            'version': model.version,
            'description': model.description,
            'losses': {lid: STPAModelIO._loss_to_dict(loss) for lid, loss in model.losses.items()},
            'hazards': {hid: STPAModelIO._hazard_to_dict(hazard) for hid, hazard in model.hazards.items()},
            'unsafe_control_actions': {uid: STPAModelIO._uca_to_dict(uca) for uid, uca in model.unsafe_control_actions.items()},
            'loss_scenarios': {sid: STPAModelIO._scenario_to_dict(scenario) for sid, scenario in model.loss_scenarios.items()},
            'chat_transcripts': model.chat_transcripts,
            'detailed_states': {nid: [STPAModelIO._state_to_dict(state) for state in node.states] 
                               for nid, node in model.control_structure.nodes.items() if node.states}
        }
        
        stpa_path = str(Path(file_path).with_suffix('.stpa.json'))
        with open(stpa_path, 'w', encoding='utf-8') as f:
            json.dump(stpa_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_graphml(file_path: str) -> STPAModel:
        """Load STPA model from GraphML format with STPA sidecar data"""
        # Load NetworkX graph
        G = nx.read_graphml(file_path)
        
        # Create model
        model = STPAModel()
        model.version = G.graph.get('version', '0.1')
        model.name = G.graph.get('model_name', 'Loaded Model')
        
        # Load control structure
        for node_id, attrs in G.nodes(data=True):
            node = model.control_structure.add_node(
                node_id=node_id,
                name=attrs.get('name', f'Node {node_id}'),
                description=attrs.get('description', ''),
                shape=attrs.get('shape', 'circle'),
                size=float(attrs.get('size', 24.0)),
                position=(float(attrs.get('pos_x', 0.0)), float(attrs.get('pos_y', 0.0)))
            )
            
            # Parse basic states from GraphML
            states_str = attrs.get('states', '')
            if states_str:
                for state_name in states_str.split('|'):
                    if state_name.strip():
                        node.add_state(state_name.strip())
        
        for u, v, attrs in G.edges(data=True):
            model.control_structure.add_link(
                link_id=attrs.get('key', f'{u}_{v}'),
                source_id=u,
                target_id=v,
                name=attrs.get('name', ''),
                description=attrs.get('description', ''),
                weight=float(attrs.get('weight', 1.0)),
                undirected=str(attrs.get('undirected', 'False')).lower() == 'true',
                bidirectional=str(attrs.get('bidirectional', 'False')).lower() == 'true'
            )
        
        # Try to load STPA sidecar data
        try:
            stpa_path = str(Path(file_path).with_suffix('.stpa.json'))
            with open(stpa_path, 'r', encoding='utf-8') as f:
                stpa_data = json.load(f)
            
            model.description = stpa_data.get('description', '')
            model.chat_transcripts = stpa_data.get('chat_transcripts', {})
            
            # Load losses
            for lid, loss_data in stpa_data.get('losses', {}).items():
                model.add_loss(lid, loss_data['name'], loss_data['description'])
            
            # Load hazards
            for hid, hazard_data in stpa_data.get('hazards', {}).items():
                condition = None
                if hazard_data.get('condition'):
                    condition = HazardCondition(description=hazard_data['condition']['description'])
                hazard = model.add_hazard(hid, hazard_data['name'], hazard_data['description'], condition)
                hazard.related_losses = hazard_data.get('related_losses', [])
            
            # Load detailed state information
            detailed_states = stpa_data.get('detailed_states', {})
            for node_id, states_data in detailed_states.items():
                node = model.control_structure.get_node(node_id)
                if node:
                    node.states = []  # Clear basic states
                    for state_data in states_data:
                        node.states.append(State(
                            name=state_data['name'],
                            description=state_data.get('description', ''),
                            is_initial=state_data.get('is_initial', False)
                        ))
            
        except FileNotFoundError:
            # No sidecar file, just use what we got from GraphML
            pass
        
        return model
    
    # Helper methods for serialization
    @staticmethod
    def _model_to_dict(model: STPAModel) -> Dict[str, Any]:
        """Convert STPA model to dictionary for JSON serialization"""
        logger.debug("Converting model to dictionary for serialization")
        
        # Extract nodes from NetworkX graph
        nodes_list: List[Dict[str, Any]] = []
        for node_id, node_attrs in model.control_structure.nodes(data=True):
            node_dict = {
                'id': node_id,
                'name': node_attrs.get('name', ''),
                'position': list(node_attrs.get('position', [0.0, 0.0])),
                'shape': node_attrs.get('shape', 'circle'),
                'size': node_attrs.get('size', 24.0),
                'description': node_attrs.get('description', ''),
                'states': []
            }
            # Handle states if they exist
            states = node_attrs.get('states', [])
            for state in states:
                if hasattr(state, '__dict__'):  # State object
                    state_dict = {
                        'name': state.name,
                        'description': state.description,
                        'is_initial': state.is_initial
                    }
                else:  # Already a dict
                    state_dict = state
                node_dict['states'].append(state_dict)
            nodes_list.append(node_dict)
        
        # Extract edges from NetworkX graph
        edges_list: List[Dict[str, Any]] = []
        for src, dst, key, edge_attrs in model.control_structure.edges(data=True, keys=True):
            edge_dict = {
                'id': str(key),
                'source_id': src,
                'target_id': dst,
                'name': edge_attrs.get('name', ''),
                'description': edge_attrs.get('description', ''),
                'weight': edge_attrs.get('weight', 1.0),
                'undirected': edge_attrs.get('undirected', False),
                'bidirectional': edge_attrs.get('bidirectional', False)
            }
            edges_list.append(edge_dict)
        
        result = {
            'version': model.version,
            'name': model.name,
            'description': model.description,
            'control_structure': {
                'nodes': nodes_list,
                'edges': edges_list
            },
            'losses': [STPAModelIO._loss_to_dict(loss) for loss in model.losses],
            'hazards': [STPAModelIO._hazard_to_dict(hazard) for hazard in model.hazards],
            'unsafe_control_actions': [STPAModelIO._uca_to_dict(uca) for uca in model.unsafe_control_actions],
            'uca_contexts': [STPAModelIO._uca_context_to_dict(ctx) for ctx in model.uca_contexts],
            'loss_scenarios': [STPAModelIO._scenario_to_dict(scenario) for scenario in model.loss_scenarios],
            'documents': [STPAModelIO._document_to_dict(doc) for doc in model.documents],
            'metadata': model.metadata,
            'chat_transcripts': model.chat_transcripts
        }
        
        logger.debug(f"Serialized model with {len(nodes_list)} nodes, {len(edges_list)} edges")
        return result
    
    @staticmethod
    def _dict_to_model(data: Dict[str, Any]) -> STPAModel:
        """Convert dictionary to STPA model"""
        logger.debug("Converting dictionary to model")
        
        model = STPAModel(
            name=data.get('name', 'Untitled Model'),
            version=data.get('version', VERSION),
            description=data.get('description', ''),
            metadata=data.get('metadata', {}),
            chat_transcripts=data.get('chat_transcripts', {
                "control_structure": "",
                "description": "",
                "losses_hazards": "",
                "uca": "",
                "scenarios": ""
            })
        )
        
        # Load control structure
        cs_data = data.get('control_structure', {})
        
        # Load nodes
        for node_data in cs_data.get('nodes', []):
            node_id = node_data['id']
            # Add node to NetworkX graph with backwards compatibility for position field
            position_data = node_data.get('position')
            if position_data is None:
                # Fall back to old 'pos' field for backwards compatibility
                position_data = node_data.get('pos', [0.0, 0.0])
            
            model.control_structure.add_node(
                node_id,
                name=node_data.get('name', ''),
                position=tuple(position_data),
                shape=node_data.get('shape', 'circle'),
                size=node_data.get('size', 24.0),
                description=node_data.get('description', ''),
                states=[]  # Will be populated below
            )
            
            # Handle states
            states = []
            for state_data in node_data.get('states', []):
                from core.models import State
                state = State(
                    name=state_data['name'],
                    description=state_data.get('description', ''),
                    is_initial=state_data.get('is_initial', False)
                )
                states.append(state)
            
            # Update node with states
            model.control_structure.nodes[node_id]['states'] = states
        
        # Load edges
        for edge_data in cs_data.get('edges', []):
            edge_id = edge_data['id']
            src = edge_data['source_id']
            dst = edge_data['target_id']
            
            model.control_structure.add_edge(
                src, dst, key=edge_id,
                id=edge_id,
                source_id=src,
                target_id=dst,
                name=edge_data.get('name', ''),
                description=edge_data.get('description', ''),
                weight=edge_data.get('weight', 1.0),
                undirected=edge_data.get('undirected', False),
                bidirectional=edge_data.get('bidirectional', False)
            )
        
        # Load STPA components
        for loss_data in data.get('losses', []):
            loss = Loss(
                description=loss_data['description'],
                severity=loss_data.get('severity', ''),
                rationale=loss_data.get('rationale', '')
            )
            model.losses.append(loss)
        
        for hazard_data in data.get('hazards', []):
            condition = None
            if hazard_data.get('condition'):
                condition = HazardCondition(description=hazard_data['condition']['description'])
            hazard = Hazard(
                description=hazard_data['description'],
                severity=hazard_data.get('severity', ''),
                rationale=hazard_data.get('rationale', ''),
                related_losses=hazard_data.get('related_losses', []),
                condition=condition
            )
            model.hazards.append(hazard)
        
        # Load UCA data
        from core.models import UnsafeControlAction, UCAContext
        
        for uca_data in data.get('unsafe_control_actions', []):
            uca = UnsafeControlAction(
                id=uca_data['id'],
                control_action=uca_data['control_action'],
                context=uca_data['context'],
                category=uca_data['category'],
                hazard_links=uca_data.get('hazard_links', []),
                rationale=uca_data.get('rationale', ''),
                severity=uca_data.get('severity', 1),
                likelihood=uca_data.get('likelihood', 1)
            )
            model.unsafe_control_actions.append(uca)
        
        for ctx_data in data.get('uca_contexts', []):
            ctx = UCAContext(
                id=ctx_data['id'],
                name=ctx_data['name'],
                description=ctx_data.get('description', ''),
                conditions=ctx_data.get('conditions', [])
            )
            model.uca_contexts.append(ctx)
        
        # Load documents
        for doc_data in data.get('documents', []):
            document = Document(
                filename=doc_data['filename'],
                original_name=doc_data['original_name'],
                file_type=doc_data['file_type'],
                file_size=doc_data['file_size'],
                upload_date=doc_data['upload_date'],
                description=doc_data.get('description', '')
            )
            model.documents.append(document)
        
        logger.debug(f"Loaded model with {len(model.control_structure.nodes)} nodes, {len(model.control_structure.edges)} edges")
        return model
    
    # Helper methods for STPA component serialization
    
    @staticmethod
    def _loss_to_dict(loss: Loss) -> Dict[str, Any]:
        """Convert Loss object to dictionary"""
        return {
            'description': loss.description,
            'severity': loss.severity,
            'rationale': loss.rationale
        }
    
    @staticmethod
    def _hazard_to_dict(hazard: Hazard) -> Dict[str, Any]:
        """Convert Hazard object to dictionary"""
        return {
            'description': hazard.description,
            'severity': hazard.severity,
            'rationale': hazard.rationale,
            'related_losses': hazard.related_losses,
            'condition': {'description': hazard.condition.description} if hazard.condition else None
        }
    
    @staticmethod
    def _uca_to_dict(uca: UnsafeControlAction) -> Dict[str, Any]:
        """Convert UnsafeControlAction object to dictionary"""
        return {
            'id': uca.id,
            'control_action': uca.control_action,
            'context': uca.context,
            'category': uca.category,
            'hazard_links': uca.hazard_links,
            'rationale': uca.rationale,
            'severity': uca.severity,
            'likelihood': uca.likelihood
        }
    
    @staticmethod
    def _uca_context_to_dict(ctx: 'UCAContext') -> Dict[str, Any]:
        """Convert UCAContext object to dictionary"""
        return {
            'id': ctx.id,
            'name': ctx.name,
            'description': ctx.description,
            'conditions': ctx.conditions
        }
    
    @staticmethod
    def _scenario_to_dict(scenario: 'LossScenario') -> Dict[str, Any]:
        """Convert LossScenario object to dictionary"""
        return {
            'id': scenario.id,
            'name': scenario.name,
            'description': scenario.description,
            'related_uca_ids': scenario.related_uca_ids
        }
    
    @staticmethod
    def _document_to_dict(document: Document) -> Dict[str, Any]:
        """Convert Document object to dictionary for JSON serialization"""
        return {
            'filename': document.filename,
            'original_name': document.original_name,
            'file_type': document.file_type,
            'file_size': document.file_size,
            'upload_date': document.upload_date,
            'description': document.description
        }
