"""
Analytics router for user engagement tracking and metrics collection.
Provides comprehensive analytics endpoints for user behavior, learning progress,
and system performance monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import logging

from ..database import get_db
from ..services.analytics_service import AnalyticsService, EventType
from ..dependencies import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

class AnalyticsRouter:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all analytics routes"""
        # User engagement endpoints
        self.router.add_api_route("/events", self.track_event, methods=["POST"])
        self.router.add_api_route("/engagement/{user_id}", self.get_user_engagement, methods=["GET"])
        self.router.add_api_route("/engagement/summary/{user_id}", self.get_engagement_summary, methods=["GET"])
        
        # Learning analytics endpoints
        self.router.add_api_route("/learning/{user_id}", self.get_learning_analytics, methods=["GET"])
        self.router.add_api_route("/progress/{user_id}", self.get_learning_progress, methods=["GET"])
        
        # Conversion funnel endpoints
        self.router.add_api_route("/funnel", self.get_conversion_funnel, methods=["GET"])
        self.router.add_api_route("/funnel/user/{user_id}", self.get_user_funnel_progress, methods=["GET"])
        
        # Dashboard endpoints
        self.router.add_api_route("/dashboard", self.get_analytics_dashboard, methods=["GET"])
        self.router.add_api_route("/dashboard/{user_id}", self.get_user_dashboard, methods=["GET"])
        
        # Metrics endpoints
        self.router.add_api_route("/metrics/engagement", self.get_engagement_metrics, methods=["GET"])
        self.router.add_api_route("/metrics/learning", self.get_learning_metrics, methods=["GET"])
        self.router.add_api_route("/metrics/system", self.get_system_metrics, methods=["GET"])

    async def track_event(
        self,
        event_data: Dict[str, Any],
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Track a user event for analytics"""
        try:
            analytics_service = AnalyticsService()
            
            # Extract event details
            event_type = EventType(event_data.get("event_type"))
            metadata = event_data.get("metadata", {})
            session_id = event_data.get("session_id")
            
            # Track the event
            await analytics_service.track_event(
                db=db,
                user_id=str(current_user.id),
                event_type=event_type,
                metadata=metadata,
                session_id=session_id
            )
            
            return {
                "status": "success",
                "message": "Event tracked successfully",
                "event_type": event_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except ValueError as e:
            logger.error(f"Invalid event type: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            raise HTTPException(status_code=500, detail="Failed to track event")

    async def get_user_engagement(
        self,
        user_id: str,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get user engagement metrics"""
        try:
            # Check if user can access this data (admin or own data)
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            engagement_metrics = await analytics_service.calculate_engagement_metrics(
                db, user_id, timedelta(days=days)
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "period_days": days,
                "metrics": engagement_metrics.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user engagement: {e}")
            raise HTTPException(status_code=500, detail="Failed to get engagement metrics")

    async def get_engagement_summary(
        self,
        user_id: str,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get comprehensive engagement summary for a user"""
        try:
            # Check if user can access this data
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            summary = await analytics_service.get_user_engagement_summary(db, user_id, days)
            
            return {
                "status": "success",
                "data": summary
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting engagement summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get engagement summary")

    async def get_learning_analytics(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get learning analytics for a user"""
        try:
            # Check if user can access this data
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            learning_metrics = await analytics_service.calculate_learning_metrics(db, user_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "learning_metrics": learning_metrics.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting learning analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get learning analytics")

    async def get_learning_progress(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get detailed learning progress for a user"""
        try:
            # Check if user can access this data
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            
            # Get conversation metrics
            conversation_metrics = await analytics_service.get_conversation_metrics(db, user_id)
            
            # Get learning metrics
            learning_metrics = await analytics_service.calculate_learning_metrics(db, user_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "conversation_metrics": conversation_metrics.dict(),
                "learning_metrics": learning_metrics.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting learning progress: {e}")
            raise HTTPException(status_code=500, detail="Failed to get learning progress")

    async def get_conversion_funnel(
        self,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get conversion funnel analysis"""
        try:
            # Only admin users can access system-wide funnel data
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            analytics_service = AnalyticsService()
            funnel_data = await analytics_service.get_conversion_funnel_analysis(db, days)
            
            return {
                "status": "success",
                "period_days": days,
                "funnel_stages": [stage.dict() for stage in funnel_data]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            raise HTTPException(status_code=500, detail="Failed to get conversion funnel")

    async def get_user_funnel_progress(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get funnel progress for a specific user"""
        try:
            # Check if user can access this data
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            
            # Get user events to determine funnel progress
            user_events = analytics_service.user_events.get(user_id, [])
            
            # Determine which funnel stages the user has completed
            completed_stages = []
            event_types = [event.event_type for event in user_events]
            
            if EventType.USER_LOGIN in event_types:
                completed_stages.append("registration")
            if EventType.MESSAGE_SENT in event_types:
                completed_stages.append("first_message")
            if EventType.LEARNING_PLAN_GENERATED in event_types:
                completed_stages.append("learning_plan_generated")
            if EventType.LEARNING_PLAN_ACCEPTED in event_types:
                completed_stages.append("learning_plan_accepted")
            if EventType.PROJECT_CREATED in event_types:
                completed_stages.append("project_created")
            if EventType.TASK_COMPLETED in event_types:
                completed_stages.append("task_completed")
            if EventType.PROJECT_COMPLETED in event_types:
                completed_stages.append("project_completed")
            
            return {
                "status": "success",
                "user_id": user_id,
                "completed_stages": completed_stages,
                "total_events": len(user_events),
                "funnel_completion_percentage": len(completed_stages) / 7 * 100  # 7 total stages
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user funnel progress: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user funnel progress")

    async def get_analytics_dashboard(
        self,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get analytics dashboard data (admin only)"""
        try:
            # Only admin users can access system-wide dashboard
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            analytics_service = AnalyticsService()
            
            # Get conversion funnel
            funnel_data = await analytics_service.get_conversion_funnel_analysis(db, days)
            
            # Calculate aggregate metrics
            total_users = len(analytics_service.user_events)
            total_events = sum(len(events) for events in analytics_service.user_events.values())
            
            # Get active users (users with events in the last 7 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            active_users = 0
            for user_events in analytics_service.user_events.values():
                if any(event.timestamp >= cutoff_date for event in user_events):
                    active_users += 1
            
            return {
                "status": "success",
                "period_days": days,
                "summary": {
                    "total_users": total_users,
                    "active_users_7d": active_users,
                    "total_events": total_events,
                    "avg_events_per_user": total_events / total_users if total_users > 0 else 0
                },
                "funnel": [stage.dict() for stage in funnel_data]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analytics dashboard: {e}")
            raise HTTPException(status_code=500, detail="Failed to get analytics dashboard")

    async def get_user_dashboard(
        self,
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get user-specific dashboard data"""
        try:
            # Check if user can access this data
            if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Access denied")
            
            analytics_service = AnalyticsService()
            
            # Get comprehensive user data
            engagement_summary = await analytics_service.get_user_engagement_summary(db, user_id, 30)
            learning_metrics = await analytics_service.calculate_learning_metrics(db, user_id)
            conversation_metrics = await analytics_service.get_conversation_metrics(db, user_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "engagement": engagement_summary,
                "learning": learning_metrics.dict(),
                "conversations": conversation_metrics.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user dashboard: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user dashboard")

    async def get_engagement_metrics(
        self,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get system-wide engagement metrics (admin only)"""
        try:
            # Only admin users can access system-wide metrics
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            analytics_service = AnalyticsService()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Calculate system-wide engagement metrics
            total_users = len(analytics_service.user_events)
            active_users = 0
            total_sessions = 0
            total_messages = 0
            
            for user_id, user_events in analytics_service.user_events.items():
                recent_events = [e for e in user_events if e.timestamp >= cutoff_date]
                if recent_events:
                    active_users += 1
                    
                # Count sessions and messages
                sessions = set(e.session_id for e in recent_events if e.session_id)
                total_sessions += len(sessions)
                
                message_events = [e for e in recent_events if e.event_type == EventType.MESSAGE_SENT]
                total_messages += len(message_events)
            
            return {
                "status": "success",
                "period_days": days,
                "metrics": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "user_retention_rate": active_users / total_users if total_users > 0 else 0,
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "avg_messages_per_user": total_messages / active_users if active_users > 0 else 0,
                    "avg_sessions_per_user": total_sessions / active_users if active_users > 0 else 0
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get engagement metrics")

    async def get_learning_metrics(
        self,
        days: int = Query(30, description="Number of days to analyze"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get system-wide learning metrics (admin only)"""
        try:
            # Only admin users can access system-wide metrics
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            analytics_service = AnalyticsService()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Calculate learning metrics across all users
            total_plans_generated = 0
            total_plans_accepted = 0
            total_projects_created = 0
            total_projects_completed = 0
            total_tasks_completed = 0
            
            for user_events in analytics_service.user_events.values():
                recent_events = [e for e in user_events if e.timestamp >= cutoff_date]
                
                for event in recent_events:
                    if event.event_type == EventType.LEARNING_PLAN_GENERATED:
                        total_plans_generated += 1
                    elif event.event_type == EventType.LEARNING_PLAN_ACCEPTED:
                        total_plans_accepted += 1
                    elif event.event_type == EventType.PROJECT_CREATED:
                        total_projects_created += 1
                    elif event.event_type == EventType.PROJECT_COMPLETED:
                        total_projects_completed += 1
                    elif event.event_type == EventType.TASK_COMPLETED:
                        total_tasks_completed += 1
            
            return {
                "status": "success",
                "period_days": days,
                "metrics": {
                    "learning_plans_generated": total_plans_generated,
                    "learning_plans_accepted": total_plans_accepted,
                    "plan_acceptance_rate": total_plans_accepted / total_plans_generated if total_plans_generated > 0 else 0,
                    "projects_created": total_projects_created,
                    "projects_completed": total_projects_completed,
                    "project_completion_rate": total_projects_completed / total_projects_created if total_projects_created > 0 else 0,
                    "tasks_completed": total_tasks_completed
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get learning metrics")

    async def get_system_metrics(
        self,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get basic system metrics (admin only)"""
        try:
            # Only admin users can access system metrics
            if not getattr(current_user, 'is_admin', False):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            # Get basic system information
            from ..models.user import User
            from ..models.chat import Conversation, Message
            
            total_users = db.query(User).count()
            total_conversations = db.query(Conversation).count()
            total_messages = db.query(Message).count()
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_users = db.query(User).filter(User.last_login >= yesterday).count()
            recent_conversations = db.query(Conversation).filter(Conversation.created_at >= yesterday).count()
            recent_messages = db.query(Message).filter(Message.created_at >= yesterday).count()
            
            return {
                "status": "success",
                "system_metrics": {
                    "total_users": total_users,
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "recent_activity_24h": {
                        "active_users": recent_users,
                        "new_conversations": recent_conversations,
                        "new_messages": recent_messages
                    }
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system metrics")

# Create router instance
router = AnalyticsRouter().router