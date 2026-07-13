#!/usr/bin/env python3
"""
Integration Test - Verify frontend/backend communication
Run this after starting the backend: python app.py
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("1️⃣  Testing /health endpoint...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok"
    print(f"   ✅ Health check passed: {data['status']}")
    return data

def test_auth():
    """Test authentication"""
    print("\n2️⃣  Testing /auth endpoint...")
    resp = requests.post(
        f"{BASE_URL}/auth",
        json={"username": "testuser", "password": "testpass"},
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Testuser"  # Capitalized
    token = data["access_token"]
    print(f"   ✅ Login successful: Got token {token[:16]}...")
    print(f"   ✅ User: {data['user']}")
    return token

def test_chat(token):
    """Test chat endpoint with valid token"""
    print("\n3️⃣  Testing /chat endpoint (valid intent)...")
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What is my balance?",
            "session_id": "test_session",
            "agent": "bfs"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "reply" in data
    assert data["agent"] == "bfs"
    assert data["safe"] == True
    print(f"   ✅ Chat response: {data['reply'][:60]}...")
    print(f"   ✅ Agent: {data['agent']}, Safe: {data['safe']}")
    print(f"   ✅ Latency: {data['metadata']['latency_ms']:.2f}ms")
    return data

def test_restricted_topic(token):
    """Test restricted topic detection"""
    print("\n4️⃣  Testing /chat endpoint (restricted topic)...")
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "My SSN is 123-45-6789",
            "session_id": "test_session"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] == False
    print(f"   ✅ Restricted topic detected: {data['reply'][:60]}...")
    print(f"   ✅ Safe flag correctly set to: {data['safe']}")

def test_invalid_token():
    """Test chat with invalid token"""
    print("\n5️⃣  Testing /chat with invalid token...")
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hello"},
        headers={
            "Authorization": "Bearer invalid_token_xyz",
            "Content-Type": "application/json"
        }
    )
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("   ✅ Correctly rejected invalid token (401)")

def test_missing_auth():
    """Test chat without auth header"""
    print("\n6️⃣  Testing /chat without auth header...")
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hello"},
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("   ✅ Correctly rejected missing auth header (401)")

def test_agent_config(token):
    """Test agent config endpoint"""
    print("\n7️⃣  Testing /agent/config endpoint...")
    resp = requests.get(
        f"{BASE_URL}/agent/config",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "bfs" in data["available_agents"]
    print(f"   ✅ Available agents: {data['available_agents']}")
    print(f"   ✅ Default agent: {data['default_agent']}")

def main():
    print("=" * 60)
    print("JARVIS BANKING AI - INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Test basic health
        health = test_health()
        
        # Test auth
        token = test_auth()
        
        # Test chat with valid intent
        chat_resp = test_chat(token)
        
        # Test restricted topics
        test_restricted_topic(token)
        
        # Test security
        test_invalid_token()
        test_missing_auth()
        
        # Test agent config
        test_agent_config(token)
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  ✅ Backend is running")
        print("  ✅ Authentication works")
        print("  ✅ Chat endpoint functional")
        print("  ✅ Security checks active")
        print("  ✅ Agent system working")
        print("\n🚀 Frontend/Backend integration is ready!")
        print("   Open index.html and try logging in with any credentials.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\n⚠️  Make sure backend is running:")
        print("   python app.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  Backend might not be running. Start it with:")
        print("   python app.py")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
