"""
AI Integration for Eir using Ollama.
"""

import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

from core.constants import APP_NAME

# Get logger for this module  
logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """Configuration for AI integration"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3:latest"
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 30
    
    @classmethod
    def from_config(cls) -> 'AIConfig':
        """Create AI config from application configuration"""
        try:
            from core.config import get_config
            config = get_config()
            return cls(
                base_url=config.ai.base_url,
                model=config.ai.model,
                temperature=config.ai.temperature,
                max_tokens=config.ai.max_tokens,
                timeout=config.ai.timeout
            )
        except (ImportError, AttributeError):
            logger.warning("Using default AI configuration - config system not available")
            return cls()


class OllamaAIManager:
    """Manages AI interactions using Ollama local models"""
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig.from_config()
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._build_system_prompt()
        logger.info(f"Initialized AI manager with model: {self.config.model}")
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for STPA methodology expertise"""
        return f"""You are an expert AI assistant for the {APP_NAME} STPA (Systems-Theoretic Process Analysis) tool. You have deep knowledge of:

1. STPA Methodology: You understand all aspects of STPA including control structures, hazards, losses, unsafe control actions (UCAs), and loss scenarios.

2. Safety Engineering: You're knowledgeable about systems safety, risk analysis, and safety-critical systems.

3. Tool Usage: You can help users with the {APP_NAME} tool features including:
   - Creating and editing control structures
   - Defining losses and hazards
   - Analyzing unsafe control actions
   - Building loss scenarios
   - Using the interactive graph editor
   - Understanding test results and performance metrics

4. Context Awareness: You understand the current tab context and can provide specific guidance based on what the user is working on.

Your responses should be:
- Helpful and educational about STPA methodology
- Specific to the tool context when relevant
- Professional but friendly
- Include practical examples when helpful
- Encourage best practices in safety analysis

If users ask for jokes, you can provide STPA-themed humor to keep things light while learning.

Always be ready to explain STPA concepts, guide methodology application, and help with tool usage."""

    def test_connection(self) -> bool:
        """Test if Ollama is accessible and the model is available"""
        try:
            logger.debug(f"Testing connection to {self.config.base_url}")
            # Test basic connectivity
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                logger.warning(f"Ollama API returned status {response.status_code}")
                return False
                
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            is_available = self.config.model in model_names
            
            if is_available:
                logger.info(f"AI model {self.config.model} is available")
            else:
                logger.warning(f"AI model {self.config.model} not found. Available: {model_names}")
            
            return is_available
            
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return False

    def generate_response(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate AI response using Ollama"""
        logger.debug(f"Generating AI response for input: {user_input[:50]}...")
        
        try:
            # Build the conversation context
            messages = self._build_conversation_context(user_input, context)
            
            # Make request to Ollama
            response = self._call_ollama(messages)
            
            if response:
                # Add to conversation history
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # Keep conversation history manageable
                if len(self.conversation_history) > 20:  # Keep last 10 exchanges
                    self.conversation_history = self.conversation_history[-20:]
                
                logger.debug(f"Generated AI response: {len(response)} characters")
                return response
            else:
                logger.warning("AI response was empty, using fallback")
                return self._get_fallback_response(user_input)
                
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._get_fallback_response(user_input)

    def _build_conversation_context(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Build conversation context for the AI model"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add context information if provided
        if context:
            context_info = self._format_context_info(context)
            if context_info:
                messages.append({"role": "system", "content": f"Current context: {context_info}"})
        
        # Add recent conversation history
        messages.extend(self.conversation_history[-10:])  # Last 5 exchanges
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages

    def _format_context_info(self, context: Dict[str, Any]) -> str:
        """Format context information for the AI"""
        context_parts = []
        
        if "current_tab" in context:
            context_parts.append(f"User is currently in the {context['current_tab']} tab")
            
        if "model_info" in context:
            model_info = context["model_info"]
            if "node_count" in model_info:
                context_parts.append(f"Model has {model_info['node_count']} nodes")
            if "edge_count" in model_info:
                context_parts.append(f"Model has {model_info['edge_count']} edges")
            if "losses_count" in model_info:
                context_parts.append(f"Model has {model_info['losses_count']} losses defined")
            if "hazards_count" in model_info:
                context_parts.append(f"Model has {model_info['hazards_count']} hazards defined")
                
        if "selected_items" in context:
            selected = context["selected_items"]
            if selected:
                context_parts.append(f"User has selected: {', '.join(selected)}")
                
        return "; ".join(context_parts)

    def _call_ollama(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Make the actual API call to Ollama"""
        try:
            # Prepare the request payload
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            # Make the request
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("AI request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Could not connect to Ollama")
            return None
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None

    def _get_fallback_response(self, user_input: str) -> str:
        """Provide fallback response when AI is unavailable"""
        user_lower = user_input.lower()
        
        # Check for common patterns
        if "joke" in user_lower:
            stpa_jokes = [
                "Why don't STPA analysts trust traditional fault trees? Because they know the real danger is in the interactions, not just the failures! 🌳",
                "What did the control action say to the process? 'I'm trying to help, but sometimes I'm unsafe!' 😅",
                "Why did the hazard break up with the loss? Because it realized it was just an enabling condition! 💔",
                "What's an STPA analyst's favorite type of music? Control loops! 🎵",
                "Why don't unsafe control actions ever win arguments? Because they always lead to losses! 🏆"
            ]
            import random
            return random.choice(stpa_jokes)
            
        elif any(word in user_lower for word in ["help", "how", "what", "explain"]):
            return """I'm here to help with STPA methodology and tool usage! However, I'm currently running in fallback mode. 
            
For the best experience, please ensure Ollama is running with the Llama3 model. You can:
- Ask about STPA concepts and methodology
- Get help with the tool features
- Request explanations of safety analysis techniques
- Ask for STPA-themed jokes to lighten the mood!

What specific aspect of STPA or the tool would you like to explore?"""
        
        else:
            return """I'd love to help you with STPA analysis! I'm currently in fallback mode, but I can still provide basic guidance.

Some things I can help with:
- STPA methodology questions
- Tool usage guidance  
- Safety analysis concepts
- Control structure modeling tips

What would you like to know about STPA or the Eir tool?"""

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history.clear()

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for saving"""
        if not self.conversation_history:
            return ""
            
        summary_parts = []
        for entry in self.conversation_history:
            role = entry["role"].title()
            content = entry["content"][:100] + "..." if len(entry["content"]) > 100 else entry["content"]
            summary_parts.append(f"{role}: {content}")
            
        return "\n".join(summary_parts)

    def load_conversation_history(self, history_text: str):
        """Load conversation history from saved text"""
        self.conversation_history.clear()
        
        if not history_text.strip():
            return
            
        try:
            lines = history_text.strip().split('\n')
            for line in lines:
                if ': ' in line:
                    role_part, content = line.split(': ', 1)
                    role = role_part.lower()
                    if role in ['user', 'assistant']:
                        self.conversation_history.append({"role": role, "content": content})
        except Exception as e:
            print(f"Failed to load conversation history: {e}")


# Global AI manager instance
_ai_manager = None

def get_ai_manager() -> OllamaAIManager:
    """Get the global AI manager instance"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = OllamaAIManager()
    return _ai_manager


def test_ai_integration() -> Dict[str, Any]:
    """Test AI integration and return status"""
    ai_manager = get_ai_manager()
    
    # Test connection
    connection_ok = ai_manager.test_connection()
    
    # Test simple query if connection is OK
    if connection_ok:
        try:
            test_response = ai_manager.generate_response("Hello, can you help with STPA?")
            response_ok = bool(test_response and len(test_response) > 10)
        except Exception as e:
            response_ok = False
            test_response = f"Error: {str(e)}"
    else:
        response_ok = False
        test_response = "Connection failed"
    
    return {
        "connection_ok": connection_ok,
        "response_ok": response_ok,
        "model": ai_manager.config.model,
        "base_url": ai_manager.config.base_url,
        "test_response": test_response[:200] + "..." if len(test_response) > 200 else test_response
    }
