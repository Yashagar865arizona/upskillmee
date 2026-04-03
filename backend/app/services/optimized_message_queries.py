"""
Optimized Message Query Service

This service provides optimized database queries for message and conversation operations
to prevent N+1 query problems and improve performance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, desc, func
from datetime import datetime, timezone, timedelta
from ..models.chat import Conversation, Message
from ..models.user import User

logger = logging.getLogger(__name__)

class OptimizedMessageQueries:
    """Service for optimized message and conversation database queries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_conversation_with_messages(
        self, 
        conversation_id: str, 
        limit: int = 50,
        include_user: bool = False
    ) -> Optional[Conversation]:
        """
        Get a conversation with its messages in a single optimized query.
        Prevents N+1 queries by using proper joins and eager loading.
        """
        try:
            query = self.db.query(Conversation)
            
            # Use selectinload to efficiently load messages
            query = query.options(
                selectinload(Conversation.messages).options(
                    joinedload(Message.user) if include_user else None
                )
            )
            
            if include_user:
                query = query.options(joinedload(Conversation.user))
            
            conversation = query.filter(Conversation.id == conversation_id).first()
            
            if conversation and conversation.messages:
                # Sort messages by created_at (database index will be used)
                conversation.messages.sort(key=lambda m: m.created_at)
                
                # Limit messages if specified
                if limit and len(conversation.messages) > limit:
                    conversation.messages = conversation.messages[-limit:]
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation with messages: {e}")
            return None
    
    def get_user_conversations_with_recent_messages(
        self, 
        user_id: str, 
        limit: int = 10,
        message_limit: int = 5
    ) -> List[Conversation]:
        """
        Get user's conversations with their most recent messages.
        Uses optimized queries with proper indexing.
        """
        try:
            # First, get conversations with basic info
            conversations = (
                self.db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .all()
            )
            
            if not conversations:
                return []
            
            # Get conversation IDs for batch message loading
            conversation_ids = [conv.id for conv in conversations]
            
            # Batch load recent messages for all conversations
            # This prevents N+1 queries by loading all messages at once
            recent_messages = (
                self.db.query(Message)
                .filter(Message.conversation_id.in_(conversation_ids))
                .order_by(Message.conversation_id, desc(Message.created_at))
                .all()
            )
            
            # Group messages by conversation
            messages_by_conversation = {}
            for message in recent_messages:
                conv_id = message.conversation_id
                if conv_id not in messages_by_conversation:
                    messages_by_conversation[conv_id] = []
                messages_by_conversation[conv_id].append(message)
            
            # Attach messages to conversations and limit them
            for conversation in conversations:
                conv_messages = messages_by_conversation.get(conversation.id, [])
                # Sort by created_at and take the most recent
                conv_messages.sort(key=lambda m: m.created_at, reverse=True)
                conversation.messages = conv_messages[:message_limit]
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting user conversations with messages: {e}")
            return []
    
    def get_messages_with_context(
        self,
        conversation_id: str,
        limit: int = 50,
        before_message_id: Optional[str] = None
    ) -> List[Message]:
        """
        Get messages for a conversation with optimized loading.
        Uses database indexes for efficient pagination.
        """
        try:
            query = (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .options(joinedload(Message.user))  # Prevent N+1 for user data
                .order_by(Message.created_at)
            )
            
            # Add pagination if before_message_id is provided
            if before_message_id:
                before_message = (
                    self.db.query(Message)
                    .filter(Message.id == before_message_id)
                    .first()
                )
                if before_message:
                    query = query.filter(Message.created_at < before_message.created_at)
            
            messages = query.limit(limit).all()
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages with context: {e}")
            return []
    
    def get_user_message_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user message statistics with optimized aggregation queries.
        Uses database indexes for efficient counting and grouping.
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Single query to get all statistics
            stats = (
                self.db.query(
                    func.count(Message.id).label('total_messages'),
                    func.count(func.distinct(Message.conversation_id)).label('conversations'),
                    func.avg(func.length(Message.content)).label('avg_message_length'),
                    func.count(
                        func.case([(Message.role == 'user', 1)], else_=None)
                    ).label('user_messages'),
                    func.count(
                        func.case([(Message.role == 'assistant', 1)], else_=None)
                    ).label('bot_messages')
                )
                .filter(
                    and_(
                        Message.user_id == user_id,
                        Message.created_at >= cutoff_date
                    )
                )
                .first()
            )
            
            return {
                'total_messages': stats.total_messages or 0,
                'conversations': stats.conversations or 0,
                'avg_message_length': float(stats.avg_message_length or 0),
                'user_messages': stats.user_messages or 0,
                'bot_messages': stats.bot_messages or 0,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting user message statistics: {e}")
            return {}
    
    def search_messages_optimized(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        conversation_id: Optional[str] = None
    ) -> List[Message]:
        """
        Search messages with optimized text search.
        Uses database indexes for efficient text matching.
        """
        try:
            db_query = (
                self.db.query(Message)
                .filter(Message.user_id == user_id)
                .options(joinedload(Message.conversation))  # Prevent N+1 for conversation data
            )
            
            # Add conversation filter if specified
            if conversation_id:
                db_query = db_query.filter(Message.conversation_id == conversation_id)
            
            # Simple text search (can be enhanced with full-text search later)
            db_query = db_query.filter(Message.content.ilike(f'%{query}%'))
            
            # Order by relevance (most recent first for now)
            db_query = db_query.order_by(desc(Message.created_at))
            
            messages = db_query.limit(limit).all()
            return messages
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    def get_conversation_participants(self, conversation_id: str) -> List[User]:
        """
        Get all users who have participated in a conversation.
        Uses optimized query with proper joins.
        """
        try:
            participants = (
                self.db.query(User)
                .join(Message, User.id == Message.user_id)
                .filter(Message.conversation_id == conversation_id)
                .distinct()
                .all()
            )
            
            return participants
            
        except Exception as e:
            logger.error(f"Error getting conversation participants: {e}")
            return []
    
    def bulk_update_message_metadata(
        self, 
        message_updates: List[Dict[str, Any]]
    ) -> bool:
        """
        Bulk update message metadata efficiently.
        Reduces database round trips for batch operations.
        """
        try:
            if not message_updates:
                return True
            
            # Group updates by message ID for efficient processing
            for update in message_updates:
                message_id = update.get('message_id')
                metadata = update.get('metadata', {})
                
                if message_id and metadata:
                    self.db.query(Message).filter(
                        Message.id == message_id
                    ).update(
                        {'message_metadata': metadata},
                        synchronize_session=False
                    )
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error bulk updating message metadata: {e}")
            self.db.rollback()
            return False
    
    def get_recent_active_conversations(
        self, 
        hours: int = 24, 
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get recently active conversations across all users.
        Uses optimized query with proper indexing.
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            conversations = (
                self.db.query(Conversation)
                .filter(Conversation.updated_at >= cutoff_time)
                .options(
                    joinedload(Conversation.user),
                    selectinload(Conversation.messages).options(
                        joinedload(Message.user)
                    )
                )
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .all()
            )
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting recent active conversations: {e}")
            return []
    
    def cleanup_old_conversations(self, days_old: int = 90) -> int:
        """
        Clean up old conversations and their messages.
        Uses efficient bulk operations.
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Get conversation IDs to delete
            old_conversations = (
                self.db.query(Conversation.id)
                .filter(Conversation.updated_at < cutoff_date)
                .all()
            )
            
            if not old_conversations:
                return 0
            
            conversation_ids = [conv.id for conv in old_conversations]
            
            # Delete messages first (due to foreign key constraints)
            deleted_messages = (
                self.db.query(Message)
                .filter(Message.conversation_id.in_(conversation_ids))
                .delete(synchronize_session=False)
            )
            
            # Delete conversations
            deleted_conversations = (
                self.db.query(Conversation)
                .filter(Conversation.id.in_(conversation_ids))
                .delete(synchronize_session=False)
            )
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_conversations} conversations and {deleted_messages} messages")
            return deleted_conversations
            
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            self.db.rollback()
            return 0