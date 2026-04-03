"""
User onboarding analytics service for tracking user journey and drop-off analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from ..models.feedback import UserOnboardingAnalytics
from ..models.user import User
from ..database import get_db

logger = logging.getLogger(__name__)

class OnboardingAnalyticsService:
    """Service for tracking and analyzing user onboarding"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Define onboarding steps and their order
        self.onboarding_steps = {
            "welcome": {"order": 1, "name": "Welcome Screen"},
            "account_setup": {"order": 2, "name": "Account Setup"},
            "profile_creation": {"order": 3, "name": "Profile Creation"},
            "preferences": {"order": 4, "name": "Learning Preferences"},
            "first_chat": {"order": 5, "name": "First Chat Interaction"},
            "learning_plan": {"order": 6, "name": "Learning Plan Creation"},
            "onboarding_complete": {"order": 7, "name": "Onboarding Complete"}
        }
    
    async def start_onboarding_step(self, user_id: str, step_name: str, 
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start tracking an onboarding step"""
        try:
            if step_name not in self.onboarding_steps:
                return {"success": False, "error": f"Unknown onboarding step: {step_name}"}
            
            # Check if step already exists and is not completed
            existing_step = self.db.query(UserOnboardingAnalytics).filter(
                and_(
                    UserOnboardingAnalytics.user_id == user_id,
                    UserOnboardingAnalytics.step_name == step_name,
                    UserOnboardingAnalytics.completed_at.is_(None),
                    UserOnboardingAnalytics.abandoned_at.is_(None)
                )
            ).first()
            
            if existing_step:
                # Update existing step
                existing_step.started_at = datetime.now(timezone.utc)
                existing_step.metadata = metadata or {}
                self.db.commit()
                
                return {
                    "success": True,
                    "step_id": str(existing_step.id),
                    "message": "Onboarding step restarted"
                }
            
            # Create new step tracking
            step_analytics = UserOnboardingAnalytics(
                user_id=user_id,
                step_name=step_name,
                step_order=self.onboarding_steps[step_name]["order"],
                started_at=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            self.db.add(step_analytics)
            self.db.commit()
            self.db.refresh(step_analytics)
            
            logger.info(f"Onboarding step '{step_name}' started for user {user_id}")
            
            return {
                "success": True,
                "step_id": str(step_analytics.id),
                "message": "Onboarding step started"
            }
            
        except Exception as e:
            logger.error(f"Error starting onboarding step: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def complete_onboarding_step(self, user_id: str, step_name: str, 
                                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete an onboarding step"""
        try:
            # Find the active step
            step = self.db.query(UserOnboardingAnalytics).filter(
                and_(
                    UserOnboardingAnalytics.user_id == user_id,
                    UserOnboardingAnalytics.step_name == step_name,
                    UserOnboardingAnalytics.completed_at.is_(None),
                    UserOnboardingAnalytics.abandoned_at.is_(None)
                )
            ).first()
            
            if not step:
                return {"success": False, "error": "Active onboarding step not found"}
            
            # Complete the step
            now = datetime.now(timezone.utc)
            step.completed_at = now
            step.time_spent_seconds = int((now - step.started_at).total_seconds())
            step.completion_rate = 1.0
            
            # Update metadata if provided
            if metadata:
                step.metadata.update(metadata)
            
            self.db.commit()
            
            logger.info(f"Onboarding step '{step_name}' completed for user {user_id}")
            
            # Check if this was the last step
            is_onboarding_complete = step_name == "onboarding_complete"
            
            return {
                "success": True,
                "step_id": str(step.id),
                "time_spent_seconds": step.time_spent_seconds,
                "onboarding_complete": is_onboarding_complete,
                "message": "Onboarding step completed"
            }
            
        except Exception as e:
            logger.error(f"Error completing onboarding step: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def abandon_onboarding_step(self, user_id: str, step_name: str, 
                                    reason: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mark an onboarding step as abandoned"""
        try:
            # Find the active step
            step = self.db.query(UserOnboardingAnalytics).filter(
                and_(
                    UserOnboardingAnalytics.user_id == user_id,
                    UserOnboardingAnalytics.step_name == step_name,
                    UserOnboardingAnalytics.completed_at.is_(None),
                    UserOnboardingAnalytics.abandoned_at.is_(None)
                )
            ).first()
            
            if not step:
                return {"success": False, "error": "Active onboarding step not found"}
            
            # Mark as abandoned
            now = datetime.now(timezone.utc)
            step.abandoned_at = now
            step.time_spent_seconds = int((now - step.started_at).total_seconds())
            step.drop_off_reason = reason
            step.completion_rate = 0.0
            
            # Update metadata if provided
            if metadata:
                step.metadata.update(metadata)
            
            self.db.commit()
            
            logger.info(f"Onboarding step '{step_name}' abandoned for user {user_id}: {reason}")
            
            return {
                "success": True,
                "step_id": str(step.id),
                "time_spent_seconds": step.time_spent_seconds,
                "message": "Onboarding step marked as abandoned"
            }
            
        except Exception as e:
            logger.error(f"Error abandoning onboarding step: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_user_onboarding_progress(self, user_id: str) -> Dict[str, Any]:
        """Get onboarding progress for a specific user"""
        try:
            # Get all onboarding steps for user
            steps = self.db.query(UserOnboardingAnalytics).filter(
                UserOnboardingAnalytics.user_id == user_id
            ).order_by(UserOnboardingAnalytics.step_order).all()
            
            progress = {
                "user_id": user_id,
                "total_steps": len(self.onboarding_steps),
                "completed_steps": 0,
                "current_step": None,
                "completion_percentage": 0.0,
                "total_time_spent": 0,
                "steps": []
            }
            
            completed_steps = 0
            total_time = 0
            current_step = None
            
            for step in steps:
                step_info = {
                    "step_name": step.step_name,
                    "step_order": step.step_order,
                    "display_name": self.onboarding_steps.get(step.step_name, {}).get("name", step.step_name),
                    "started_at": step.started_at.isoformat(),
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "abandoned_at": step.abandoned_at.isoformat() if step.abandoned_at else None,
                    "time_spent_seconds": step.time_spent_seconds,
                    "completion_rate": step.completion_rate,
                    "drop_off_reason": step.drop_off_reason,
                    "status": "completed" if step.completed_at else ("abandoned" if step.abandoned_at else "in_progress")
                }
                
                progress["steps"].append(step_info)
                
                if step.completed_at:
                    completed_steps += 1
                elif not step.abandoned_at:
                    current_step = step.step_name
                
                if step.time_spent_seconds:
                    total_time += step.time_spent_seconds
            
            progress["completed_steps"] = completed_steps
            progress["current_step"] = current_step
            progress["completion_percentage"] = (completed_steps / len(self.onboarding_steps)) * 100
            progress["total_time_spent"] = total_time
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting user onboarding progress: {e}")
            return {"error": str(e)}
    
    async def get_onboarding_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive onboarding analytics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Total users who started onboarding
            total_users = self.db.query(UserOnboardingAnalytics.user_id).filter(
                UserOnboardingAnalytics.started_at >= cutoff_date
            ).distinct().count()
            
            # Users who completed onboarding
            completed_users = self.db.query(UserOnboardingAnalytics.user_id).filter(
                and_(
                    UserOnboardingAnalytics.step_name == "onboarding_complete",
                    UserOnboardingAnalytics.completed_at >= cutoff_date
                )
            ).distinct().count()
            
            # Overall completion rate
            overall_completion_rate = (completed_users / total_users * 100) if total_users > 0 else 0
            
            # Step-by-step analytics
            step_analytics = {}
            for step_name, step_info in self.onboarding_steps.items():
                # Users who started this step
                started = self.db.query(UserOnboardingAnalytics.user_id).filter(
                    and_(
                        UserOnboardingAnalytics.step_name == step_name,
                        UserOnboardingAnalytics.started_at >= cutoff_date
                    )
                ).distinct().count()
                
                # Users who completed this step
                completed = self.db.query(UserOnboardingAnalytics.user_id).filter(
                    and_(
                        UserOnboardingAnalytics.step_name == step_name,
                        UserOnboardingAnalytics.completed_at >= cutoff_date
                    )
                ).distinct().count()
                
                # Users who abandoned this step
                abandoned = self.db.query(UserOnboardingAnalytics.user_id).filter(
                    and_(
                        UserOnboardingAnalytics.step_name == step_name,
                        UserOnboardingAnalytics.abandoned_at >= cutoff_date
                    )
                ).distinct().count()
                
                # Average time spent on this step
                avg_time = self.db.query(func.avg(UserOnboardingAnalytics.time_spent_seconds)).filter(
                    and_(
                        UserOnboardingAnalytics.step_name == step_name,
                        UserOnboardingAnalytics.started_at >= cutoff_date,
                        UserOnboardingAnalytics.time_spent_seconds.isnot(None)
                    )
                ).scalar()
                
                # Drop-off reasons for this step
                drop_off_reasons = self.db.query(
                    UserOnboardingAnalytics.drop_off_reason,
                    func.count(UserOnboardingAnalytics.id).label('count')
                ).filter(
                    and_(
                        UserOnboardingAnalytics.step_name == step_name,
                        UserOnboardingAnalytics.abandoned_at >= cutoff_date,
                        UserOnboardingAnalytics.drop_off_reason.isnot(None)
                    )
                ).group_by(UserOnboardingAnalytics.drop_off_reason).all()
                
                step_analytics[step_name] = {
                    "display_name": step_info["name"],
                    "order": step_info["order"],
                    "users_started": started,
                    "users_completed": completed,
                    "users_abandoned": abandoned,
                    "completion_rate": (completed / started * 100) if started > 0 else 0,
                    "abandonment_rate": (abandoned / started * 100) if started > 0 else 0,
                    "average_time_seconds": float(avg_time) if avg_time else 0,
                    "drop_off_reasons": {reason[0]: reason[1] for reason in drop_off_reasons}
                }
            
            # Daily onboarding starts
            daily_starts = self.db.query(
                func.date(UserOnboardingAnalytics.started_at).label('date'),
                func.count(UserOnboardingAnalytics.user_id.distinct()).label('count')
            ).filter(
                and_(
                    UserOnboardingAnalytics.started_at >= cutoff_date,
                    UserOnboardingAnalytics.step_name == "welcome"
                )
            ).group_by(func.date(UserOnboardingAnalytics.started_at)).all()
            
            # Daily onboarding completions
            daily_completions = self.db.query(
                func.date(UserOnboardingAnalytics.completed_at).label('date'),
                func.count(UserOnboardingAnalytics.user_id.distinct()).label('count')
            ).filter(
                and_(
                    UserOnboardingAnalytics.completed_at >= cutoff_date,
                    UserOnboardingAnalytics.step_name == "onboarding_complete"
                )
            ).group_by(func.date(UserOnboardingAnalytics.completed_at)).all()
            
            return {
                "period_days": days,
                "summary": {
                    "total_users_started": total_users,
                    "total_users_completed": completed_users,
                    "overall_completion_rate": overall_completion_rate,
                    "overall_abandonment_rate": 100 - overall_completion_rate
                },
                "step_analytics": step_analytics,
                "daily_trends": {
                    "starts": [
                        {"date": item[0].isoformat(), "count": item[1]} 
                        for item in daily_starts
                    ],
                    "completions": [
                        {"date": item[0].isoformat(), "count": item[1]} 
                        for item in daily_completions
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding analytics: {e}")
            return {"error": str(e)}
    
    async def get_drop_off_analysis(self, step_name: str = None, days: int = 30) -> Dict[str, Any]:
        """Get detailed drop-off analysis"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = self.db.query(UserOnboardingAnalytics).filter(
                and_(
                    UserOnboardingAnalytics.abandoned_at >= cutoff_date,
                    UserOnboardingAnalytics.abandoned_at.isnot(None)
                )
            )
            
            if step_name:
                query = query.filter(UserOnboardingAnalytics.step_name == step_name)
            
            abandoned_steps = query.all()
            
            # Analyze drop-off patterns
            drop_off_by_step = {}
            drop_off_by_reason = {}
            drop_off_by_time_spent = {"0-30s": 0, "30s-2m": 0, "2m-5m": 0, "5m+": 0}
            
            for step in abandoned_steps:
                # By step
                step_name_key = step.step_name
                if step_name_key not in drop_off_by_step:
                    drop_off_by_step[step_name_key] = 0
                drop_off_by_step[step_name_key] += 1
                
                # By reason
                reason = step.drop_off_reason or "unknown"
                if reason not in drop_off_by_reason:
                    drop_off_by_reason[reason] = 0
                drop_off_by_reason[reason] += 1
                
                # By time spent
                if step.time_spent_seconds:
                    if step.time_spent_seconds <= 30:
                        drop_off_by_time_spent["0-30s"] += 1
                    elif step.time_spent_seconds <= 120:
                        drop_off_by_time_spent["30s-2m"] += 1
                    elif step.time_spent_seconds <= 300:
                        drop_off_by_time_spent["2m-5m"] += 1
                    else:
                        drop_off_by_time_spent["5m+"] += 1
            
            # Get recommendations based on patterns
            recommendations = self._generate_drop_off_recommendations(
                drop_off_by_step, drop_off_by_reason, drop_off_by_time_spent
            )
            
            return {
                "period_days": days,
                "step_filter": step_name,
                "total_drop_offs": len(abandoned_steps),
                "drop_off_by_step": drop_off_by_step,
                "drop_off_by_reason": drop_off_by_reason,
                "drop_off_by_time_spent": drop_off_by_time_spent,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting drop-off analysis: {e}")
            return {"error": str(e)}
    
    def _generate_drop_off_recommendations(self, by_step: Dict, by_reason: Dict, 
                                         by_time: Dict) -> List[str]:
        """Generate recommendations based on drop-off patterns"""
        recommendations = []
        
        # Analyze step patterns
        if by_step:
            highest_drop_off_step = max(by_step.items(), key=lambda x: x[1])
            if highest_drop_off_step[1] > 5:  # More than 5 drop-offs
                recommendations.append(
                    f"High drop-off rate in '{highest_drop_off_step[0]}' step. "
                    f"Consider simplifying or providing better guidance."
                )
        
        # Analyze reason patterns
        if "too_complex" in by_reason and by_reason["too_complex"] > 3:
            recommendations.append(
                "Users find the process too complex. Consider breaking down steps "
                "or providing more intuitive UI."
            )
        
        if "too_long" in by_reason and by_reason["too_long"] > 3:
            recommendations.append(
                "Users think the onboarding is too long. Consider reducing steps "
                "or making some optional."
            )
        
        # Analyze time patterns
        if by_time["0-30s"] > by_time["30s-2m"]:
            recommendations.append(
                "Many users drop off within 30 seconds. Improve initial engagement "
                "and make value proposition clearer."
            )
        
        if not recommendations:
            recommendations.append("No specific patterns detected. Continue monitoring.")
        
        return recommendations