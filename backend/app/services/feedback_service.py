"""
User feedback collection and management service.
Handles feedback submission, rating systems, and user support.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from ..models.feedback import (
    UserFeedback, FeedbackResponse, UserSupportTicket, SupportMessage,
    FeatureUsageAnalytics
)
from ..models.user import User
from ..database import get_db

logger = logging.getLogger(__name__)

class FeedbackService:
    """Service for managing user feedback and ratings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def submit_feedback(self, user_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit user feedback"""
        try:
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type=feedback_data.get("type", "general"),
                category=feedback_data.get("category"),
                title=feedback_data["title"],
                description=feedback_data["description"],
                rating=feedback_data.get("rating"),
                page_url=feedback_data.get("page_url"),
                user_agent=feedback_data.get("user_agent"),
                metadata=feedback_data.get("metadata", {})
            )
            
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            
            logger.info(f"Feedback submitted by user {user_id}: {feedback.id}")
            
            return {
                "success": True,
                "feedback_id": str(feedback.id),
                "message": "Feedback submitted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_feedback(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get feedback submitted by a user"""
        try:
            feedback_items = self.db.query(UserFeedback).filter(
                UserFeedback.user_id == user_id
            ).order_by(UserFeedback.created_at.desc()).limit(limit).all()
            
            result = []
            for feedback in feedback_items:
                feedback_dict = {
                    "id": str(feedback.id),
                    "type": feedback.feedback_type,
                    "category": feedback.category,
                    "title": feedback.title,
                    "description": feedback.description,
                    "rating": feedback.rating,
                    "status": feedback.status,
                    "priority": feedback.priority,
                    "created_at": feedback.created_at.isoformat(),
                    "updated_at": feedback.updated_at.isoformat(),
                    "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None
                }
                
                # Add public responses
                public_responses = self.db.query(FeedbackResponse).filter(
                    and_(
                        FeedbackResponse.feedback_id == feedback.id,
                        FeedbackResponse.is_public == True
                    )
                ).order_by(FeedbackResponse.created_at).all()
                
                feedback_dict["responses"] = [
                    {
                        "id": str(response.id),
                        "response_text": response.response_text,
                        "created_at": response.created_at.isoformat()
                    }
                    for response in public_responses
                ]
                
                result.append(feedback_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return []
    
    async def get_feedback_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback analytics and insights"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Total feedback counts
            total_feedback = self.db.query(func.count(UserFeedback.id)).filter(
                UserFeedback.created_at >= cutoff_date
            ).scalar()
            
            # Feedback by type
            feedback_by_type = self.db.query(
                UserFeedback.feedback_type,
                func.count(UserFeedback.id).label('count')
            ).filter(
                UserFeedback.created_at >= cutoff_date
            ).group_by(UserFeedback.feedback_type).all()
            
            # Feedback by status
            feedback_by_status = self.db.query(
                UserFeedback.status,
                func.count(UserFeedback.id).label('count')
            ).filter(
                UserFeedback.created_at >= cutoff_date
            ).group_by(UserFeedback.status).all()
            
            # Average rating
            avg_rating = self.db.query(func.avg(UserFeedback.rating)).filter(
                and_(
                    UserFeedback.created_at >= cutoff_date,
                    UserFeedback.rating.isnot(None)
                )
            ).scalar()
            
            # Rating distribution
            rating_distribution = self.db.query(
                UserFeedback.rating,
                func.count(UserFeedback.id).label('count')
            ).filter(
                and_(
                    UserFeedback.created_at >= cutoff_date,
                    UserFeedback.rating.isnot(None)
                )
            ).group_by(UserFeedback.rating).all()
            
            # Response time analytics
            response_times = self.db.query(
                func.extract('epoch', FeedbackResponse.created_at - UserFeedback.created_at).label('response_time')
            ).join(FeedbackResponse).filter(
                UserFeedback.created_at >= cutoff_date
            ).all()
            
            avg_response_time = sum(rt[0] for rt in response_times) / len(response_times) if response_times else 0
            
            return {
                "period_days": days,
                "total_feedback": total_feedback,
                "feedback_by_type": {item[0]: item[1] for item in feedback_by_type},
                "feedback_by_status": {item[0]: item[1] for item in feedback_by_status},
                "average_rating": float(avg_rating) if avg_rating else None,
                "rating_distribution": {item[0]: item[1] for item in rating_distribution},
                "average_response_time_hours": avg_response_time / 3600 if avg_response_time else 0,
                "total_responses": len(response_times)
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {"error": str(e)}
    
    async def respond_to_feedback(self, feedback_id: str, admin_user_id: str, 
                                response_text: str, is_public: bool = True) -> Dict[str, Any]:
        """Admin response to user feedback"""
        try:
            # Verify feedback exists
            feedback = self.db.query(UserFeedback).filter(
                UserFeedback.id == feedback_id
            ).first()
            
            if not feedback:
                return {"success": False, "error": "Feedback not found"}
            
            # Create response
            response = FeedbackResponse(
                feedback_id=feedback_id,
                admin_user_id=admin_user_id,
                response_text=response_text,
                is_public=is_public
            )
            
            self.db.add(response)
            
            # Update feedback status if it was open
            if feedback.status == "open":
                feedback.status = "in_review"
                feedback.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(response)
            
            logger.info(f"Response added to feedback {feedback_id} by admin {admin_user_id}")
            
            return {
                "success": True,
                "response_id": str(response.id),
                "message": "Response added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error responding to feedback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def update_feedback_status(self, feedback_id: str, status: str, 
                                   admin_user_id: str = None) -> Dict[str, Any]:
        """Update feedback status"""
        try:
            feedback = self.db.query(UserFeedback).filter(
                UserFeedback.id == feedback_id
            ).first()
            
            if not feedback:
                return {"success": False, "error": "Feedback not found"}
            
            old_status = feedback.status
            feedback.status = status
            feedback.updated_at = datetime.now(timezone.utc)
            
            if status in ["resolved", "closed"]:
                feedback.resolved_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Feedback {feedback_id} status updated from {old_status} to {status}")
            
            return {
                "success": True,
                "message": f"Status updated to {status}"
            }
            
        except Exception as e:
            logger.error(f"Error updating feedback status: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

class SupportTicketService:
    """Service for managing user support tickets"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        import random
        import string
        
        while True:
            # Generate format: SUP-YYYYMMDD-XXXX
            date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
            random_part = ''.join(random.choices(string.digits, k=4))
            ticket_number = f"SUP-{date_part}-{random_part}"
            
            # Check if it already exists
            existing = self.db.query(UserSupportTicket).filter(
                UserSupportTicket.ticket_number == ticket_number
            ).first()
            
            if not existing:
                return ticket_number
    
    async def create_ticket(self, user_id: str, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new support ticket"""
        try:
            ticket = UserSupportTicket(
                user_id=user_id,
                ticket_number=self._generate_ticket_number(),
                subject=ticket_data["subject"],
                description=ticket_data["description"],
                category=ticket_data.get("category", "general"),
                priority=ticket_data.get("priority", "medium")
            )
            
            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)
            
            logger.info(f"Support ticket created: {ticket.ticket_number} by user {user_id}")
            
            return {
                "success": True,
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.ticket_number,
                "message": "Support ticket created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_user_tickets(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get support tickets for a user"""
        try:
            tickets = self.db.query(UserSupportTicket).filter(
                UserSupportTicket.user_id == user_id
            ).order_by(UserSupportTicket.created_at.desc()).limit(limit).all()
            
            result = []
            for ticket in tickets:
                # Get message count
                message_count = self.db.query(func.count(SupportMessage.id)).filter(
                    SupportMessage.ticket_id == ticket.id
                ).scalar()
                
                # Get last message
                last_message = self.db.query(SupportMessage).filter(
                    SupportMessage.ticket_id == ticket.id
                ).order_by(SupportMessage.created_at.desc()).first()
                
                ticket_dict = {
                    "id": str(ticket.id),
                    "ticket_number": ticket.ticket_number,
                    "subject": ticket.subject,
                    "description": ticket.description,
                    "category": ticket.category,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "created_at": ticket.created_at.isoformat(),
                    "updated_at": ticket.updated_at.isoformat(),
                    "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                    "message_count": message_count,
                    "last_message_at": last_message.created_at.isoformat() if last_message else None,
                    "satisfaction_rating": ticket.satisfaction_rating,
                    "satisfaction_comment": ticket.satisfaction_comment
                }
                
                result.append(ticket_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    async def add_message(self, ticket_id: str, sender_id: str, message_text: str, 
                         is_internal: bool = False) -> Dict[str, Any]:
        """Add message to support ticket"""
        try:
            # Verify ticket exists
            ticket = self.db.query(UserSupportTicket).filter(
                UserSupportTicket.id == ticket_id
            ).first()
            
            if not ticket:
                return {"success": False, "error": "Ticket not found"}
            
            message = SupportMessage(
                ticket_id=ticket_id,
                sender_id=sender_id,
                message_text=message_text,
                is_internal=is_internal
            )
            
            self.db.add(message)
            
            # Update ticket status and timestamp
            if ticket.status == "waiting":
                ticket.status = "in_progress"
            ticket.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(message)
            
            logger.info(f"Message added to ticket {ticket.ticket_number}")
            
            return {
                "success": True,
                "message_id": str(message.id),
                "message": "Message added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding message to ticket: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_ticket_messages(self, ticket_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Get messages for a support ticket"""
        try:
            # Verify access to ticket
            ticket = self.db.query(UserSupportTicket).filter(
                UserSupportTicket.id == ticket_id
            ).first()
            
            if not ticket:
                return []
            
            # If user_id provided, verify they own the ticket or are admin
            if user_id and str(ticket.user_id) != user_id:
                # Check if user is admin (simplified check)
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user or not getattr(user, 'is_admin', False):
                    return []
            
            # Get messages (exclude internal messages for regular users)
            query = self.db.query(SupportMessage).filter(
                SupportMessage.ticket_id == ticket_id
            )
            
            if user_id and str(ticket.user_id) == user_id:
                # Regular user - exclude internal messages
                query = query.filter(SupportMessage.is_internal == False)
            
            messages = query.order_by(SupportMessage.created_at).all()
            
            result = []
            for message in messages:
                sender = self.db.query(User).filter(User.id == message.sender_id).first()
                
                message_dict = {
                    "id": str(message.id),
                    "message_text": message.message_text,
                    "is_internal": message.is_internal,
                    "created_at": message.created_at.isoformat(),
                    "sender": {
                        "id": str(sender.id),
                        "email": sender.email,
                        "is_admin": getattr(sender, 'is_admin', False)
                    } if sender else None
                }
                
                result.append(message_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting ticket messages: {e}")
            return []

class FeatureUsageService:
    """Service for tracking feature usage analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_feature_usage(self, user_id: str, feature_name: str, action: str,
                                metadata: Dict[str, Any] = None, session_id: str = None,
                                page_url: str = None, user_agent: str = None) -> bool:
        """Track feature usage event"""
        try:
            usage_event = FeatureUsageAnalytics(
                user_id=user_id,
                feature_name=feature_name,
                action=action,
                session_id=session_id,
                page_url=page_url,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.db.add(usage_event)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            self.db.rollback()
            return False
    
    async def get_feature_analytics(self, feature_name: str = None, 
                                  days: int = 30) -> Dict[str, Any]:
        """Get feature usage analytics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = self.db.query(FeatureUsageAnalytics).filter(
                FeatureUsageAnalytics.timestamp >= cutoff_date
            )
            
            if feature_name:
                query = query.filter(FeatureUsageAnalytics.feature_name == feature_name)
            
            # Total events
            total_events = query.count()
            
            # Unique users
            unique_users = query.with_entities(FeatureUsageAnalytics.user_id).distinct().count()
            
            # Events by feature
            events_by_feature = self.db.query(
                FeatureUsageAnalytics.feature_name,
                func.count(FeatureUsageAnalytics.id).label('count')
            ).filter(
                FeatureUsageAnalytics.timestamp >= cutoff_date
            ).group_by(FeatureUsageAnalytics.feature_name).all()
            
            # Events by action
            events_by_action = self.db.query(
                FeatureUsageAnalytics.action,
                func.count(FeatureUsageAnalytics.id).label('count')
            ).filter(
                FeatureUsageAnalytics.timestamp >= cutoff_date
            ).group_by(FeatureUsageAnalytics.action).all()
            
            # Daily usage trend
            daily_usage = self.db.query(
                func.date(FeatureUsageAnalytics.timestamp).label('date'),
                func.count(FeatureUsageAnalytics.id).label('count')
            ).filter(
                FeatureUsageAnalytics.timestamp >= cutoff_date
            ).group_by(func.date(FeatureUsageAnalytics.timestamp)).all()
            
            return {
                "period_days": days,
                "feature_name": feature_name,
                "total_events": total_events,
                "unique_users": unique_users,
                "events_by_feature": {item[0]: item[1] for item in events_by_feature},
                "events_by_action": {item[0]: item[1] for item in events_by_action},
                "daily_usage": [
                    {"date": item[0].isoformat(), "count": item[1]} 
                    for item in daily_usage
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting feature analytics: {e}")
            return {"error": str(e)}