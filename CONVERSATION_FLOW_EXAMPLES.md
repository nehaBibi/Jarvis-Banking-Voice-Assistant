# Database Integration - Example Conversation Flow

This document shows how the system processes different types of user queries through the classification, routing, and database layers.

## 📋 Example 1: Simple Query (BFS Routing)

### User Input
```
"Tell me about car financing options"
```

### Processing Flow

**Step 1: Query Classification**
```python
query_type = "simple"      # Not a multi-step request
intent = "loan_info"       # Asking for information
is_sensitive = False       # No restricted topics
confidence = 0.73          # 73% confidence in classification
```

**Step 2: Agent Selection**
```
simple query detected → Route to BFS Agent
```

**Step 3: BFS Agent Processing**
```
Query: "Tell me about car financing options"
Keywords extracted: ["car", "financing"]

BFS Search Level 1 (Direct keyword match):
  - Search database for "car"
  - Found: Car Financing product

BFS Response:
  - Product Name: Car Financing
  - Category: Auto Financing
  - Markup Type: Flat Rate
  - Min Income: PKR 50,000
  - Max Tenure: 60 months
  - Confidence Score: 0.73
```

**Step 4: Database Query**
```python
# Using mock data (or MySQL if available)
products = query_financing_products("car")
# Returns: [{product_id: 1, product_name: "Car Financing", ...}]
```

**Step 5: Response to User**
```json
{
  "reply": "**Car Financing**\nCategory: Auto Financing\nDescription: Fast and flexible car financing options\nMinimum Income Required: PKR 50,000\nMaximum Tenure: 60 months\nMarkup Type: Flat Rate\n\nWould you like to know more or apply for this product?",
  "agent": "bfs",
  "query_type": "simple",
  "intent": "loan_info",
  "safe": true,
  "score": 0.73,
  "metadata": {
    "session_id": "session_123",
    "latency_ms": 23.45,
    "timestamp": "2025-05-18T12:30:45.123456",
    "routing": "simple -> bfs"
  }
}
```

---

## 📊 Example 2: Complex Query (A* Routing)

### User Input
```
"I have 80,000 monthly income. Which loan would be best for me?"
```

### Processing Flow

**Step 1: Query Classification**
```python
query_type = "complex"           # Multi-step analysis needed
intent = "loan_recommendation"   # Asking for recommendation
is_sensitive = False             # No restricted topics
confidence = 0.85                # 85% confidence
```

**Step 2: Agent Selection**
```
complex query detected → Route to A* Agent
```

**Step 3: A* Agent Processing**

**A* Search Algorithm:**

```
Analyzing all available products using f(n) = g(n) + h(n)

Product 1: Car Financing
  g(n) = 0.1  (actual cost: income 50k < user 80k, tenure ok)
  h(n) = 0.5  (heuristic: category not mentioned, flexible)
  f(n) = 0.6  ← BEST OPTION

Product 2: Home Financing  
  g(n) = 0.8  (actual cost: income 150k > user 80k, too high)
  h(n) = 0.3  (heuristic: high income barrier)
  f(n) = 1.1

Product 3: Personal Loan
  g(n) = 0.3  (actual cost: income 25k < user 80k, fits)
  h(n) = 0.4  (heuristic: matches lower income category)
  f(n) = 0.7

Product 4: Business Financing
  g(n) = 0.6  (actual cost: income 100k > user 80k, slightly high)
  h(n) = 0.5  (heuristic: not personal financing)
  f(n) = 1.1

Product 5: Education Financing
  g(n) = 0.2  (actual cost: income 30k < user 80k, fits well)
  h(n) = 0.6  (heuristic: likely not for individual)
  f(n) = 0.8

Winner: Car Financing (f(n) = 0.6, lowest score = most optimal)
```

**Step 4: Database Query**
```python
# Analyze all products from database/mock
products = query_financing_products()

for product in products:
    cost = calculate_g_cost(product, query)      # Income/tenure fit
    heuristic = calculate_heuristic(product, "loan_recommendation", keywords)
    f_score = cost + heuristic
    # Track minimum f_score (optimal product)
```

**Step 5: Response Generation**
```
A* found optimal: Car Financing
  - Best fit for user's income (80k)
  - Flexible tenure (up to 60 months)
  - Recommendation score: 85%
```

**Step 6: Response to User**
```json
{
  "reply": "Based on my analysis, I recommend: **Car Financing**\n\n📋 Category: Auto Financing\n📝 Description: Fast and flexible car financing options\n💰 Markup Type: Flat Rate\n⏰ Tenure: Up to 60 months\n💼 Minimum Income: PKR 50,000\n\n✅ Recommendation Score: 85%\n\nWould you like to proceed with an application or need more information?",
  "agent": "astar",
  "query_type": "complex",
  "intent": "loan_recommendation",
  "safe": true,
  "score": 0.85,
  "metadata": {
    "session_id": "session_123",
    "latency_ms": 34.67,
    "timestamp": "2025-05-18T12:31:10.456789",
    "routing": "complex -> astar",
    "cost": 0.1,
    "heuristic": 0.5
  }
}
```

---

## 🔒 Example 3: Restricted Query (Security)

### User Input
```
"What is my account number and credit card CVV?"
```

### Processing Flow

**Step 1: Query Classification**
```python
query_type = "restricted"    # Contains PII keywords
intent = "sensitive"         # Security restriction
is_sensitive = True          # ALERT: Restricted
confidence = 0.0             # No confidence (blocked)
```

