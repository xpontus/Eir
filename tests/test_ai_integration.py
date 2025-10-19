"""
Tests for AI integration functionality
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_integration import get_ai_manager, test_ai_integration, OllamaAIManager, AIConfig


class TestAIIntegration(unittest.TestCase):
    """Test AI integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ai_manager = get_ai_manager()
        
    def test_ai_config_creation(self):
        """Test AI configuration creation"""
        config = AIConfig()
        self.assertEqual(config.base_url, "http://localhost:11434")
        self.assertEqual(config.model, "llama3:latest")
        self.assertIsInstance(config.temperature, float)
        self.assertIsInstance(config.max_tokens, int)
        
    def test_ai_manager_creation(self):
        """Test AI manager creation"""
        self.assertIsInstance(self.ai_manager, OllamaAIManager)
        self.assertIsNotNone(self.ai_manager.config)
        self.assertIsNotNone(self.ai_manager.system_prompt)
        
    def test_connection_test(self):
        """Test AI connection functionality"""
        # Note: This test may fail if Ollama is not running
        try:
            connection_ok = self.ai_manager.test_connection()
            self.assertIsInstance(connection_ok, bool)
            if connection_ok:
                print("✅ Ollama connection successful")
            else:
                print("⚠️ Ollama connection failed - ensure Ollama is running")
        except Exception as e:
            print(f"⚠️ Connection test exception: {e}")
            # Don't fail the test if Ollama is not available
            pass
            
    def test_fallback_responses(self):
        """Test fallback responses when AI is unavailable"""
        # Test with invalid configuration to trigger fallback
        invalid_config = AIConfig(base_url="http://invalid:9999")
        invalid_manager = OllamaAIManager(invalid_config)
        
        # Test joke request
        response = invalid_manager.generate_response("tell me a joke")
        self.assertIn("STPA", response)
        
        # Test help request
        response = invalid_manager.generate_response("help me with STPA")
        self.assertIn("STPA", response)
        self.assertIn("methodology", response.lower())
        
    def test_context_formatting(self):
        """Test context information formatting"""
        context = {
            "current_tab": "Control Structure",
            "model_info": {
                "node_count": 5,
                "edge_count": 4,
                "losses_count": 2,
                "hazards_count": 3
            },
            "selected_items": ["Node1", "Edge2"]
        }
        
        formatted = self.ai_manager._format_context_info(context)
        self.assertIn("Control Structure", formatted)
        self.assertIn("5 nodes", formatted)
        self.assertIn("4 edges", formatted)
        self.assertIn("Node1", formatted)
        
    def test_conversation_history_management(self):
        """Test conversation history management"""
        # Clear history
        self.ai_manager.clear_conversation()
        self.assertEqual(len(self.ai_manager.conversation_history), 0)
        
        # Add some mock history
        self.ai_manager.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "What is STPA?"},
            {"role": "assistant", "content": "STPA is Systems-Theoretic Process Analysis..."}
        ]
        
        # Test summary generation
        summary = self.ai_manager.get_conversation_summary()
        self.assertIn("User: Hello", summary)
        self.assertIn("Assistant: Hi there!", summary)
        
        # Test history loading
        self.ai_manager.clear_conversation()
        self.ai_manager.load_conversation_history(summary)
        self.assertEqual(len(self.ai_manager.conversation_history), 4)
        
    def test_system_prompt_content(self):
        """Test system prompt contains required content"""
        prompt = self.ai_manager.system_prompt
        self.assertIn("STPA", prompt)
        self.assertIn("Systems-Theoretic Process Analysis", prompt)
        self.assertIn("control structures", prompt)
        self.assertIn("hazards", prompt)
        self.assertIn("safety", prompt)
        
    def test_ai_integration_test_function(self):
        """Test the AI integration test function"""
        result = test_ai_integration()
        
        # Check return format
        self.assertIsInstance(result, dict)
        self.assertIn("connection_ok", result)
        self.assertIn("response_ok", result)
        self.assertIn("model", result)
        self.assertIn("base_url", result)
        self.assertIn("test_response", result)
        
        # Check data types
        self.assertIsInstance(result["connection_ok"], bool)
        self.assertIsInstance(result["response_ok"], bool)
        self.assertIsInstance(result["model"], str)
        self.assertIsInstance(result["base_url"], str)
        self.assertIsInstance(result["test_response"], str)


class TestAIIntegrationLive(unittest.TestCase):
    """Live tests that require Ollama to be running"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ai_manager = get_ai_manager()
        
    def test_real_ai_response(self):
        """Test real AI response generation (requires Ollama)"""
        # Skip if Ollama is not available
        if not self.ai_manager.test_connection():
            self.skipTest("Ollama not available")
            
        # Test simple question
        response = self.ai_manager.generate_response("What is a control action in STPA?")
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 10)
        self.assertTrue(any(word in response.lower() for word in ["control", "action", "stpa"]))
        
    def test_context_aware_response(self):
        """Test context-aware AI responses (requires Ollama)"""
        if not self.ai_manager.test_connection():
            self.skipTest("Ollama not available")
            
        context = {
            "current_tab": "Losses & Hazards",
            "model_info": {
                "losses_count": 0,
                "hazards_count": 0
            }
        }
        
        response = self.ai_manager.generate_response(
            "I'm just starting my analysis. What should I do first?",
            context
        )
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 20)
        
    def test_conversation_flow(self):
        """Test conversation flow with history (requires Ollama)"""
        if not self.ai_manager.test_connection():
            self.skipTest("Ollama not available")
            
        # Clear conversation
        self.ai_manager.clear_conversation()
        
        # First message
        response1 = self.ai_manager.generate_response("What is STPA?")
        self.assertGreater(len(response1), 10)
        
        # Follow-up message that should reference context
        response2 = self.ai_manager.generate_response("Can you give me an example?")
        self.assertGreater(len(response2), 10)
        
        # Check that conversation history was maintained
        self.assertGreaterEqual(len(self.ai_manager.conversation_history), 4)


if __name__ == '__main__':
    # Run tests with different verbosity based on Ollama availability
    ai_manager = get_ai_manager()
    if ai_manager.test_connection():
        print("🤖 Ollama detected - running full AI tests")
        unittest.main(verbosity=2)
    else:
        print("⚠️ Ollama not available - running basic tests only")
        # Run only basic tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAIIntegration)
        unittest.TextTestRunner(verbosity=2).run(suite)
