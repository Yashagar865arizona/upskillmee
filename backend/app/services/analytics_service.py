"""
Enhanced analytics service combining conversation metrics and mentor effectiveness tracking.
"""

from typing import Dict, List, Optional, Any, Sequence, Type, TypeVar
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, select
from ..models.chat import Conversation, Message
from ..models.schemas import ConversationMetrics, ConversationSummary
from ..models.user import UserProject, UserSnapshot
import numpy as np
from collections import defaultdict
from pydantic import BaseModel
from ..config import settings
import json
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Types of user events to track"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    PROJECT_CREATED = "project_created"
    PROJECT_COMPLETED = "project_completed"
    LEARNING_PLAN_GENERATED = "learning_plan_generated"
    LEARNING_PLAN_ACCEPTED = "learning_plan_accepted"
    LEARNING_PLAN_REJECTED = "learning_plan_rejected"
    TASK_COMPLETED = "task_completed"
    PROFILE_UPDATED = "profile_updated"
    AGENT_MODE_SWITCHED = "agent_mode_switched"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    ERROR_OCCURRED = "error_occurred"

class UserEvent(BaseModel):
    """Model for tracking user events"""
    user_id: str
    event_type: EventType
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    session_id: Optional[str] = None
    
class ConversionFunnel(BaseModel):
    """Model for conversion funnel analysis"""
    stage: str
    users_entered: int
    users_completed: int
    conversion_rate: float
    avg_time_to_complete: float  # in minutes

T = TypeVar('T', bound=Any)

class EngagementMetrics(BaseModel):
    messages_per_day: float
    response_time_avg: float  # in seconds
    session_duration_avg: float  # in minutes
    active_days_streak: int
    project_completion_rate: float

class LearningMetrics(BaseModel):
    completed_projects: int
    active_projects: int
    skill_progress: Dict[str, float]  # skill -> progress percentage
    learning_pace: float  # relative to baseline
    milestone_completion_rate: float

class MentorEffectivenessMetrics(BaseModel):
    user_satisfaction: float  # based on explicit feedback
    concept_retention: float  # based on follow-up discussions
    progression_rate: float  # speed of advancing through difficulty levels
    engagement_score: float  # composite score of various engagement metrics

