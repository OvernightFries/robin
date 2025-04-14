import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChatMemory:
    def __init__(self):
        """Initialize chat memory storage."""
        self.sessions: Dict[str, Dict] = {}
        self.max_sessions = 100
        self.max_age = timedelta(days=1)
        
    def get_current_ticker(self, session_id: str) -> Optional[str]:
        """Get the current ticker for a session."""
        if session_id in self.sessions:
            return self.sessions[session_id].get('current_ticker')
        return None
        
    def set_ticker(self, session_id: str, ticker: str):
        """Set the current ticker for a session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        self.sessions[session_id]['current_ticker'] = ticker
        self.sessions[session_id]['last_updated'] = datetime.now()
        self._cleanup()
        
    def clear_session(self, session_id: str):
        """Clear a session's data."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
    def _cleanup(self):
        """Clean up old sessions."""
        now = datetime.now()
        # Remove sessions older than max_age
        self.sessions = {
            sid: data for sid, data in self.sessions.items()
            if now - data['last_updated'] <= self.max_age
        }
        # Remove oldest sessions if we exceed max_sessions
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1]['last_updated']
            )
            self.sessions = dict(sorted_sessions[-self.max_sessions:]) 
