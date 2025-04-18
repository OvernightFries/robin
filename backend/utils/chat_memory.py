import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import redis
import time

logger = logging.getLogger(__name__)

class ChatMemory:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize chat memory storage with Redis."""
        self.redis = redis_client
        self.max_sessions = 100
        self.max_age = timedelta(days=1)
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
    def _retry_on_failure(self, func, *args, **kwargs):
        """Retry a Redis operation on failure."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Redis operation failed after {self.max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Redis operation failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Unexpected Redis error: {str(e)}")
                raise
        
    def get_current_ticker(self, session_id: str) -> Optional[str]:
        """Get the current ticker for a session."""
        if not self.redis:
            return None
            
        try:
            def _get():
                session_data = self.redis.get(f"session:{session_id}")
                if session_data:
                    data = json.loads(session_data)
                    return data.get('current_ticker')
                return None
                
            return self._retry_on_failure(_get)
        except Exception as e:
            logger.error(f"Error getting ticker from Redis: {str(e)}")
            return None
        
    def set_ticker(self, session_id: str, ticker: str):
        """Set the current ticker for a session."""
        if not self.redis:
            return
            
        try:
            def _set():
                session_data = {
                    'current_ticker': ticker,
                    'last_updated': datetime.now().isoformat()
                }
                self.redis.setex(
                    f"session:{session_id}",
                    self.max_age.total_seconds(),
                    json.dumps(session_data)
                )
                
            self._retry_on_failure(_set)
        except Exception as e:
            logger.error(f"Error setting ticker in Redis: {str(e)}")
        
    def clear_session(self, session_id: str):
        """Clear a session's data."""
        if not self.redis:
            return
            
        try:
            def _delete():
                self.redis.delete(f"session:{session_id}")
                
            self._retry_on_failure(_delete)
        except Exception as e:
            logger.error(f"Error clearing session from Redis: {str(e)}")
            
    def _cleanup(self):
        """Clean up old sessions."""
        if not self.redis:
            return
            
        try:
            # Redis will automatically expire keys based on the TTL we set
            # No need for manual cleanup
            pass
        except Exception as e:
            logger.error(f"Error cleaning up Redis sessions: {str(e)}") 