class AnalyticsService:
    def __init__(self):
        self.topic_weights = {
            'project_completion': 0.4,
            'message_engagement': 0.3,
            'quiz_performance': 0.3
        }
        self.interactions = {}
        self.interaction_metadata = defaultdict(list)
        self.engagement_thresholds = getattr(settings, 'ENGAGEMENT_THRESHOLDS', {})
        self.learning_pace_baseline = getattr(settings, 'LEARNING_PACE_BASELINE', 7.0)
        
        # Event tracking storage (in production, use Redis or database)
        self.user_events = defaultdict(list)
        self.session_events = defaultdict(list)
        
    async def track_event(self, db: Session, user_id: str, event_type: EventType, 
                         metadata: Dict[str, Any] = None, session_id: str = None,
                         ip_address: str = None, user_agent: str = None) -> None:
        """Track a user event for analytics"""
        try:
            from ..models.analytics import UserEvent as DBUserEvent
            
            # Create database event record
            db_event = DBUserEvent(
                user_id=user_id,
                event_type=event_type.value,
                event_metadata=metadata or {},
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(db_event)
            db.commit()
            
            # Also store in memory for quick access (keep last 100 events per user)
            event = UserEvent(
                user_id=user_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
                session_id=session_id
            )
            
            self.user_events[user_id].append(event)
            if session_id:
                self.session_events[session_id].append(event)
            
            # Keep only last 100 events per user in memory
            if len(self.user_events[user_id]) > 100:
                self.user_events[user_id] = self.user_events[user_id][-100:]
                
            logger.info(f"Tracked event {event_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            # Don't raise exception to avoid breaking user flow
            pass
    
    async def get_user_engagement_summary(self, db: Session, user_id: str, 
                                        days: int = 30) -> Dict[str, Any]:
        """Get comprehensive engagement summary for a user"""
        try:
            # Get events for the time period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            user_events = [
                event for event in self.user_events.get(user_id, [])
                if event.timestamp >= cutoff_date
            ]
            
            # Calculate engagement metrics
            engagement_metrics = await self.calculate_engagement_metrics(db, user_id)
            learning_metrics = await self.calculate_learning_metrics(db, user_id)
            
            # Event counts by type
            event_counts = defaultdict(int)
            for event in user_events:
                event_counts[event.event_type.value] += 1
            
            # Session analysis
            session_analysis = self._analyze_user_sessions(user_events)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "engagement_metrics": engagement_metrics.dict(),
                "learning_metrics": learning_metrics.dict(),
                "event_counts": dict(event_counts),
                "session_analysis": session_analysis,
                "total_events": len(user_events),
                "last_activity": max([e.timestamp for e in user_events]) if user_events else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement summary: {e}")
            return {}
    
    async def get_conversion_funnel_analysis(self, db: Session, 
                                           days: int = 30) -> List[ConversionFunnel]:
        """Analyze user conversion funnel"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Define funnel stages
            funnel_stages = [
                ("registration", [EventType.USER_LOGIN]),
                ("first_message", [EventType.MESSAGE_SENT]),
                ("learning_plan_generated", [EventType.LEARNING_PLAN_GENERATED]),
                ("learning_plan_accepted", [EventType.LEARNING_PLAN_ACCEPTED]),
                ("project_created", [EventType.PROJECT_CREATED]),
                ("task_completed", [EventType.TASK_COMPLETED]),
                ("project_completed", [EventType.PROJECT_COMPLETED])
            ]
            
            funnel_results = []
            all_users = set()
            
            # Collect all users who had any activity
            for user_events in self.user_events.values():
                for event in user_events:
                    if event.timestamp >= cutoff_date:
                        all_users.add(event.user_id)
            
            previous_stage_users = all_users
            
            for stage_name, event_types in funnel_stages:
                # Find users who completed this stage
                stage_users = set()
                stage_times = []
                
                for user_id in all_users:
                    user_events = self.user_events.get(user_id, [])
                    for event in user_events:
                        if (event.timestamp >= cutoff_date and 
                            event.event_type in event_types):
                            stage_users.add(user_id)
                            # Calculate time from first event to this stage
                            first_event_time = min([e.timestamp for e in user_events 
                                                  if e.timestamp >= cutoff_date])
                            stage_times.append((event.timestamp - first_event_time).total_seconds() / 60)
                            break
                
                users_entered = len(previous_stage_users)
                users_completed = len(stage_users & previous_stage_users)
                conversion_rate = users_completed / users_entered if users_entered > 0 else 0.0
                avg_time = np.mean(stage_times) if stage_times else 0.0
                
                funnel_results.append(ConversionFunnel(
                    stage=stage_name,
                    users_entered=users_entered,
                    users_completed=users_completed,
                    conversion_rate=conversion_rate,
                    avg_time_to_complete=avg_time
                ))
                
                previous_stage_users = stage_users
            
            return funnel_results
            
        except Exception as e:
            logger.error(f"Error analyzing conversion funnel: {e}")
            return []
    
    def _analyze_user_sessions(self, user_events: List[UserEvent]) -> Dict[str, Any]:
        """Analyze user session patterns"""
        try:
            if not user_events:
                return {}
            
            # Group events by session
            sessions = defaultdict(list)
            for event in user_events:
                if event.session_id:
                    sessions[event.session_id].append(event)
            
            if not sessions:
                return {"total_sessions": 0}
            
            # Calculate session metrics
            session_durations = []
            session_event_counts = []
            
            for session_events in sessions.values():
                if len(session_events) > 1:
                    session_events.sort(key=lambda x: x.timestamp)
                    duration = (session_events[-1].timestamp - session_events[0].timestamp).total_seconds() / 60
                    session_durations.append(duration)
                session_event_counts.append(len(session_events))
            
            return {
                "total_sessions": len(sessions),
                "avg_session_duration_minutes": np.mean(session_durations) if session_durations else 0.0,
                "avg_events_per_session": np.mean(session_event_counts) if session_event_counts else 0.0,
                "total_session_time_minutes": sum(session_durations) if session_durations else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user sessions: {e}")
            return {}
        
    async def get_conversation_metrics(
        self, 
        db: Session, 
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ConversationMetrics:
        """Get metrics for user conversations in the specified time range."""
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Get conversations in date range
            query = db.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= start_date,
                    Conversation.created_at <= end_date
                )
            )
            conversations = query.all()

            if not conversations:
                return ConversationMetrics(
                    total_messages=0,
                    average_response_time=0.0,
                    topics_covered=[],
                    learning_progress={},
                    last_active=start_date
                )

            # Calculate metrics
            total_messages = 0
            response_times = []
            topics = set()
            last_active = start_date

            for conv in conversations:
                messages = db.query(Message).filter(
                    Message.conversation_id == conv.id
                ).order_by(Message.created_at).all()
                
                total_messages += len(messages)
                
                # Calculate response times
                for i in range(1, len(messages)):
                    prev_role = db.query(Message.role).filter(Message.id == messages[i-1].id).scalar()
                    curr_role = db.query(Message.role).filter(Message.id == messages[i].id).scalar()
                    
                    if curr_role == 'assistant' and prev_role == 'user':
                        response_time = (messages[i].created_at - messages[i-1].created_at).total_seconds()
                        response_times.append(response_time)
                
                # Track topics
                topic = db.query(Conversation.topic).filter(Conversation.id == conv.id).scalar()
                if topic:
                    topics.add(topic)
                
                # Get the latest activity time
                conv_updated = db.query(Conversation.updated_at).filter(Conversation.id == conv.id).scalar()
                if conv_updated and conv_updated > last_active:
                    last_active = conv_updated

            # Calculate learning progress
            learning_progress = await self._calculate_learning_progress(db, user_id, list(topics))

            # Convert SQLAlchemy Column types to Python types
            avg_response_time = float(np.mean(response_times) if response_times else 0.0)
            last_active_time = datetime.fromtimestamp(last_active.timestamp())

            return ConversationMetrics(
                total_messages=total_messages,
                average_response_time=avg_response_time,
                topics_covered=list(topics),
                learning_progress=learning_progress,
                last_active=last_active_time
            )

        except Exception as e:
            logger.error(f"Error calculating conversation metrics: {e}")
            raise

    async def get_conversation_summaries(
        self, 
        db: Session, 
        user_id: str,
        limit: int = 10
    ) -> List[ConversationSummary]:
        """Get summaries of recent conversations."""
        try:
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(desc(Conversation.updated_at)).limit(limit).all()

            summaries = []
            for conv in conversations:
                last_message_query = db.query(Message).filter(
                    Message.conversation_id == conv.id
                ).order_by(desc(Message.created_at))
                last_message = last_message_query.first()

                message_count = db.query(func.count(Message.id)).filter(
                    Message.conversation_id == conv.id
                ).scalar()

                # Convert SQLAlchemy Column types to Python types
                created_time = datetime.fromtimestamp(conv.created_at.timestamp())
                updated_time = datetime.fromtimestamp(conv.updated_at.timestamp())
                message_text = str(last_message.content) if last_message else ""

                summaries.append(ConversationSummary(
                    id=str(conv.id),
                    topic=conv.topic or "General Discussion",
                    last_message=message_text,
                    message_count=message_count,
                    created_at=created_time,
                    updated_at=updated_time
                ))

            return summaries

        except Exception as e:
            logger.error(f"Error getting conversation summaries: {e}")
            raise

    async def _calculate_learning_progress(
        self, 
        db: Session, 
        user_id: str,
        topics: List[str]
    ) -> Dict[str, float]:
        """Calculate learning progress for each topic."""
        try:
            progress = {}
            # user_snapshot = db.query(UserSnapshot).filter(
            #     UserSnapshot.user_id == user_id
            # ).first()

            # if not user_snapshot:
            #     return {topic: 0.0 for topic in topics}

            for topic in topics:
                # Project completion progress
                project_progress = self._calculate_project_progress(db, user_id, topic)
                
                # Message engagement progress
                engagement_progress = self._calculate_engagement_progress(db, user_id, topic)
                
                # Quiz/assessment progress
                quiz_progress = self._calculate_quiz_progress(db, user_id, topic)
                
                # Weighted average of different progress indicators
                progress[topic] = (
                    project_progress * self.topic_weights['project_completion'] +
                    engagement_progress * self.topic_weights['message_engagement'] +
                    quiz_progress * self.topic_weights['quiz_performance']
                )

            return progress

        except Exception as e:
            logger.error(f"Error calculating learning progress: {e}")
            return {topic: 0.0 for topic in topics}

    def _calculate_project_progress(self, db: Session, user_id: str, topic: str) -> float:
        """Calculate progress based on project completion."""
        try:
            # Implementation would track project milestones and completion
            return 0.5  # Placeholder
        except Exception as e:
            logger.error(f"Error calculating project progress: {e}")
            return 0.0

    def _calculate_engagement_progress(self, db: Session, user_id: str, topic: str) -> float:
        """Calculate progress based on message engagement."""
        try:
            # Implementation would analyze message frequency and quality
            return 0.5  # Placeholder
        except Exception as e:
            logger.error(f"Error calculating engagement progress: {e}")
            return 0.0

    def _calculate_quiz_progress(self, db: Session, user_id: str, topic: str) -> float:
        """Calculate progress based on quiz performance."""
        try:
            # Implementation would track quiz scores and completion
            return 0.5  # Placeholder
        except Exception as e:
            logger.error(f"Error calculating quiz progress: {e}")
            return 0.0

    async def log_interaction(self, user_id: str, message: Message, result: Dict[str, Any]) -> None:
        """Log user interaction for analytics"""
        try:
            # Log basic interaction metrics
            self.interactions[user_id] = self.interactions.get(user_id, 0) + 1
            
            # Store metadata
            self.interaction_metadata[user_id].append({
                'message_id': message.id,
                'timestamp': datetime.now(timezone.utc),
                'response_time': result.get('metadata', {}).get('response_time', 0),
                'has_learning_plan': 'plan' in result,
                'context_used': result.get('metadata', {}).get('context_used', False)
            })
            
            # Cleanup old metadata (keep last 100 interactions)
            if len(self.interaction_metadata[user_id]) > 100:
                self.interaction_metadata[user_id] = self.interaction_metadata[user_id][-100:]
                
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")

    def process_analytics_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process analytics data and return enriched metrics"""
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
            
        try:
            return {
                "user_metrics": self._process_metrics(data.get("user_data", {}), ["active_time", "interaction_count", "session_duration"]),
                "system_metrics": self._process_metrics(data.get("system_data", {}), ["cpu_usage", "memory_usage", "network_latency"]),
                "performance_metrics": self._process_metrics(data.get("performance_data", {}), ["response_time", "error_rate", "throughput"])
            }
        except Exception as e:
            logger.error(f"Error processing analytics data: {str(e)}")
            raise

    def _process_metrics(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Generic method to process metrics data"""
        if not data:
            return {}
            
        metrics = {}
        try:
            for field in fields:
                value = data.get(field, 0)
                metrics[field] = float(value) if isinstance(value, (int, float, str)) else 0.0
            return metrics
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing metrics: {str(e)}")
            return {}

    # Mentor Metrics Methods
    def _execute_count_query(self, db: Session, model_class: Type[Any], conditions: List) -> int:
        """Execute a count query with conditions."""
        try:
            query = db.query(func.count(model_class.id)).filter(and_(*conditions))
            return query.scalar() or 0
        except Exception as e:
            logger.error(f"Error executing count query: {e}")
            return 0
    
    def _get_user_projects(self, db: Session, user_id: str, status: Optional[str] = None, 
                           time_window: Optional[timedelta] = None) -> List[UserProject]:
        """Get user projects with optional filters."""
        try:
            query = db.query(UserProject).filter(UserProject.user_id == user_id)
            
            if status:
                query = query.filter(UserProject.status == status)
                
            if time_window:
                cutoff_date = datetime.now(timezone.utc) - time_window
                query = query.filter(UserProject.created_at >= cutoff_date)
                
            return query.all()
        except Exception as e:
            logger.error(f"Error getting user projects: {e}")
            return []

    def _get_user_messages(self, db: Session, user_id: str, 
                          time_window: Optional[timedelta] = None,
                          has_feedback: bool = False) -> List[Message]:
        """Get user messages with optional filters."""
        try:
            query = db.query(Message).join(Conversation).filter(
                Conversation.user_id == user_id
            )
            
            if time_window:
                cutoff_date = datetime.now(timezone.utc) - time_window
                query = query.filter(Message.created_at >= cutoff_date)
                
            if has_feedback:
                query = query.filter(Message.feedback.isnot(None))
                
            return query.all()
        except Exception as e:
            logger.error(f"Error getting user messages: {e}")
            return []

    def _get_latest_user_snapshot(self, db: Session, user_id: str) -> Optional[UserSnapshot]:
        """Get the latest user snapshot"""
        stmt = select(UserSnapshot).where(
            UserSnapshot.user_id == user_id
        ).order_by(desc(UserSnapshot.created_at))
        return db.execute(stmt).scalar()

    async def calculate_engagement_metrics(
        self, 
        db: Session, 
        user_id: str,
        time_window: timedelta = timedelta(days=30)
    ) -> EngagementMetrics:
        """Calculate engagement metrics for a user."""
        try:
            cutoff_date = datetime.now(timezone.utc) - time_window
            
            # Get messages in time window
            messages = self._get_user_messages(db, user_id, time_window)
            if not messages:
                return EngagementMetrics(
                    messages_per_day=0.0,
                    response_time_avg=0.0,
                    session_duration_avg=0.0,
                    active_days_streak=0,
                    project_completion_rate=0.0
                )
            
            # Calculate messages per day
            message_dates = [msg.created_at for msg in messages]
            unique_days = len(set(date.date() for date in message_dates))
            messages_per_day = float(len(messages)) / unique_days if unique_days > 0 else 0.0
            
            # Calculate response time average
            response_times = []
            for i in range(1, len(messages)):
                if str(messages[i].role) == 'assistant' and str(messages[i-1].role) == 'user':
                    response_time = (messages[i].created_at - messages[i-1].created_at).total_seconds()
                    response_times.append(response_time)
            response_time_avg = float(np.mean(response_times)) if response_times else 0.0
            
            # Calculate session durations
            session_durations = self._get_session_durations(db, user_id, cutoff_date)
            session_duration_avg = float(np.mean(session_durations)) if session_durations else 0.0
            
            # Calculate active days streak
            timestamps = [datetime.fromtimestamp(msg.created_at.timestamp()) for msg in messages]
            active_days_streak = self._calculate_streak(timestamps)
            
            # Calculate project completion rate
            projects = self._get_user_projects(db, user_id, time_window=time_window)
            completed_projects = sum(1 for p in projects if str(p.status) == 'completed')
            project_completion_rate = float(completed_projects) / len(projects) if projects else 0.0
            
            return EngagementMetrics(
                messages_per_day=messages_per_day,
                response_time_avg=response_time_avg,
                session_duration_avg=session_duration_avg,
                active_days_streak=active_days_streak,
                project_completion_rate=project_completion_rate
            )
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return EngagementMetrics(
                messages_per_day=0.0,
                response_time_avg=0.0,
                session_duration_avg=0.0,
                active_days_streak=0,
                project_completion_rate=0.0
            )

    async def calculate_learning_metrics(
        self,
        db: Session,
        user_id: str
    ) -> LearningMetrics:
        """Calculate learning metrics for a user."""
        try:
            # Get user projects
            projects = self._get_user_projects(db, user_id)
            completed_projects = sum(1 for p in projects if str(p.status) == 'completed')
            active_projects = sum(1 for p in projects if str(p.status) == 'in_progress')
            
            # Get user snapshots for learning pace
            snapshots = db.query(UserSnapshot).filter(
                UserSnapshot.user_id == user_id
            ).order_by(UserSnapshot.created_at).all()
            
            # Calculate metrics
            skill_progress = await self._calculate_learning_progress(db, user_id, [])
            learning_pace = self._calculate_learning_pace(snapshots)
            milestone_rate = self._calculate_milestone_rate(projects)
            
            return LearningMetrics(
                completed_projects=completed_projects,
                active_projects=active_projects,
                skill_progress=skill_progress,
                learning_pace=learning_pace,
                milestone_completion_rate=milestone_rate
            )
            
        except Exception as e:
            logger.error(f"Error calculating learning metrics: {e}")
            return LearningMetrics(
                completed_projects=0,
                active_projects=0,
                skill_progress={},
                learning_pace=0.0,
                milestone_completion_rate=0.0
            )

    def _calculate_streak(self, timestamps: Sequence[datetime]) -> int:
        """Calculate the longest streak of consecutive days with activity."""
        try:
            if not timestamps:
                return 0
                
            # Convert to dates and sort
            dates = sorted(set(ts.date() for ts in timestamps))
            if not dates:
                return 0
                
            # Calculate streak
            current_streak = 1
            max_streak = 1
            for i in range(1, len(dates)):
                if (dates[i] - dates[i-1]).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
                    
            return max_streak
            
        except Exception as e:
            logger.error(f"Error calculating streak: {e}")
            return 0

    def _calculate_learning_pace(self, snapshots: List[UserSnapshot]) -> float:
        """Calculate the learning pace relative to baseline."""
        try:
            if not snapshots:
                return 0.0
                
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(snapshots, key=lambda x: x.created_at.timestamp())
            
            # Calculate average time between snapshots
            time_diffs = []
            for i in range(1, len(sorted_snapshots)):
                time_diff = (sorted_snapshots[i].created_at - sorted_snapshots[i-1].created_at).days
                if time_diff > 0:
                    time_diffs.append(time_diff)
                    
            if not time_diffs:
                return 0.0
                
            avg_time = float(np.mean(time_diffs))
            return self.learning_pace_baseline / avg_time if avg_time > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating learning pace: {e}")
            return 0.0

    def _calculate_milestone_rate(self, projects: List[UserProject]) -> float:
        """Calculate the rate of milestone completion."""
        try:
            if not projects:
                return 0.0
                
            # Count completed milestones
            completed_milestones = sum(
                len(p.milestones) for p in projects 
                if hasattr(p, 'milestones') and p.milestones
            )
            
            # Calculate rate
            total_days = sum(
                (datetime.fromtimestamp(p.updated_at.timestamp()) - datetime.fromtimestamp(p.created_at.timestamp())).days 
                for p in projects 
                if p.updated_at is not None and p.created_at is not None
            )
            
            if total_days == 0:
                return 0.0
                
            return float(completed_milestones) / total_days
            
        except Exception as e:
            logger.error(f"Error calculating milestone rate: {e}")
            return 0.0

    async def _calculate_retention(self, db: Session, user_id: str) -> float:
        """Calculate concept retention from follow-up discussions."""
        try:
            # Get messages with follow-up discussions
            messages = self._get_user_messages(db, user_id, has_feedback=True)
            if not messages:
                return 0.0
                
            # Calculate retention score based on feedback
            feedback_scores = []
            for msg in messages:
                if hasattr(msg, 'feedback') and msg.feedback:
                    try:
                        score = float(msg.feedback)
                        if 0 <= score <= 1:
                            feedback_scores.append(score)
                    except (ValueError, TypeError):
                        continue
                        
            if not feedback_scores:
                return 0.0
                
            return float(np.mean(feedback_scores))
            
        except Exception as e:
            logger.error(f"Error calculating retention: {e}")
            return 0.0

    def _calculate_engagement_score(self, metrics: EngagementMetrics) -> float:
        """Calculate composite engagement score."""
        try:
            # Normalize metrics to 0-1 range
            normalized_metrics = {
                'messages_per_day': min(metrics.messages_per_day / 10.0, 1.0),
                'response_time_avg': 1.0 - min(metrics.response_time_avg / 3600.0, 1.0),
                'session_duration_avg': min(metrics.session_duration_avg / 60.0, 1.0),
                'active_days_streak': min(metrics.active_days_streak / 7.0, 1.0),
                'project_completion_rate': metrics.project_completion_rate
            }
            
            # Weight the metrics
            weights = {
                'messages_per_day': 0.3,
                'response_time_avg': 0.2,
                'session_duration_avg': 0.2,
                'active_days_streak': 0.15,
                'project_completion_rate': 0.15
            }
            
            return sum(normalized_metrics[key] * weight for key, weight in weights.items())
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    def _get_session_durations(self, db: Session, user_id: str, cutoff_date: datetime) -> List[float]:
        """Get session durations in minutes."""
        try:
            # Get unique session IDs
            sessions_stmt = select(Message.session_id).distinct().join(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    Message.created_at >= cutoff_date
                )
            )
            session_ids = [row[0] for row in db.execute(sessions_stmt).all()]
            
            durations = []
            for session_id in session_ids:
                # Get first and last message in session
                messages = db.query(Message).filter(
                    Message.session_id == session_id
                ).order_by(Message.created_at).all()
                
                if len(messages) >= 2:
                    duration = (messages[-1].created_at - messages[0].created_at).total_seconds() / 60
                    durations.append(duration)
                    
            return durations
        except Exception as e:
            logger.error(f"Error getting session durations: {e}")
            return []

    def _calculate_satisfaction_from_feedback(self, messages: List[Message]) -> float:
        """Calculate user satisfaction from feedback in messages."""
        try:
            feedback_scores = []
            for msg in messages:
                if hasattr(msg, 'feedback') and msg.feedback:
                    # Assuming feedback is a float between 0 and 1
                    score = float(msg.feedback)
                    if 0 <= score <= 1:
                        feedback_scores.append(score)
            
            return float(np.mean(feedback_scores)) if feedback_scores else 0.5
        except Exception as e:
            logger.error(f"Error calculating satisfaction: {e}")
            return 0.5

    def _calculate_progression_rate(self, snapshots: List[UserSnapshot]) -> float:
        """Calculate the rate of progression through difficulty levels."""
        try:
            if not snapshots:
                return 0.0
                
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(snapshots, key=lambda x: x.created_at.timestamp())
            
            # Calculate progression rate based on difficulty level changes
            progression_steps = 0
            for i in range(1, len(sorted_snapshots)):
                if sorted_snapshots[i].difficulty_level > sorted_snapshots[i-1].difficulty_level:
                    progression_steps += 1
            
            # Normalize by time span
            time_span = (sorted_snapshots[-1].created_at - sorted_snapshots[0].created_at).days
            if time_span == 0:
                return 0.0
                
            return float(progression_steps) / time_span
        except Exception as e:
            logger.error(f"Error calculating progression rate: {e}")
            return 0.0
