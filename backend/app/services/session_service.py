"""
InsightX AI - Session Service

Provides session context management for maintaining conversation history.
Supports in-memory storage with easy Redis swap.
"""

from datetime import datetime
from typing import Dict, Optional
from collections import OrderedDict

from app.config import get_settings
from app.models.schemas import ConversationTurn, SessionContext


class SessionService:
    """
    Service for managing conversation session context.
    
    Maintains last N turns per session for context-aware responses.
    Uses in-memory storage by default, with optional Redis backend.
    """
    
    def __init__(self, max_turns: int = 6, max_sessions: int = 1000):
        """
        Initialize session service.
        
        Args:
            max_turns: Maximum conversation turns to retain per session.
            max_sessions: Maximum sessions to keep in memory (LRU eviction).
        """
        self.max_turns = max_turns
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, SessionContext] = OrderedDict()
    
    def get_session(self, session_id: str) -> SessionContext:
        """
        Get or create a session context.
        
        Args:
            session_id: Unique session identifier.
            
        Returns:
            SessionContext for the given session_id.
        """
        if session_id in self._sessions:
            # Move to end (most recently used)
            self._sessions.move_to_end(session_id)
            return self._sessions[session_id]
        
        # Create new session
        session = SessionContext(session_id=session_id)
        self._add_session(session_id, session)
        return session
    
    def add_turn(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        intent: Optional[Dict] = None,
        analysis: Optional[Dict] = None
    ) -> None:
        """
        Add a conversation turn to a session.
        
        Args:
            session_id: Session identifier.
            role: 'user' or 'assistant'.
            content: Message content.
            intent: Optional extracted intent (for user messages).
            analysis: Optional analysis result (for assistant messages).
        """
        session = self.get_session(session_id)
        
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        session.turns.append(turn)
        session.last_updated = datetime.utcnow()
        
        # Trim to max turns
        if len(session.turns) > self.max_turns:
            session.turns = session.turns[-self.max_turns:]
    
    def get_context_string(self, session_id: str) -> str:
        """
        Get formatted context string for LLM prompts.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Formatted conversation history string.
        """
        session = self.get_session(session_id)
        
        if not session.turns:
            return "No previous context."
        
        context_parts = []
        for turn in session.turns[-self.max_turns:]:
            role_label = "User" if turn.role == "user" else "Assistant"
            # Truncate long messages
            content = turn.content[:500] + "..." if len(turn.content) > 500 else turn.content
            context_parts.append(f"{role_label}: {content}")
        
        return "\n".join(context_parts)
    
    def get_last_user_query(self, session_id: str) -> Optional[str]:
        """Get the last user query from session."""
        session = self.get_session(session_id)
        
        for turn in reversed(session.turns):
            if turn.role == "user":
                return turn.content
        return None
    
    def clear_session(self, session_id: str) -> None:
        """Clear a specific session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def _add_session(self, session_id: str, session: SessionContext) -> None:
        """Add session with LRU eviction if needed."""
        if len(self._sessions) >= self.max_sessions:
            # Remove oldest session
            self._sessions.popitem(last=False)
        
        self._sessions[session_id] = session


class RedisSessionService(SessionService):
    """
    Redis-backed session service.
    
    Drop-in replacement for SessionService using Redis for persistence.
    """
    
    def __init__(self, redis_url: str, max_turns: int = 6):
        """
        Initialize Redis session service.
        
        Args:
            redis_url: Redis connection URL.
            max_turns: Maximum conversation turns to retain.
        """
        super().__init__(max_turns=max_turns)
        self.redis_url = redis_url
        self._redis = None
        
        # Import redis only if needed
        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
        except ImportError:
            raise ImportError("redis package required for Redis session storage")
    
    def get_session(self, session_id: str) -> SessionContext:
        """Get session from Redis."""
        if not self._redis:
            return super().get_session(session_id)
        
        import json
        
        key = f"insightx:session:{session_id}"
        data = self._redis.get(key)
        
        if data:
            return SessionContext.model_validate_json(data)
        
        # Create new session
        session = SessionContext(session_id=session_id)
        self._save_session(session)
        return session
    
    def add_turn(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        intent: Optional[Dict] = None,
        analysis: Optional[Dict] = None
    ) -> None:
        """Add turn and save to Redis."""
        session = self.get_session(session_id)
        
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        session.turns.append(turn)
        session.last_updated = datetime.utcnow()
        
        # Trim to max turns
        if len(session.turns) > self.max_turns:
            session.turns = session.turns[-self.max_turns:]
        
        self._save_session(session)
    
    def _save_session(self, session: SessionContext) -> None:
        """Save session to Redis with TTL."""
        if not self._redis:
            return
        
        key = f"insightx:session:{session.session_id}"
        # 24 hour TTL
        self._redis.setex(key, 86400, session.model_dump_json())
    
    def clear_session(self, session_id: str) -> None:
        """Clear session from Redis."""
        if self._redis:
            self._redis.delete(f"insightx:session:{session_id}")


# Global session service instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Get or create the session service singleton."""
    global _session_service
    
    if _session_service is None:
        settings = get_settings()
        
        if settings.redis_url:
            _session_service = RedisSessionService(
                redis_url=settings.redis_url,
                max_turns=settings.max_context_turns
            )
        else:
            _session_service = SessionService(
                max_turns=settings.max_context_turns
            )
    
    return _session_service
