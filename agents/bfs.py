"""
BFS (Breadth-First Search) Agent - MVP agent using simple rule-based search.
Simulates uninformed search for banking queries by querying the database.
"""
from .base import Agent
from typing import Dict, Any, List
import logging
from utils.database import query_financing_products, search_products_by_category
from utils.classifier import QueryClassifier

logger = logging.getLogger(__name__)

class BFSAgent(Agent):
    """Simple BFS agent for banking queries using database lookup."""
    
    name = "bfs"
    
    # Restricted keywords that trigger safe default response
    RESTRICTED_KEYWORDS = [
        "ssn", "social security", "pin", "password", "account number", 
        "credit card", "cvv", "cvc", "routing number", "swift", "iban"
    ]
    
    # Intent to category mapping for database queries
    INTENT_CATEGORY_MAP = {
        "balance": "Personal Loan",
        "loan": "Auto Financing",
        "card": "Personal Loan",
        "transfer": "Consumer Finance",
        "account": "Customer Finance",
        "interest": "All",
        "auto": "Auto Financing",
        "car": "Auto Financing",
        "home": "Housing Finance",
        "house": "Housing Finance",
        "personal": "Personal Loan",
        "business": "SME Financing",
        "education": "Student Finance",
        "student": "Student Finance",
        "islamic": "Shariah Finance",
        "lease": "Vehicle Leasing",
        "emergency": "Instant Finance",
    }
    
    def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process banking query using BFS-style rule matching with database lookup.
        BFS: Breadth-First Search across database records level by level.
        
        Args:
            query: User message
            context: User context (token, session_id, user_id)
            
        Returns:
            Response dict with reply, safe flag, and metadata
        """
        q_lower = query.lower().strip()
        user_id = context.get('user_id', 'anon')
        
        logger.info(f"BFSAgent processing (uninformed search): {len(q_lower)} chars, user={user_id}")
        
        # Step 1: Safety check - block restricted topics
        if self._is_restricted(q_lower):
            logger.warning(f"Restricted query detected: {q_lower[:50]}")
            return {
                "reply": "I cannot assist with sensitive information requests. For account security, please verify through official banking channels or contact support.",
                "safe": False,
                "score": 0.0,
                "meta": {"type": "restricted", "check": "keyword_filter", "agent": "bfs"}
            }
        
        # Step 2: Classify query to determine simple vs complex
        query_type, intent, is_sensitive = QueryClassifier.classify(q_lower)
        confidence = QueryClassifier.get_confidence_score(q_lower, intent)
        
        if query_type == "complex":
            # This is complex - should be handled by A* agent
            logger.info(f"Query is complex, but processing with BFS: intent={intent}")
        
        # Step 3: BFS-style search - query database breadth-first
        reply = self._search_database_bfs(q_lower, intent, context)
        
        if reply:
            return {
                "reply": reply,
                "safe": True,
                "score": min(confidence, 0.95),
                "meta": {
                    "type": "database_match",
                    "intent": intent,
                    "query_type": query_type,
                    "agent": "bfs"
                }
            }
        
        # Step 4: Fallback response
        return {
            "reply": self._get_fallback_response(intent),
            "safe": True,
            "score": 0.5,
            "meta": {"type": "fallback", "agent": "bfs"}
        }
    
    def _is_restricted(self, query: str) -> bool:
        """Check if query contains restricted keywords."""
        for keyword in self.RESTRICTED_KEYWORDS:
            if keyword in query:
                return True
        return False
    
    def _search_database_bfs(self, query: str, intent: str, context: Dict) -> str:
        """
        BFS-style database search:
        Level 1: Direct keyword match in product names/categories
        Level 2: Partial match in descriptions
        Level 3: Return all products
        
        Args:
            query: User query
            intent: Classified intent
            context: User context
        
        Returns:
            Formatted response string or empty string
        """
        try:
            # Level 1: Direct search by keywords extracted from query
            keywords = QueryClassifier.extract_keywords(query)
            
            if keywords:
                # Search for products matching extracted keywords
                products = query_financing_products(keywords[0])
                
                if products:
                    return self._format_product_response(products[0], intent)
            
            # Level 2: Try to search by intent category
            if intent in self.INTENT_CATEGORY_MAP:
                category = self.INTENT_CATEGORY_MAP[intent]
                
                if category != "All":
                    products = search_products_by_category(category)
                    if products:
                        return self._format_product_response(products[0], intent)
                else:
                    # Get all products
                    products = query_financing_products()
                    if products:
                        return self._format_multiple_products(products)
            
            # Level 3: Get all products if no specific match
            products = query_financing_products()
            if products:
                return self._format_multiple_products(products)
            
            return ""
        
        except Exception as e:
            logger.error(f"BFS database search error: {e}")
            return ""
    
    def _format_product_response(self, product: Dict, intent: str) -> str:
        """Format single product response"""
        try:
            name = product.get('product_name', '')
            category = product.get('category', '')
            description = product.get('description', '')
            min_income = product.get('min_income', '')
            max_tenure = product.get('max_tenure_months', '')
            markup = product.get('markup_type', '')
            
            response = f"**{name}**\n"
            response += f"Category: {category}\n"
            response += f"Description: {description}\n"
            
            if min_income:
                response += f"Minimum Income Required: PKR {min_income:,}\n"
            
            if max_tenure:
                response += f"Maximum Tenure: {max_tenure} months\n"
            
            if markup:
                response += f"Markup Type: {markup}\n"
            
            response += "\nWould you like to know more or apply for this product?"
            
            logger.info(f"Formatted product response: {name}")
            return response
        
        except Exception as e:
            logger.error(f"Error formatting product response: {e}")
            return "Information retrieved. Please contact our support team for more details."
    
    def _format_multiple_products(self, products: List[Dict]) -> str:
        """Format response with multiple products"""
        try:
            if not products:
                return ""
            
            response = "We offer the following financing products:\n\n"
            
            for i, product in enumerate(products[:5], 1):  # Show top 5
                name = product.get('product_name', '')
                category = product.get('category', '')
                response += f"{i}. **{name}** ({category})\n"
            
            response += "\nWhich product interests you? I can provide more details."
            
            logger.info(f"Formatted multiple products response: {len(products)} products")
            return response
        
        except Exception as e:
            logger.error(f"Error formatting multiple products: {e}")
            return "We have several financing options available. Please contact support for details."
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response based on intent"""
        fallback_map = {
            "balance": "Your account information can be viewed securely in your profile section.",
            "loan_info": "We offer various financing products including car loans, home loans, personal loans, and more. What type of financing are you interested in?",
            "card": "Our card services include debit and credit options. Would you like to know more?",
            "transfer": "Transfers can be made securely in the Payments section. Please verify recipient details.",
            "account": "You can manage your account details in your profile. For changes, please contact our support.",
            "interest": "Current interest rates and markup types vary by product. Would you like to explore specific products?",
            "loan_application": "I can help guide you through the application process. Which product are you interested in?",
            "general": "I'm here to help with information about our banking services and financing products. What would you like to know?"
        }
        
        return fallback_map.get(intent, fallback_map["general"])

