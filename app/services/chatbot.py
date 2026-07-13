import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ChatbotService:
    
    @classmethod
    def process_message(cls, query, user_id, session_id):
        from utils.classifier import QueryClassifier
        from agents import AgentManager
        from app.utils.database import log_chat_interaction
        
        try:
            query_type, intent, is_sensitive = QueryClassifier.classify(query)
            
            if is_sensitive:
                logger.warning(f"Sensitive query detected: {query[:50]}")
                return {
                    'reply': 'I cannot assist with sensitive information requests. For account security, please contact support.',
                    'safe': False,
                    'query_type': query_type,
                    'intent': intent,
                    'agent': 'safety_filter'
                }
            
            agent_manager = AgentManager()
            
            if query_type == "complex":
                agent = agent_manager.get_agent("astar")
            else:
                agent = agent_manager.get_agent("bfs")
            
            context = {
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'query_type': query_type,
                'intent': intent
            }
            
            agent_response = agent.handle(query, context)
            
            try:
                log_chat_interaction(
                    user_id=user_id,
                    user_message=query,
                    agent_name=agent.name,
                    bot_response=agent_response.get('reply'),
                    query_type=query_type,
                    intent=intent,
                    safe=agent_response.get('safe', True)
                )
            except Exception as log_err:
                logger.warning(f"Failed to log interaction: {log_err}")
            
            return {
                'reply': agent_response.get('reply'),
                'agent': agent.name,
                'query_type': query_type,
                'intent': intent,
                'safe': agent_response.get('safe', True),
                'score': agent_response.get('score', 0.0)
            }
        
        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            return {
                'reply': 'I encountered an error processing your request. Please try again.',
                'agent': 'error_handler',
                'query_type': 'error',
                'intent': 'unknown',
                'safe': True
            }
