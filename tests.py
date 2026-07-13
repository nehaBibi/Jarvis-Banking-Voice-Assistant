"""
Simple test suite for Jarvis Banking AI - MVP
Run with: python -m pytest tests.py -v
Or manually: python tests.py
"""
import sys
import time
from agents.bfs import BFSAgent
from agents import AgentManager
from utils.security import SecurityValidator


def test_bfs_agent_balance_intent():
    """Test BFS agent matches balance intent."""
    agent = BFSAgent()
    response = agent.handle("What's my balance?", {"user_id": "test"})
    
    assert response["safe"] == True, "Should be safe"
    assert "balance" in response["reply"].lower(), "Should mention balance"
    assert response["score"] >= 0.5, "Should have confidence score"
    print("✅ test_bfs_agent_balance_intent PASSED")


def test_bfs_agent_restricted_topic():
    """Test BFS agent detects restricted topics."""
    agent = BFSAgent()
    response = agent.handle("My SSN is 123-45-6789", {"user_id": "test"})
    
    assert response["safe"] == False, "Should mark as unsafe"
    assert "sensitive" in response["reply"].lower(), "Should warn about sensitive info"
    print("✅ test_bfs_agent_restricted_topic PASSED")


def test_bfs_agent_fallback():
    """Test BFS agent fallback response."""
    agent = BFSAgent()
    response = agent.handle("Tell me a joke", {"user_id": "test"})
    
    assert response["safe"] == True, "Should be safe"
    assert "help" in response["reply"].lower(), "Should offer to help"
    print("✅ test_bfs_agent_fallback PASSED")


def test_agent_manager_registration():
    """Test agent manager can register and retrieve agents."""
    manager = AgentManager()
    
    # Check defaults registered
    agents = manager.list_agents()
    assert "bfs" in agents, "Should have BFS agent"
    assert "astar" in agents, "Should have A* agent"
    
    # Get agent instance
    agent = manager.get_agent("bfs")
    assert agent.name == "bfs", "Agent should have correct name"
    
    print("✅ test_agent_manager_registration PASSED")


def test_agent_manager_switching():
    """Test agent manager can switch default agent."""
    manager = AgentManager()
    
    manager.set_default("astar")
    agent = manager.get_agent()
    assert agent.name == "astar", "Should switch to astar"
    
    manager.set_default("bfs")
    agent = manager.get_agent()
    assert agent.name == "bfs", "Should switch back to bfs"
    
    print("✅ test_agent_manager_switching PASSED")


def test_security_validate_message():
    """Test input validation for messages."""
    # Valid message
    is_valid, msg = SecurityValidator.validate_message("Hello bot")
    assert is_valid == True, "Should accept valid message"
    
    # Empty message
    is_valid, msg = SecurityValidator.validate_message("")
    assert is_valid == False, "Should reject empty message"
    
    # Too long message
    long_msg = "a" * 3000
    is_valid, msg = SecurityValidator.validate_message(long_msg)
    assert is_valid == False, "Should reject too-long message"
    
    print("✅ test_security_validate_message PASSED")


def test_security_validate_username():
    """Test username validation."""
    # Valid username
    is_valid, msg = SecurityValidator.validate_username("demo123")
    assert is_valid == True, "Should accept valid username"
    
    # Too short
    is_valid, msg = SecurityValidator.validate_username("ab")
    assert is_valid == False, "Should reject too-short username"
    
    # Invalid characters
    is_valid, msg = SecurityValidator.validate_username("demo@123")
    assert is_valid == False, "Should reject special characters"
    
    print("✅ test_security_validate_username PASSED")


def test_security_sanitize_message():
    """Test message sanitization."""
    # Control characters
    msg = "Hello\x00World\x1bTest"
    sanitized = SecurityValidator.sanitize_message(msg)
    assert "\x00" not in sanitized, "Should remove null chars"
    assert "\x1b" not in sanitized, "Should remove escape chars"
    
    # Newlines preserved
    msg = "Line 1\nLine 2"
    sanitized = SecurityValidator.sanitize_message(msg)
    assert "\n" in sanitized, "Should preserve newlines"
    
    print("✅ test_security_sanitize_message PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("JARVIS BANKING AI - MVP TEST SUITE")
    print("="*50 + "\n")
    
    tests = [
        test_bfs_agent_balance_intent,
        test_bfs_agent_restricted_topic,
        test_bfs_agent_fallback,
        test_agent_manager_registration,
        test_agent_manager_switching,
        test_security_validate_message,
        test_security_validate_username,
        test_security_sanitize_message,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