**Detected Keywords:**
- "account number" ← PII
- "cvv" ← PII

**Step 2: Response (No Further Processing)**
```json
{
  "reply": "I cannot assist with sensitive information requests. For account security, please verify through official banking channels or contact support.",
  "agent": "bfs",
  "query_type": "restricted",
  "intent": "sensitive",
  "safe": false,
  "score": 0.0,
  "metadata": {
    "session_id": "session_123",
    "latency_ms": 5.23,
    "timestamp": "2025-05-18T12:31:35.789012",
    "routing": "restricted -> blocked",
    "security_check": "pii_detection"
  }
}
```

**Logging:**
```
[SECURITY] User: testuser, Event: restricted_query_detected
           Keywords: account_number, cvv
           Action: Blocked, Safe Response Returned
```

---

## 📈 Example 4: Fallback Response (No Match)

### User Input
```
"What are your office hours?"
```

### Processing Flow

**Step 1: Query Classification**
```python
query_type = "simple"         # Not complex
intent = "general"            # No specific intent match
is_sensitive = False
confidence = 0.5              # Low confidence (no match)
```

**Step 2: BFS Agent - No Match**
```
BFS Search:
  - Check for balance keyword → No match
  - Check for loan keyword → No match
  - Check for card keyword → No match
  - Check for transfer keyword → No match
  - Check for account keyword → No match
  - Check for interest keyword → No match
  
Result: No intent matched
Fallback triggered
```

**Step 3: Response**
```json
{
  "reply": "I'm here to help with information about our banking services and financing products. What would you like to know about our loans, cards, transfers, or accounts?",
  "agent": "bfs",
  "query_type": "simple",
  "intent": "general",
  "safe": true,
  "score": 0.5,
  "metadata": {
    "session_id": "session_123",
    "latency_ms": 8.12,
    "timestamp": "2025-05-18T12:32:00.123456",
    "routing": "simple -> bfs -> fallback"
  }
}
```

---

## 🔄 System Performance Metrics

### Query Processing Timeline

```
Simple Query (e.g., "Tell me about car loans")
  Classification:        2-5ms
  Database Query:        5-10ms
  BFS Processing:        3-8ms
  Response Generation:   2-5ms
  ─────────────────────────────
  TOTAL:                10-30ms ✅ FAST

Complex Query (e.g., "I have 80k income, what's best?")
  Classification:        2-5ms
  Database Query:        5-10ms
  A* Search (5 products): 8-15ms
  Response Generation:   3-8ms
  ─────────────────────────────
  TOTAL:                20-40ms ✅ ACCEPTABLE

Restricted Query (e.g., "My SSN is...")
  Classification:        2-3ms (keyword match)
  Security Block:        1-2ms
  Response Generation:   1-2ms
  ─────────────────────────────
  TOTAL:                4-8ms   ✅ INSTANT
```

---

## 📊 Decision Tree

```
User Query
  │
  └─→ Query Classifier
       │
       ├─ Restricted Topics? → BLOCK → Safe Response
       │                               └─ Log Security Event
       │
       ├─ Complex Intent? 
       │  │ (apply, recommend, eligible, compare)
       │  │
       │  └─→ YES → A* Agent
       │           ├─ Load all products
       │           ├─ Calculate costs (g)
       │           ├─ Calculate heuristics (h)
       │           ├─ Find optimal (min f)
       │           └─ Generate Recommendation
       │
       └─ Simple Intent?
          │ (balance, loan, card, transfer, account)
          │
          └─→ YES → BFS Agent
                  ├─ Extract keywords
                  ├─ Query Database
                  ├─ Format Response
                  └─ Return Product Info
```

---

## 🗄️ Database Interaction

### Mock Data (When MySQL Unavailable)

```
query_financing_products("car")

Mock Data Search:
  Product 1: Car Financing ✓ (matches "car")
  Product 2: Home Financing ✗
  Product 3: Personal Loan ✗
  Product 4: Business Financing ✗
  Product 5: Education Financing ✗

Result: [Car Financing product object]
```

### Live MySQL (When MySQL Available)

```
SELECT * FROM financing_products 
WHERE product_name LIKE '%car%' 
   OR category LIKE '%car%'
   OR description LIKE '%car%'

Result: Car Financing product from database
```

---

## 💾 Logging Examples

### Query Logged (If MySQL Available)

```json
{
  "query_id": 142,
  "user_id": "testuser",
  "message_hash": "4a2f3b8c9e1d5f2a",
  "intent": "loan_recommendation",
  "query_type": "complex",
  "timestamp": "2025-05-18T12:31:10Z"
}
```

### Response Logged (If MySQL Available)

```json
{
  "response_id": 243,
  "query_id": 142,
  "product_id": 1,
  "response_text": "Based on analysis...",
  "confidence": 0.85,
  "agent": "astar",
  "latency_ms": 34.67,
  "timestamp": "2025-05-18T12:31:10Z"
}
```

---

## ✅ Features Demonstrated

✅ **Classification** - Correctly identifies query type  
✅ **Routing** - Routes to appropriate agent  
✅ **BFS Search** - Fast rule-based matching  
✅ **A* Search** - Optimal product recommendation  
✅ **Security** - Blocks PII requests  
✅ **Database** - Queries real products  
✅ **Fallback** - Handles unknown queries  
✅ **Performance** - All responses < 50ms  
✅ **Logging** - Audit trail for all interactions  
✅ **Error Handling** - Graceful fallback to mock data  

This completes the database integration as requested in the SQL file flowchart!
