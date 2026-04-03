"""
API endpoints for user feedback collection and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
import logging

from ..services.feedback_service import FeedbackService, SupportTicketService, FeatureUsageService
from ..services.onboarding_analytics_service import OnboardingAnalyticsService
from ..services.ab_testing_service import ABTestingService
from ..dependencies import get_current_user
from ..models.user import User
from ..database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

feedback_router = APIRouter()

# Dependency to get services
def get_feedback_service(db: Session = Depends(get_db)):
    return FeedbackService(db)

def get_support_service(db: Session = Depends(get_db)):
    return SupportTicketService(db)

def get_feature_usage_service(db: Session = Depends(get_db)):
    return FeatureUsageService(db)

def get_onboarding_service(db: Session = Depends(get_db)):
    return OnboardingAnalyticsService(db)

def get_ab_testing_service(db: Session = Depends(get_db)):
    return ABTestingService(db)

# Feedback endpoints
@feedback_router.post("/submit")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Submit user feedback"""
    try:
        result = await feedback_service.submit_feedback(
            user_id=str(current_user.id),
            feedback_data=feedback_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "feedback_id": result["feedback_id"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@feedback_router.get("/my-feedback")
async def get_my_feedback(
    limit: int = Query(50, description="Maximum number of feedback items to return"),
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get feedback submitted by current user"""
    try:
        feedback_items = await feedback_service.get_user_feedback(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {
            "status": "success",
            "feedback": feedback_items,
            "count": len(feedback_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting user feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback")

@feedback_router.get("/analytics")
async def get_feedback_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get feedback analytics (admin only)"""
    try:
        # Only admin users can access analytics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics = await feedback_service.get_feedback_analytics(days=days)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@feedback_router.post("/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: str,
    response_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Respond to user feedback (admin only)"""
    try:
        # Only admin users can respond to feedback
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if "response_text" not in response_data:
            raise HTTPException(status_code=400, detail="Missing response_text")
        
        result = await feedback_service.respond_to_feedback(
            feedback_id=feedback_id,
            admin_user_id=str(current_user.id),
            response_text=response_data["response_text"],
            is_public=response_data.get("is_public", True)
        )
        
        if result["success"]:
            return {
                "status": "success",
                "response_id": result["response_id"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to respond to feedback")

# Support ticket endpoints
@feedback_router.post("/support/tickets")
async def create_support_ticket(
    ticket_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    support_service: SupportTicketService = Depends(get_support_service)
):
    """Create a new support ticket"""
    try:
        required_fields = ["subject", "description"]
        for field in required_fields:
            if field not in ticket_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        result = await support_service.create_ticket(
            user_id=str(current_user.id),
            ticket_data=ticket_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "ticket_id": result["ticket_id"],
                "ticket_number": result["ticket_number"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create support ticket")

@feedback_router.get("/support/tickets")
async def get_my_support_tickets(
    limit: int = Query(50, description="Maximum number of tickets to return"),
    current_user: User = Depends(get_current_user),
    support_service: SupportTicketService = Depends(get_support_service)
):
    """Get support tickets for current user"""
    try:
        tickets = await support_service.get_user_tickets(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {
            "status": "success",
            "tickets": tickets,
            "count": len(tickets)
        }
        
    except Exception as e:
        logger.error(f"Error getting user tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tickets")

@feedback_router.post("/support/tickets/{ticket_id}/messages")
async def add_ticket_message(
    ticket_id: str,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    support_service: SupportTicketService = Depends(get_support_service)
):
    """Add message to support ticket"""
    try:
        if "message_text" not in message_data:
            raise HTTPException(status_code=400, detail="Missing message_text")
        
        result = await support_service.add_message(
            ticket_id=ticket_id,
            sender_id=str(current_user.id),
            message_text=message_data["message_text"],
            is_internal=message_data.get("is_internal", False)
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message_id": result["message_id"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding ticket message: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")

@feedback_router.get("/support/tickets/{ticket_id}/messages")
async def get_ticket_messages(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    support_service: SupportTicketService = Depends(get_support_service)
):
    """Get messages for a support ticket"""
    try:
        messages = await support_service.get_ticket_messages(
            ticket_id=ticket_id,
            user_id=str(current_user.id)
        )
        
        return {
            "status": "success",
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting ticket messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

# Feature usage analytics endpoints
@feedback_router.post("/usage/track")
async def track_feature_usage(
    usage_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    usage_service: FeatureUsageService = Depends(get_feature_usage_service)
):
    """Track feature usage event"""
    try:
        required_fields = ["feature_name", "action"]
        for field in required_fields:
            if field not in usage_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        success = await usage_service.track_feature_usage(
            user_id=str(current_user.id),
            feature_name=usage_data["feature_name"],
            action=usage_data["action"],
            metadata=usage_data.get("metadata"),
            session_id=usage_data.get("session_id"),
            page_url=usage_data.get("page_url"),
            user_agent=usage_data.get("user_agent")
        )
        
        if success:
            return {
                "status": "success",
                "message": "Feature usage tracked successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to track feature usage")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking feature usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to track feature usage")

@feedback_router.get("/usage/analytics")
async def get_feature_usage_analytics(
    feature_name: Optional[str] = Query(None, description="Specific feature to analyze"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    usage_service: FeatureUsageService = Depends(get_feature_usage_service)
):
    """Get feature usage analytics (admin only)"""
    try:
        # Only admin users can access analytics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics = await usage_service.get_feature_analytics(
            feature_name=feature_name,
            days=days
        )
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature usage analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# Onboarding analytics endpoints
@feedback_router.post("/onboarding/start-step")
async def start_onboarding_step(
    step_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    onboarding_service: OnboardingAnalyticsService = Depends(get_onboarding_service)
):
    """Start tracking an onboarding step"""
    try:
        if "step_name" not in step_data:
            raise HTTPException(status_code=400, detail="Missing step_name")
        
        result = await onboarding_service.start_onboarding_step(
            user_id=str(current_user.id),
            step_name=step_data["step_name"],
            metadata=step_data.get("metadata")
        )
        
        if result["success"]:
            return {
                "status": "success",
                "step_id": result["step_id"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting onboarding step: {e}")
        raise HTTPException(status_code=500, detail="Failed to start onboarding step")

@feedback_router.post("/onboarding/complete-step")
async def complete_onboarding_step(
    step_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    onboarding_service: OnboardingAnalyticsService = Depends(get_onboarding_service)
):
    """Complete an onboarding step"""
    try:
        if "step_name" not in step_data:
            raise HTTPException(status_code=400, detail="Missing step_name")
        
        result = await onboarding_service.complete_onboarding_step(
            user_id=str(current_user.id),
            step_name=step_data["step_name"],
            metadata=step_data.get("metadata")
        )
        
        if result["success"]:
            return {
                "status": "success",
                "step_id": result["step_id"],
                "time_spent_seconds": result["time_spent_seconds"],
                "onboarding_complete": result["onboarding_complete"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing onboarding step: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding step")

@feedback_router.get("/onboarding/progress")
async def get_onboarding_progress(
    current_user: User = Depends(get_current_user),
    onboarding_service: OnboardingAnalyticsService = Depends(get_onboarding_service)
):
    """Get onboarding progress for current user"""
    try:
        progress = await onboarding_service.get_user_onboarding_progress(
            user_id=str(current_user.id)
        )
        
        if "error" in progress:
            raise HTTPException(status_code=500, detail=progress["error"])
        
        return {
            "status": "success",
            "progress": progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding progress")

@feedback_router.get("/onboarding/analytics")
async def get_onboarding_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    onboarding_service: OnboardingAnalyticsService = Depends(get_onboarding_service)
):
    """Get onboarding analytics (admin only)"""
    try:
        # Only admin users can access analytics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics = await onboarding_service.get_onboarding_analytics(days=days)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return {
            "status": "success",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting onboarding analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

# A/B testing endpoints
@feedback_router.get("/ab-tests/assignment/{feature_flag}")
async def get_ab_test_assignment(
    feature_flag: str,
    current_user: User = Depends(get_current_user),
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get A/B test variant assignment for user"""
    try:
        # Get user attributes for targeting (simplified)
        user_attributes = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
        
        result = await ab_service.assign_user_to_experiment(
            user_id=str(current_user.id),
            feature_flag=feature_flag,
            user_attributes=user_attributes
        )
        
        if result["success"]:
            return {
                "status": "success",
                "variant": result["variant"],
                "experiment_id": result["experiment_id"],
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to get A/B test assignment")

@feedback_router.post("/ab-tests/conversion")
async def track_ab_test_conversion(
    conversion_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Track A/B test conversion event"""
    try:
        required_fields = ["experiment_id", "event_name"]
        for field in required_fields:
            if field not in conversion_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        result = await ab_service.track_conversion_event(
            user_id=str(current_user.id),
            experiment_id=conversion_data["experiment_id"],
            event_name=conversion_data["event_name"],
            event_data=conversion_data.get("event_data")
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking A/B test conversion: {e}")
        raise HTTPException(status_code=500, detail="Failed to track conversion")

@feedback_router.get("/ab-tests/my-experiments")
async def get_my_ab_test_experiments(
    current_user: User = Depends(get_current_user),
    ab_service: ABTestingService = Depends(get_ab_testing_service)
):
    """Get A/B test experiments user is participating in"""
    try:
        experiments = await ab_service.get_user_experiments(
            user_id=str(current_user.id)
        )
        
        return {
            "status": "success",
            "experiments": experiments,
            "count": len(experiments)
        }
        
    except Exception as e:
        logger.error(f"Error getting user A/B test experiments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get experiments")

# Create router instance
router = feedback_router