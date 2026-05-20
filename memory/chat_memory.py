"""
Chat Memory - Conversation history management.
"""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger


class ChatMemory:
    """
    Chat Memory for managing conversation history.

    Features:
    - Session-based memory
    - Message history
    - Context window management
    - Memory persistence
    """

    def __init__(
        self,
        max_history_length: int = 10,
        max_context_tokens: int = 4000,
    ):
        """
        Initialize chat memory.

        Args:
            max_history_length: Maximum number of messages to keep
            max_context_tokens: Maximum tokens for context
        """
        self.max_history_length = max_history_length
        self.max_context_tokens = max_context_tokens

        # Session storage
        self._sessions: Dict[UUID, List[Dict]] = {}

    def create_session(self) -> UUID:
        """
        Create a new chat session.

        Returns:
            Session ID
        """
        session_id = uuid4()
        self._sessions[session_id] = []
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: UUID) -> Optional[List[Dict]]:
        """
        Get chat history for a session.

        Args:
            session_id: Session ID

        Returns:
            List of messages or None if session not found
        """
        return self._sessions.get(session_id)

    def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add a message to session history.

        Args:
            session_id: Session ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

        self._sessions[session_id].append(message)

        # Trim history if needed
        self._trim_history(session_id)

        logger.debug(f"Added message to session {session_id}: {role}")

    def get_history(
        self,
        session_id: UUID,
        last_n: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get chat history for a session.

        Args:
            session_id: Session ID
            last_n: Number of last messages to return

        Returns:
            List of messages
        """
        history = self._sessions.get(session_id, [])

        if last_n:
            return history[-last_n:]

        return history

    def get_context_window(
        self,
        session_id: UUID,
        max_tokens: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get context window for LLM input.

        Args:
            session_id: Session ID
            max_tokens: Maximum tokens for context

        Returns:
            List of messages within token limit
        """
        max_tokens = max_tokens or self.max_context_tokens
        history = self._sessions.get(session_id, [])

        # Estimate tokens (simple: 1 token ≈ 4 chars)
        context = []
        total_tokens = 0

        for message in reversed(history):
            message_tokens = len(message["content"]) // 4

            if total_tokens + message_tokens > max_tokens:
                break

            context.insert(0, message)
            total_tokens += message_tokens

        return context

    def clear_session(self, session_id: UUID) -> None:
        """
        Clear chat history for a session.

        Args:
            session_id: Session ID
        """
        if session_id in self._sessions:
            self._sessions[session_id] = []
            logger.info(f"Cleared session: {session_id}")

    def delete_session(self, session_id: UUID) -> None:
        """
        Delete a session.

        Args:
            session_id: Session ID
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")

    def _trim_history(self, session_id: UUID) -> None:
        """
        Trim history to maximum length.

        Args:
            session_id: Session ID
        """
        history = self._sessions.get(session_id, [])

        if len(history) > self.max_history_length:
            self._sessions[session_id] = history[-self.max_history_length:]

    def get_session_count(self) -> int:
        """
        Get number of active sessions.

        Returns:
            Number of sessions
        """
        return len(self._sessions)

    def get_all_sessions(self) -> List[UUID]:
        """
        Get all session IDs.

        Returns:
            List of session IDs
        """
        return list(self._sessions.keys())

    def format_history_for_llm(
        self,
        session_id: UUID,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Format history for LLM input.

        Args:
            session_id: Session ID
            last_n: Number of last messages

        Returns:
            List of formatted messages
        """
        history = self.get_history(session_id, last_n)

        formatted = []
        for message in history:
            formatted.append({
                "role": message["role"],
                "content": message["content"],
            })

        return formatted

    def extract_query_context(
        self,
        session_id: UUID,
        current_query: str,
    ) -> str:
        """
        Extract context from history for query rewriting.

        Args:
            session_id: Session ID
            current_query: Current user query

        Returns:
            Context string
        """
        history = self.get_history(session_id, last_n=3)

        if not history:
            return current_query

        # Build context from recent history
        context_parts = []
        for message in history:
            if message["role"] == "user":
                context_parts.append(f"User: {message['content']}")
            elif message["role"] == "assistant":
                context_parts.append(f"Assistant: {message['content']}")

        context = "\n".join(context_parts)
        context += f"\nUser: {current_query}"

        return context
