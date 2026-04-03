"""
A/B testing service for feature experimentation and optimization.
"""

import logging
import hashlib
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from ..models.feedback import ABTestExperiment, ABTestParticipation
from ..models.user import User
from ..database import get_db

logger = logging.getLogger(__name__)

class ABTestingService:
    """Service for managing A/B testing experiments"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_experiment(self, creator_id: str, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new A/B testing experiment"""
        try:
            # Validate experiment data
            required_fields = ["name", "feature_flag", "variants", "traffic_allocation", "success_metrics"]
            for field in required_fields:
                if field not in experiment_data:
                    return {"success": False, "error": f"Missing required field: {field}"}
            
            # Validate traffic allocation sums to 100
            total_allocation = sum(experiment_data["traffic_allocation"].values())
            if abs(total_allocation - 100.0) > 0.01:
                return {"success": False, "error": "Traffic allocation must sum to 100%"}
            
            # Validate variants match allocation keys
            variant_names = set(experiment_data["variants"].keys())
            allocation_names = set(experiment_data["traffic_allocation"].keys())
            if variant_names != allocation_names:
                return {"success": False, "error": "Variant names must match traffic allocation keys"}
            
            experiment = ABTestExperiment(
                name=experiment_data["name"],
                description=experiment_data.get("description"),
                feature_flag=experiment_data["feature_flag"],
                variants=experiment_data["variants"],
                traffic_allocation=experiment_data["traffic_allocation"],
                target_audience=experiment_data.get("target_audience"),
                success_metrics=experiment_data["success_metrics"],
                created_by=creator_id
            )
            
            self.db.add(experiment)
            self.db.commit()
            self.db.refresh(experiment)
            
            logger.info(f"A/B test experiment created: {experiment.name} by user {creator_id}")
            
            return {
                "success": True,
                "experiment_id": str(experiment.id),
                "message": "Experiment created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating A/B test experiment: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def start_experiment(self, experiment_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Start an A/B testing experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                return {"success": False, "error": "Experiment not found"}
            
            if experiment.status != "draft":
                return {"success": False, "error": f"Cannot start experiment in {experiment.status} status"}
            
            experiment.status = "active"
            experiment.start_date = datetime.now(timezone.utc)
            experiment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"A/B test experiment started: {experiment.name}")
            
            return {
                "success": True,
                "message": "Experiment started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting A/B test experiment: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def stop_experiment(self, experiment_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Stop an A/B testing experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                return {"success": False, "error": "Experiment not found"}
            
            if experiment.status != "active":
                return {"success": False, "error": f"Cannot stop experiment in {experiment.status} status"}
            
            experiment.status = "completed"
            experiment.end_date = datetime.now(timezone.utc)
            experiment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"A/B test experiment stopped: {experiment.name}")
            
            return {
                "success": True,
                "message": "Experiment stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping A/B test experiment: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def assign_user_to_experiment(self, user_id: str, feature_flag: str, 
                                      user_attributes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Assign a user to an active experiment variant"""
        try:
            # Find active experiment for this feature flag
            experiment = self.db.query(ABTestExperiment).filter(
                and_(
                    ABTestExperiment.feature_flag == feature_flag,
                    ABTestExperiment.status == "active"
                )
            ).first()
            
            if not experiment:
                return {
                    "success": True,
                    "variant": "control",
                    "experiment_id": None,
                    "message": "No active experiment found, using control"
                }
            
            # Check if user is already assigned to this experiment
            existing_participation = self.db.query(ABTestParticipation).filter(
                and_(
                    ABTestParticipation.user_id == user_id,
                    ABTestParticipation.experiment_id == experiment.id
                )
            ).first()
            
            if existing_participation:
                return {
                    "success": True,
                    "variant": existing_participation.variant,
                    "experiment_id": str(experiment.id),
                    "message": "User already assigned to experiment"
                }
            
            # Check if user matches target audience
            if not self._user_matches_target_audience(user_attributes or {}, experiment.target_audience):
                return {
                    "success": True,
                    "variant": "control",
                    "experiment_id": None,
                    "message": "User does not match target audience"
                }
            
            # Assign user to variant based on traffic allocation
            variant = self._assign_variant(user_id, experiment.traffic_allocation)
            
            # Create participation record
            participation = ABTestParticipation(
                experiment_id=experiment.id,
                user_id=user_id,
                variant=variant,
                metadata=user_attributes or {}
            )
            
            self.db.add(participation)
            self.db.commit()
            self.db.refresh(participation)
            
            logger.info(f"User {user_id} assigned to variant '{variant}' in experiment {experiment.name}")
            
            return {
                "success": True,
                "variant": variant,
                "experiment_id": str(experiment.id),
                "participation_id": str(participation.id),
                "message": "User assigned to experiment variant"
            }
            
        except Exception as e:
            logger.error(f"Error assigning user to experiment: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _user_matches_target_audience(self, user_attributes: Dict[str, Any], 
                                    target_audience: Optional[Dict[str, Any]]) -> bool:
        """Check if user matches experiment target audience criteria"""
        if not target_audience:
            return True  # No targeting criteria means all users qualify
        
        for criterion, expected_value in target_audience.items():
            user_value = user_attributes.get(criterion)
            
            if isinstance(expected_value, list):
                # Multiple acceptable values
                if user_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict):
                # Range or comparison criteria
                if "min" in expected_value and user_value < expected_value["min"]:
                    return False
                if "max" in expected_value and user_value > expected_value["max"]:
                    return False
            else:
                # Exact match
                if user_value != expected_value:
                    return False
        
        return True
    
    def _assign_variant(self, user_id: str, traffic_allocation: Dict[str, float]) -> str:
        """Assign user to variant based on traffic allocation"""
        # Use consistent hashing to ensure same user always gets same variant
        hash_input = f"{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        percentage = (hash_value % 10000) / 100.0  # 0-99.99
        
        # Assign based on cumulative percentages
        cumulative = 0.0
        for variant, allocation in traffic_allocation.items():
            cumulative += allocation
            if percentage < cumulative:
                return variant
        
        # Fallback to first variant (shouldn't happen if allocation sums to 100)
        return list(traffic_allocation.keys())[0]
    
    async def track_conversion_event(self, user_id: str, experiment_id: str, 
                                   event_name: str, event_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track a conversion event for A/B test analysis"""
        try:
            # Find user's participation in experiment
            participation = self.db.query(ABTestParticipation).filter(
                and_(
                    ABTestParticipation.user_id == user_id,
                    ABTestParticipation.experiment_id == experiment_id
                )
            ).first()
            
            if not participation:
                return {"success": False, "error": "User not participating in experiment"}
            
            # Update first exposure time if not set
            if not participation.first_exposure_at:
                participation.first_exposure_at = datetime.now(timezone.utc)
            
            # Add conversion event
            if not participation.conversion_events:
                participation.conversion_events = []
            
            conversion_event = {
                "event_name": event_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": event_data or {}
            }
            
            participation.conversion_events.append(conversion_event)
            
            # Mark as modified for SQLAlchemy to detect JSON changes
            self.db.merge(participation)
            self.db.commit()
            
            logger.info(f"Conversion event '{event_name}' tracked for user {user_id} in experiment {experiment_id}")
            
            return {
                "success": True,
                "message": "Conversion event tracked successfully"
            }
            
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get comprehensive results for an A/B test experiment"""
        try:
            experiment = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.id == experiment_id
            ).first()
            
            if not experiment:
                return {"success": False, "error": "Experiment not found"}
            
            # Get all participations
            participations = self.db.query(ABTestParticipation).filter(
                ABTestParticipation.experiment_id == experiment_id
            ).all()
            
            # Analyze results by variant
            variant_results = {}
            total_participants = len(participations)
            
            for variant_name in experiment.variants.keys():
                variant_participants = [p for p in participations if p.variant == variant_name]
                variant_count = len(variant_participants)
                
                # Calculate conversion rates for each success metric
                conversions = {}
                for metric in experiment.success_metrics:
                    metric_name = metric["name"]
                    converted_users = 0
                    
                    for participation in variant_participants:
                        if participation.conversion_events:
                            for event in participation.conversion_events:
                                if event["event_name"] == metric_name:
                                    converted_users += 1
                                    break
                    
                    conversion_rate = (converted_users / variant_count * 100) if variant_count > 0 else 0
                    conversions[metric_name] = {
                        "converted_users": converted_users,
                        "conversion_rate": conversion_rate
                    }
                
                # Calculate average time to first exposure
                exposure_times = [
                    (p.first_exposure_at - p.assigned_at).total_seconds()
                    for p in variant_participants 
                    if p.first_exposure_at and p.assigned_at
                ]
                avg_exposure_time = sum(exposure_times) / len(exposure_times) if exposure_times else 0
                
                variant_results[variant_name] = {
                    "participants": variant_count,
                    "percentage_of_total": (variant_count / total_participants * 100) if total_participants > 0 else 0,
                    "conversions": conversions,
                    "average_exposure_time_seconds": avg_exposure_time,
                    "exposure_rate": (len(exposure_times) / variant_count * 100) if variant_count > 0 else 0
                }
            
            # Calculate statistical significance (simplified)
            significance_results = self._calculate_statistical_significance(variant_results, experiment.success_metrics)
            
            # Get daily participation trends
            daily_participations = self.db.query(
                func.date(ABTestParticipation.assigned_at).label('date'),
                ABTestParticipation.variant,
                func.count(ABTestParticipation.id).label('count')
            ).filter(
                ABTestParticipation.experiment_id == experiment_id
            ).group_by(
                func.date(ABTestParticipation.assigned_at),
                ABTestParticipation.variant
            ).all()
            
            daily_trends = {}
            for date, variant, count in daily_participations:
                date_str = date.isoformat()
                if date_str not in daily_trends:
                    daily_trends[date_str] = {}
                daily_trends[date_str][variant] = count
            
            return {
                "success": True,
                "experiment": {
                    "id": str(experiment.id),
                    "name": experiment.name,
                    "description": experiment.description,
                    "feature_flag": experiment.feature_flag,
                    "status": experiment.status,
                    "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
                    "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
                    "variants": experiment.variants,
                    "success_metrics": experiment.success_metrics
                },
                "results": {
                    "total_participants": total_participants,
                    "variant_results": variant_results,
                    "statistical_significance": significance_results,
                    "daily_trends": daily_trends
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting experiment results: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_statistical_significance(self, variant_results: Dict[str, Any], 
                                          success_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistical significance between variants (simplified)"""
        significance_results = {}
        
        # This is a simplified implementation
        # In production, you'd want to use proper statistical tests like chi-square or t-test
        
        variants = list(variant_results.keys())
        if len(variants) < 2:
            return {"error": "Need at least 2 variants for significance testing"}
        
        control_variant = variants[0]  # Assume first variant is control
        
        for metric in success_metrics:
            metric_name = metric["name"]
            
            control_data = variant_results[control_variant]["conversions"].get(metric_name, {})
            control_rate = control_data.get("conversion_rate", 0)
            control_count = variant_results[control_variant]["participants"]
            
            metric_results = {
                "metric_name": metric_name,
                "control_variant": control_variant,
                "control_conversion_rate": control_rate,
                "variant_comparisons": []
            }
            
            for variant in variants[1:]:  # Compare other variants to control
                variant_data = variant_results[variant]["conversions"].get(metric_name, {})
                variant_rate = variant_data.get("conversion_rate", 0)
                variant_count = variant_results[variant]["participants"]
                
                # Simple significance check (in production, use proper statistical tests)
                rate_difference = variant_rate - control_rate
                relative_improvement = (rate_difference / control_rate * 100) if control_rate > 0 else 0
                
                # Simplified significance (would need proper calculation in production)
                min_sample_size = 100  # Minimum sample size for significance
                is_significant = (
                    control_count >= min_sample_size and 
                    variant_count >= min_sample_size and 
                    abs(rate_difference) > 2.0  # At least 2% difference
                )
                
                metric_results["variant_comparisons"].append({
                    "variant": variant,
                    "conversion_rate": variant_rate,
                    "rate_difference": rate_difference,
                    "relative_improvement": relative_improvement,
                    "is_statistically_significant": is_significant,
                    "sample_size": variant_count
                })
            
            significance_results[metric_name] = metric_results
        
        return significance_results
    
    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active experiments"""
        try:
            experiments = self.db.query(ABTestExperiment).filter(
                ABTestExperiment.status == "active"
            ).all()
            
            result = []
            for experiment in experiments:
                # Get participant count
                participant_count = self.db.query(ABTestParticipation).filter(
                    ABTestParticipation.experiment_id == experiment.id
                ).count()
                
                result.append({
                    "id": str(experiment.id),
                    "name": experiment.name,
                    "description": experiment.description,
                    "feature_flag": experiment.feature_flag,
                    "status": experiment.status,
                    "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
                    "participant_count": participant_count,
                    "variants": list(experiment.variants.keys()),
                    "traffic_allocation": experiment.traffic_allocation
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting active experiments: {e}")
            return []
    
    async def get_user_experiments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get experiments a user is participating in"""
        try:
            participations = self.db.query(ABTestParticipation).join(
                ABTestExperiment
            ).filter(
                ABTestParticipation.user_id == user_id
            ).all()
            
            result = []
            for participation in participations:
                experiment = participation.experiment
                
                result.append({
                    "experiment_id": str(experiment.id),
                    "experiment_name": experiment.name,
                    "feature_flag": experiment.feature_flag,
                    "variant": participation.variant,
                    "assigned_at": participation.assigned_at.isoformat(),
                    "first_exposure_at": participation.first_exposure_at.isoformat() if participation.first_exposure_at else None,
                    "conversion_events": participation.conversion_events or [],
                    "experiment_status": experiment.status
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user experiments: {e}")
            return []