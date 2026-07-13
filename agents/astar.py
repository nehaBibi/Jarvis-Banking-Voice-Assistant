"""
A* Search Agent - Informed heuristic search for complex banking queries.
Implements cost + heuristic-based search for multi-step banking tasks.
Finds the optimal financing product for user needs.
"""
from .base import Agent
from typing import Dict, Any, List
import logging
from utils.database import query_financing_products, get_all_categories
from utils.classifier import QueryClassifier

logger = logging.getLogger(__name__)

class AStarAgent(Agent):
    """
    A* Search agent for goal-directed banking queries.
    Uses cost (actual steps) + heuristic (estimated relevance to goal).
    
    Optimal for:
    - Loan applications
    - Eligibility checks
    - Product recommendations
    - Multi-step financing queries
    """
    
    name = "astar"
    
    def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        A* agent handler for complex queries.
        
        Args:
            query: User message
            context: User context
            
        Returns:
            Response dict with optimized product recommendation
        """
        q_lower = query.lower().strip()
        user_id = context.get('user_id', 'anon')
        
        logger.info(f"AStarAgent processing (informed search): {len(q_lower)} chars, user={user_id}")
        
        # Classify query
        query_type, intent, is_sensitive = QueryClassifier.classify(q_lower)
        confidence = QueryClassifier.get_confidence_score(q_lower, intent)
        
        if is_sensitive:
            return {
                "reply": "I cannot assist with sensitive information requests.",
                "safe": False,
                "score": 0.0,
                "meta": {"type": "restricted", "agent": "astar"}
            }
        
        # Use A* search to find optimal product
        best_product, cost, heuristic = self._a_star_search(q_lower, intent, context)
        
        if best_product:
            reply = self._generate_recommendation(best_product, intent, cost, heuristic)
            return {
                "reply": reply,
                "safe": True,
                "score": min(confidence, 0.95),
                "meta": {
                    "type": "a_star_recommendation",
                    "intent": intent,
                    "cost": cost,
                    "heuristic": heuristic,
                    "algorithm": "A*",
                    "agent": "astar"
                }
            }
        
        # Fallback
        return {
            "reply": self._get_fallback_response(),
            "safe": True,
            "score": 0.5,
            "meta": {"type": "fallback", "agent": "astar"}
        }
    
    def _a_star_search(self, query: str, intent: str, context: Dict) -> tuple:
        """
        A* Search Algorithm Implementation:
        f(n) = g(n) + h(n)
        where:
          g(n) = actual cost from start to node n (steps taken)
          h(n) = heuristic estimated cost from n to goal (relevance score)
        
        Args:
            query: User query
            intent: Extracted intent
            context: User context
        
        Returns:
            Tuple of (best_product, cost, heuristic_score)
        """
        try:
            # Get all financing products (open set)
            all_products = query_financing_products()
            
            if not all_products:
                logger.warning("No products found in database")
                return None, 0, 0
            
            # Extract goal from query (what user is looking for)
            keywords = QueryClassifier.extract_keywords(query)
            
            # A* search: evaluate all products with f(n) = g(n) + h(n)
            best_node = None
            best_f_score = float('inf')
            
            for product in all_products:
                # g(n): actual cost - distance from query requirements
                g_cost = self._calculate_g_cost(product, query)
                
                # h(n): heuristic - estimated relevance to intent
                h_score = self._calculate_heuristic(product, intent, keywords)
                
                # f(n) = g + h
                f_score = g_cost + h_score
                
                logger.debug(f"Product: {product['product_name']} - f={f_score:.2f} (g={g_cost:.2f}, h={h_score:.2f})")
                
                # Track best (lowest f score = most optimal)
                if f_score < best_f_score:
                    best_f_score = f_score
                    best_node = product
            
            if best_node:
                g_final = self._calculate_g_cost(best_node, query)
                h_final = self._calculate_heuristic(best_node, intent, keywords)
                logger.info(f"A* found optimal: {best_node['product_name']} with f={best_f_score:.2f}")
                return best_node, g_final, h_final
            
            return None, 0, 0
        
        except Exception as e:
            logger.error(f"A* search error: {e}")
            return None, 0, 0
    
    def _calculate_g_cost(self, product: Dict, query: str) -> float:
        """
        Calculate g(n): actual cost from start to node
        Lower cost = better match to user requirements
        
        Factors:
        - Income requirement match
        - Tenure match
        - Category relevance
        """
        cost = 0.0
        
        # Factor 1: Check if category appears in query
        if product['category'].lower() not in query.lower():
            cost += 0.5  # Penalty for category not mentioned
        else:
            cost -= 0.2  # Bonus for category match
        
        # Factor 2: Income flexibility
        min_income = product.get('min_income', 0)
        if min_income > 100000:
            cost += 0.3  # High income requirement adds cost
        elif min_income > 50000:
            cost += 0.1
        else:
            cost -= 0.1  # Lower income requirement is better
        
        # Factor 3: Tenure availability
        max_tenure = product.get('max_tenure_months', 0)
        if max_tenure < 24:
            cost += 0.4  # Short tenure adds cost
        elif max_tenure > 120:
            cost -= 0.1  # Longer tenure is more flexible
        
        return max(cost, 0.0)
    
    def _calculate_heuristic(self, product: Dict, intent: str, keywords: List[str]) -> float:
        """
        Calculate h(n): heuristic - estimated relevance to goal
        Lower heuristic = closer to goal (more relevant)
        
        Factors:
        - Intent match
        - Keyword overlap
        - Product description relevance
        """
        h_score = 1.0  # Base heuristic
        
        # Factor 1: Intent matching
        intent_keywords = {
            "loan_application": ["apply", "application"],
            "loan_eligibility": ["eligible", "qualify"],
            "loan_recommendation": ["recommend", "best", "suitable"],
            "loan_info": ["info", "details", "tell me"],
        }
        
        if intent in intent_keywords:
            for keyword in intent_keywords[intent]:
                if keyword in product['product_name'].lower():
                    h_score -= 0.3
        
        # Factor 2: Keyword overlap with product name and category
        product_text = (product['product_name'] + " " + product['category']).lower()
        matching_keywords = sum(1 for kw in keywords if kw in product_text)
        h_score -= (matching_keywords * 0.2)
        
        # Factor 3: Description relevance
        if product.get('description') and 'flexible' in product['description'].lower():
            h_score -= 0.15  # Flexibility is good
        
        return max(h_score, 0.0)
    
    def _generate_recommendation(self, product: Dict, intent: str, cost: float, heuristic: float) -> str:
        """Generate recommendation response based on A* results"""
        try:
            name = product['product_name']
            category = product['category']
            description = product['description']
            markup = product['markup_type']
            
            response = f"Based on my analysis, I recommend: **{name}**\n\n"
            response += f"📋 Category: {category}\n"
            response += f"📝 Description: {description}\n"
            response += f"💰 Markup Type: {markup}\n"
            
            if product.get('max_tenure_months'):
                response += f"⏰ Tenure: Up to {product['max_tenure_months']} months\n"
            
            if product.get('min_income'):
                response += f"💼 Minimum Income: PKR {product['min_income']:,}\n"
            
            response += f"\n✅ Recommendation Score: {(1 - (cost + heuristic)/2)*100:.0f}%\n"
            response += "\nWould you like to proceed with an application or need more information?"
            
            logger.info(f"Generated A* recommendation for: {name}")
            return response
        
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "I found a suitable financing option for you. Please contact our team for details."
    
    def _get_fallback_response(self) -> str:
        """Get fallback response for A* agent"""
        return (
            "I'm analyzing available financing options for you. "
            "Could you provide more details about your needs? "
            "For example: what type of financing, your income range, or preferred tenure?"
        )

