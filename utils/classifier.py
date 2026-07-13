"""
Query Classifier - Determines if query is Simple or Complex
Routes to appropriate agent (BFS for simple, A* for complex)
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class QueryClassifier:
    """Classifies queries as simple or complex and extracts intent"""
    
    # Simple intent keywords (uninformed search - BFS/DFS)
    SIMPLE_INTENTS = {
        "balance": ["balance", "account balance", "how much", "remaining"],
        "loan_info": ["loan", "financing", "tell me about", "information", "details", "what is"],
        "card": ["card", "debit card", "credit card"],
        "transfer": ["transfer", "send money", "payment"],
        "interest": ["interest", "rate", "markup", "charges"],
        "account": ["account", "profile", "my account"],
    }
    
    # Complex intent keywords (informed search - A*/Greedy)
    COMPLEX_INTENTS = {
        "loan_application": ["apply", "application", "interested", "want to apply", "how to apply"],
        "loan_eligibility": ["eligible", "qualify", "qualification", "requirements", "criteria"],
        "loan_recommendation": ["recommend", "suitable", "best", "which is better", "compare"],
        "multi_step_query": ["multiple", "steps", "process", "procedure", "how does it work"],
        "custom_financing": ["custom", "tailored", "specific needs", "circumstances"],
    }
    
    # Restricted/Sensitive topics
    RESTRICTED_TOPICS = {
        "sensitive": ["ssn", "pin", "password", "account number", "credit card number", 
                     "card details", "cvv", "routing number", "iban", "swift"]
    }
    
    @classmethod
    def classify(cls, query: str) -> Tuple[str, str, bool]:
        """
        Classify query type and extract intent
        
        Args:
            query: User query string
        
        Returns:
            Tuple of (query_type, intent, is_sensitive)
            query_type: "simple", "complex", or "restricted"
            intent: extracted intent keyword
            is_sensitive: whether topic is restricted
        """
        query_lower = query.lower().strip()
        
        # Check for restricted topics first
        for category, keywords in cls.RESTRICTED_TOPICS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    logger.warning(f"Restricted topic detected: {keyword}")
                    return "restricted", category, True
        
        # Check for complex intents
        for intent, keywords in cls.COMPLEX_INTENTS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    logger.info(f"Complex query detected - Intent: {intent}")
                    return "complex", intent, False
        
        # Check for simple intents
        for intent, keywords in cls.SIMPLE_INTENTS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    logger.info(f"Simple query detected - Intent: {intent}")
                    return "simple", intent, False
        
        # Default to simple if no specific intent found
        logger.info("Query classified as simple (default)")
        return "simple", "general", False
    
    @classmethod
    def extract_keywords(cls, query: str) -> list:
        """Extract important keywords from query"""
        query_lower = query.lower()
        keywords = []
        
        # Extract category names
        categories = ["auto", "car", "home", "house", "personal", "business", "education", 
                     "student", "islamic", "lease", "emergency"]
        
        for category in categories:
            if category in query_lower:
                keywords.append(category)
        
        # Extract financial terms
        terms = ["loan", "financing", "interest", "markup", "tenure", "payment", "income"]
        for term in terms:
            if term in query_lower:
                keywords.append(term)
        
        return list(set(keywords))  # Remove duplicates
    
    @classmethod
    def get_confidence_score(cls, query: str, intent: str) -> float:
        """
        Calculate confidence score for extracted intent (0.0 - 1.0)
        
        Args:
            query: User query
            intent: Extracted intent
        
        Returns:
            Confidence score
        """
        query_lower = query.lower()
        
        # Look up intent keywords
        intent_keywords = cls.SIMPLE_INTENTS.get(intent, [])
        if not intent_keywords:
            intent_keywords = cls.COMPLEX_INTENTS.get(intent, [])
        
        if not intent_keywords:
            return 0.5  # Unknown intent
        
        # Count how many keywords match
        match_count = sum(1 for keyword in intent_keywords if keyword in query_lower)
        max_possible = len(intent_keywords)
        
        # Calculate confidence (base 0.6 + 0.4 * match ratio)
        confidence = 0.6 + (0.4 * (match_count / max_possible))
        return min(confidence, 0.95)  # Cap at 0.95
