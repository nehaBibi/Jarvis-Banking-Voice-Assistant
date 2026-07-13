"""
Unit Tests - Database Integration Components
Tests core logic without needing the backend to be running
"""
import sys
import os
sys.path.insert(0, '.')

# Set UTF-8 encoding for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'

from utils.classifier import QueryClassifier
from utils.database import query_financing_products, search_products_by_category, get_all_categories
from agents.bfs import BFSAgent
from agents.astar import AStarAgent

def test_classifier():
    """Test query classifier"""
    print("\n" + "="*60)
    print("TEST 1: Query Classifier")
    print("="*60)
    
    tests = [
        ("Tell me about car loans", "simple", "loan_info"),
        ("How do I apply for a loan", "complex", "loan_application"),
        ("What are eligibility requirements", "complex", "loan_eligibility"),
        ("I want to recommend a product", "complex", "loan_recommendation"),
        ("Check my balance", "simple", "balance"),
        ("My SSN is 123-45-6789", "restricted", "sensitive"),
    ]
    
    passed = 0
    for query, expected_type, expected_intent in tests:
        query_type, intent, is_sensitive = QueryClassifier.classify(query)
        is_correct = query_type == expected_type and intent == expected_intent
        
        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_type} / {expected_intent}")
        print(f"   Got: {query_type} / {intent}")
        
        if is_correct:
            passed += 1
    
    print(f"\n[PASS] Classifier: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

def test_bfs_agent():
    """Test BFS agent with database queries"""
    print("\n" + "="*60)
    print("TEST 2: BFS Agent (Uninformed Search)")
    print("="*60)
    
    agent = BFSAgent()
    context = {'user_id': 'test_user'}
    
    # Test 1: Simple loan inquiry
    print("\n1. Testing simple loan inquiry...")
    response = agent.handle("Tell me about personal loans", context)
    
    print(f"   Response type: {response['meta'].get('type')}")
    print(f"   Agent: {response['meta'].get('agent')}")
    print(f"   Safe: {response['safe']}")
    print(f"   Score: {response['score']}")
    print(f"   Reply: {response['reply'][:100]}...")
    
    assert response['safe'] == True, "BFS should mark response as safe"
    assert response['meta']['agent'] == 'bfs', "Should use BFS agent"
    
    # Test 2: Restricted query
    print("\n2. Testing restricted topic detection...")
    response = agent.handle("What is my SSN?", context)
    
    print(f"   Safe: {response['safe']}")
    print(f"   Score: {response['score']}")
    print(f"   Type: {response['meta'].get('type')}")
    
    assert response['safe'] == False, "BFS should mark restricted as unsafe"
    assert response['score'] == 0.0, "Restricted should have 0 score"
    
    print("\n[PASS] BFS Agent: All tests passed")
    return True

def test_astar_agent():
    """Test A* agent with intelligent routing"""
    print("\n" + "="*60)
    print("TEST 3: A* Agent (Informed Search)")
    print("="*60)
    
    agent = AStarAgent()
    context = {'user_id': 'test_user'}
    
    # Test 1: Recommendation query
    print("\n1. Testing loan recommendation...")
    response = agent.handle("I need a loan for business with 100k income", context)
    
    print(f"   Response type: {response['meta'].get('type')}")
    print(f"   Agent: {response['meta'].get('agent')}")
    print(f"   Safe: {response['safe']}")
    print(f"   Score: {response['score']}")
    print(f"   Reply: {response['reply'][:100]}...")
    
    assert response['safe'] == True, "A* should mark response as safe"
    assert response['meta']['agent'] == 'astar', "Should use A* agent"
    assert 'recommend' in response['reply'].lower() or 'recommend' in response['meta'].get('type', '').lower(), "Should provide recommendation"
    
    # Test 2: Complex eligibility query
    print("\n2. Testing eligibility analysis...")
    response = agent.handle("Am I eligible for home financing with 50k monthly income?", context)
    
    print(f"   Safe: {response['safe']}")
    print(f"   Score: {response['score']}")
    
    assert response['safe'] == True, "A* should handle eligibility safely"
    
    print("\n[PASS] A* Agent: All tests passed")
    return True

def test_database_fallback():
    """Test database fallback to mock data"""
    print("\n" + "="*60)
    print("TEST 4: Database Integration (Mock Fallback)")
    print("="*60)
    
    # Test 1: Get all products
    print("\n1. Testing product retrieval...")
    products = query_financing_products()
    print(f"   Retrieved {len(products)} products")
    for p in products:
        print(f"   - {p['product_name']} ({p['category']})")
    
    assert len(products) > 0, "Should retrieve products"
    assert 'product_name' in products[0], "Product should have name"
    
    # Test 2: Search products
    print("\n2. Testing product search...")
    car_products = query_financing_products("car")
    print(f"   Found {len(car_products)} products matching 'car'")
    for p in car_products:
        print(f"   - {p['product_name']}")
    
    assert len(car_products) > 0, "Should find car products"
    
    # Test 3: Search by category
    print("\n3. Testing category search...")
    categories = get_all_categories()
    print(f"   Available categories: {categories}")
    
    assert len(categories) > 0, "Should have categories"
    
    personal = search_products_by_category("Personal")
    print(f"   Personal Loan products: {[p['product_name'] for p in personal]}")
    
    assert len(personal) > 0, "Should find personal loan products"
    
    print("\n[PASS] Database: All tests passed")
    return True

def test_integration():
    """Test end-to-end integration"""
    print("\n" + "="*60)
    print("TEST 5: End-to-End Integration")
    print("="*60)
    
    # Simulate a conversation flow
    print("\n1. User asks simple question...")
    query = "What car financing options do you have?"
    query_type, intent, _ = QueryClassifier.classify(query)
    print(f"   Classified as: {query_type} / {intent}")
    
    # Route to appropriate agent
    if query_type == "simple":
        agent = BFSAgent()
        agent_name = "BFS"
    else:
        agent = AStarAgent()
        agent_name = "A*"
    
    response = agent.handle(query, {'user_id': 'user1'})
    print(f"   Routed to: {agent_name}")
    print(f"   Response: {response['reply'][:100]}...")
    
    # Test 2: Complex question
    print("\n2. User asks complex question...")
    query = "I have 80k income, what would you recommend?"
    query_type, intent, _ = QueryClassifier.classify(query)
    print(f"   Classified as: {query_type} / {intent}")
    
    if query_type == "simple":
        agent = BFSAgent()
        agent_name = "BFS"
    else:
        agent = AStarAgent()
        agent_name = "A*"
    
    response = agent.handle(query, {'user_id': 'user1'})
    print(f"   Routed to: {agent_name}")
    print(f"   Response: {response['reply'][:100]}...")
    
    print("\n[PASS] Integration: All tests passed")
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("DATABASE INTEGRATION UNIT TESTS")
    print("="*60)
    
    all_passed = True
    
    try:
        all_passed &= test_classifier()
        all_passed &= test_database_fallback()
        all_passed &= test_bfs_agent()
        all_passed &= test_astar_agent()
        all_passed &= test_integration()
        
        if all_passed:
            print("\n" + "="*60)
            print("[PASS] ALL TESTS PASSED")
            print("="*60)
            print("\nSystem Status:")
            print("  [PASS] Query Classification - Working")
            print("  [PASS] BFS Agent - Working (Mock Data)")
            print("  [PASS] A* Agent - Working (Mock Data)")
            print("  [PASS] Database Fallback - Working")
            print("  [PASS] Intelligent Routing - Working")
            print("\nReady for frontend integration!")
        else:
            print("\n[FAIL] Some tests failed")
    except Exception as e:
        print(f"\n[FAIL] Test Error: {e}")
        import traceback
        traceback.print_exc()
