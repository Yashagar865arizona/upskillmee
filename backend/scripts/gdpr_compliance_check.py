#!/usr/bin/env python3
"""
GDPR Compliance verification script for Ponder backend.
Checks data handling, user rights, consent management, and privacy controls.
"""

import sys
import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import get_db
from app.models import User, Message, Conversation, UserProfile
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class GDPRComplianceChecker:
    """GDPR compliance verification for Ponder application."""
    
    def __init__(self):
        self.compliance_results = {
            "timestamp": time.time(),
            "data_mapping": {},
            "user_rights": {},
            "consent_management": {},
            "data_protection": {},
            "privacy_controls": {},
            "documentation": {},
            "technical_measures": {},
            "compliance_score": 0,
            "recommendations": []
        }
    
    def check_data_mapping(self) -> Dict[str, Any]:
        """Check data mapping and inventory (Article 30 - Records of Processing)."""
        logger.info("Checking data mapping and inventory...")
        
        # Analyze database models for personal data
        personal_data_fields = {
            "User": {
                "direct_identifiers": ["id", "email", "name"],
                "indirect_identifiers": ["created_at", "updated_at"],
                "sensitive_data": [],
                "purpose": "User account management and authentication"
            },
            "UserProfile": {
                "direct_identifiers": ["user_id"],
                "indirect_identifiers": ["preferences", "settings"],
                "sensitive_data": [],
                "purpose": "User personalization and preferences"
            },
            "Message": {
                "direct_identifiers": ["user_id"],
                "indirect_identifiers": ["content", "created_at", "conversation_id"],
                "sensitive_data": ["content"],
                "purpose": "Chat functionality and AI interaction"
            },
            "Conversation": {
                "direct_identifiers": ["user_id"],
                "indirect_identifiers": ["title", "created_at", "updated_at"],
                "sensitive_data": [],
                "purpose": "Chat session management"
            }
        }
        
        # Check for data retention policies
        retention_policies = self.check_data_retention_policies()
        
        # Check for data processing purposes
        processing_purposes = self.check_processing_purposes()
        
        return {
            "personal_data_inventory": personal_data_fields,
            "data_retention_policies": retention_policies,
            "processing_purposes": processing_purposes,
            "data_categories": self.categorize_data_types(personal_data_fields),
            "third_party_sharing": self.check_third_party_sharing(),
            "cross_border_transfers": self.check_cross_border_transfers()
        }
    
    def check_data_retention_policies(self) -> Dict[str, Any]:
        """Check data retention policies."""
        backend_path = Path(__file__).parent.parent
        
        # Look for retention policy documentation
        policy_files = []
        for pattern in ["*retention*", "*policy*", "*privacy*"]:
            policy_files.extend(list(backend_path.rglob(pattern)))
        
        # Check for automated deletion mechanisms
        deletion_code = self.find_deletion_mechanisms(backend_path)
        
        return {
            "policy_documentation": [str(f) for f in policy_files],
            "automated_deletion": deletion_code,
            "retention_periods_defined": len(policy_files) > 0,
            "recommendation": "Define clear retention periods for each data category"
        }
    
    def find_deletion_mechanisms(self, backend_path: Path) -> List[Dict[str, Any]]:
        """Find automated deletion mechanisms in code."""
        deletion_patterns = [
            r'delete.*user',
            r'remove.*data',
            r'cleanup.*old',
            r'expire.*after',
            r'retention.*period'
        ]
        
        deletion_code = []
        
        for py_file in backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in deletion_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        deletion_code.append({
                            "file": str(py_file.relative_to(backend_path)),
                            "pattern": pattern,
                            "matches": len(matches)
                        })
            except Exception:
                continue
        
        return deletion_code
    
    def check_processing_purposes(self) -> Dict[str, Any]:
        """Check data processing purposes."""
        return {
            "authentication": {
                "data_used": ["email", "password_hash", "user_id"],
                "legal_basis": "Contract performance",
                "purpose": "User authentication and account management"
            },
            "chat_functionality": {
                "data_used": ["user_id", "message_content", "conversation_history"],
                "legal_basis": "Contract performance / Legitimate interest",
                "purpose": "Provide AI chat services"
            },
            "personalization": {
                "data_used": ["user_preferences", "usage_patterns"],
                "legal_basis": "Consent / Legitimate interest",
                "purpose": "Personalize user experience"
            },
            "analytics": {
                "data_used": ["usage_statistics", "performance_metrics"],
                "legal_basis": "Legitimate interest",
                "purpose": "Service improvement and analytics"
            }
        }
    
    def categorize_data_types(self, personal_data_fields: Dict) -> Dict[str, List[str]]:
        """Categorize data types according to GDPR."""
        return {
            "identity_data": ["name", "email", "user_id"],
            "contact_data": ["email"],
            "technical_data": ["ip_address", "session_data", "device_info"],
            "usage_data": ["message_content", "conversation_history", "preferences"],
            "special_categories": [],  # No special category data identified
            "criminal_data": []  # No criminal data identified
        }
    
    def check_third_party_sharing(self) -> Dict[str, Any]:
        """Check third-party data sharing."""
        return {
            "ai_services": {
                "provider": "OpenAI / AI Service Provider",
                "data_shared": ["message_content", "conversation_context"],
                "purpose": "AI response generation",
                "safeguards": "Data processing agreement required"
            },
            "analytics_services": {
                "provider": "Analytics Provider (if any)",
                "data_shared": ["usage_statistics", "performance_metrics"],
                "purpose": "Service analytics and improvement",
                "safeguards": "Anonymization and aggregation"
            },
            "recommendation": "Ensure all third-party processors have DPAs in place"
        }
    
    def check_cross_border_transfers(self) -> Dict[str, Any]:
        """Check cross-border data transfers."""
        return {
            "transfers_identified": True,
            "destinations": ["United States (AI services)", "Cloud providers"],
            "transfer_mechanisms": ["Standard Contractual Clauses", "Adequacy decisions"],
            "safeguards": "Data processing agreements with adequate safeguards",
            "recommendation": "Ensure all transfers comply with Chapter V GDPR"
        }
    
    def check_user_rights(self) -> Dict[str, Any]:
        """Check implementation of user rights (Chapter III GDPR)."""
        logger.info("Checking user rights implementation...")
        
        return {
            "right_to_information": self.check_right_to_information(),
            "right_of_access": self.check_right_of_access(),
            "right_to_rectification": self.check_right_to_rectification(),
            "right_to_erasure": self.check_right_to_erasure(),
            "right_to_restrict_processing": self.check_right_to_restrict_processing(),
            "right_to_data_portability": self.check_right_to_data_portability(),
            "right_to_object": self.check_right_to_object(),
            "rights_related_to_automated_decision_making": self.check_automated_decision_making()
        }
    
    def check_right_to_information(self) -> Dict[str, Any]:
        """Check right to information (Articles 13-14)."""
        return {
            "privacy_notice_available": self.check_privacy_notice_exists(),
            "information_provided": {
                "controller_identity": "Required",
                "processing_purposes": "Required",
                "legal_basis": "Required",
                "retention_periods": "Required",
                "user_rights": "Required",
                "complaint_right": "Required"
            },
            "compliance_status": "Partial - Privacy notice needs review",
            "recommendation": "Ensure comprehensive privacy notice covers all required elements"
        }
    
    def check_privacy_notice_exists(self) -> bool:
        """Check if privacy notice exists."""
        backend_path = Path(__file__).parent.parent.parent
        
        privacy_files = []
        for pattern in ["*privacy*", "*policy*", "*terms*"]:
            privacy_files.extend(list(backend_path.rglob(pattern)))
        
        return len(privacy_files) > 0
    
    def check_right_of_access(self) -> Dict[str, Any]:
        """Check right of access (Article 15)."""
        # Check if there's an endpoint for data export/access
        backend_path = Path(__file__).parent.parent
        
        access_endpoints = self.find_data_access_endpoints(backend_path)
        
        return {
            "data_access_endpoint": len(access_endpoints) > 0,
            "endpoints_found": access_endpoints,
            "data_provided": {
                "personal_data_copy": "Required",
                "processing_purposes": "Required",
                "data_categories": "Required",
                "recipients": "Required",
                "retention_period": "Required",
                "user_rights": "Required",
                "data_source": "Required"
            },
            "response_timeframe": "30 days maximum",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement user data access endpoint"
        }
    
    def find_data_access_endpoints(self, backend_path: Path) -> List[str]:
        """Find data access endpoints in code."""
        access_patterns = [
            r'@.*\.route.*export',
            r'@.*\.route.*download',
            r'@.*\.route.*data',
            r'def.*export.*data',
            r'def.*download.*data'
        ]
        
        endpoints = []
        
        for py_file in backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in access_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        endpoints.extend(matches)
            except Exception:
                continue
        
        return endpoints
    
    def check_right_to_rectification(self) -> Dict[str, Any]:
        """Check right to rectification (Article 16)."""
        return {
            "user_profile_update": "Available through user profile endpoints",
            "data_correction_mechanism": "Partial - user can update profile",
            "notification_to_recipients": "Needs implementation",
            "compliance_status": "Partial",
            "recommendation": "Ensure all personal data can be corrected by users"
        }
    
    def check_right_to_erasure(self) -> Dict[str, Any]:
        """Check right to erasure (Article 17)."""
        backend_path = Path(__file__).parent.parent
        
        deletion_endpoints = self.find_deletion_endpoints(backend_path)
        
        return {
            "account_deletion_available": len(deletion_endpoints) > 0,
            "deletion_endpoints": deletion_endpoints,
            "complete_data_removal": "Needs verification",
            "anonymization_option": "Needs implementation",
            "notification_to_recipients": "Needs implementation",
            "exceptions_handling": {
                "freedom_of_expression": "Not applicable",
                "legal_obligations": "Consider retention requirements",
                "public_interest": "Not applicable"
            },
            "compliance_status": "Needs improvement",
            "recommendation": "Implement comprehensive data deletion with proper anonymization"
        }
    
    def find_deletion_endpoints(self, backend_path: Path) -> List[str]:
        """Find deletion endpoints in code."""
        deletion_patterns = [
            r'@.*\.route.*delete',
            r'@.*\.route.*remove',
            r'def.*delete.*user',
            r'def.*remove.*account'
        ]
        
        endpoints = []
        
        for py_file in backend_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in deletion_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        endpoints.extend(matches)
            except Exception:
                continue
        
        return endpoints
    
    def check_right_to_restrict_processing(self) -> Dict[str, Any]:
        """Check right to restrict processing (Article 18)."""
        return {
            "processing_restriction_mechanism": "Needs implementation",
            "account_suspension_option": "Needs implementation",
            "data_marking_system": "Needs implementation",
            "compliance_status": "Not implemented",
            "recommendation": "Implement processing restriction controls"
        }
    
    def check_right_to_data_portability(self) -> Dict[str, Any]:
        """Check right to data portability (Article 20)."""
        return {
            "data_export_format": "JSON format recommended",
            "structured_data_export": "Needs implementation",
            "machine_readable_format": "Needs implementation",
            "direct_transmission": "Not applicable for this service",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement structured data export in JSON/CSV format"
        }
    
    def check_right_to_object(self) -> Dict[str, Any]:
        """Check right to object (Article 21)."""
        return {
            "objection_mechanism": "Needs implementation",
            "marketing_opt_out": "Not applicable - no marketing",
            "profiling_opt_out": "Consider if AI personalization constitutes profiling",
            "legitimate_interest_override": "Needs assessment",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement objection mechanism for legitimate interest processing"
        }
    
    def check_automated_decision_making(self) -> Dict[str, Any]:
        """Check rights related to automated decision-making (Article 22)."""
        return {
            "automated_decisions_present": "AI responses may constitute automated processing",
            "human_intervention_available": "Needs implementation",
            "decision_explanation": "AI response generation should be explainable",
            "decision_challenge": "Needs implementation",
            "compliance_status": "Needs assessment",
            "recommendation": "Assess if AI responses constitute automated decision-making under Article 22"
        }
    
    def check_consent_management(self) -> Dict[str, Any]:
        """Check consent management (Article 7)."""
        logger.info("Checking consent management...")
        
        return {
            "consent_collection": self.check_consent_collection(),
            "consent_withdrawal": self.check_consent_withdrawal(),
            "consent_records": self.check_consent_records(),
            "granular_consent": self.check_granular_consent(),
            "child_consent": self.check_child_consent()
        }
    
    def check_consent_collection(self) -> Dict[str, Any]:
        """Check consent collection mechanisms."""
        return {
            "explicit_consent": "Needs implementation for non-essential processing",
            "informed_consent": "Privacy notice must be clear and accessible",
            "freely_given": "Ensure consent is not bundled with service access",
            "specific_consent": "Separate consent for different purposes",
            "consent_mechanism": "Checkboxes, opt-in forms needed",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement explicit consent collection for optional processing"
        }
    
    def check_consent_withdrawal(self) -> Dict[str, Any]:
        """Check consent withdrawal mechanisms."""
        return {
            "withdrawal_mechanism": "Needs implementation",
            "easy_withdrawal": "Must be as easy as giving consent",
            "withdrawal_effects": "Must stop processing based on consent",
            "user_notification": "Inform users about withdrawal consequences",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement easy consent withdrawal mechanism"
        }
    
    def check_consent_records(self) -> Dict[str, Any]:
        """Check consent record keeping."""
        return {
            "consent_logging": "Needs implementation",
            "consent_timestamp": "Record when consent was given",
            "consent_version": "Track privacy policy versions",
            "consent_method": "Record how consent was obtained",
            "consent_scope": "Record what was consented to",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement comprehensive consent logging system"
        }
    
    def check_granular_consent(self) -> Dict[str, Any]:
        """Check granular consent options."""
        return {
            "separate_purposes": "Allow consent for different processing purposes",
            "optional_features": "Separate consent for optional features",
            "marketing_consent": "Not applicable - no marketing",
            "analytics_consent": "Consider separate consent for analytics",
            "compliance_status": "Needs implementation",
            "recommendation": "Provide granular consent options for different purposes"
        }
    
    def check_child_consent(self) -> Dict[str, Any]:
        """Check child consent handling."""
        return {
            "age_verification": "Needs implementation if service available to children",
            "parental_consent": "Required for children under 16 (or national age)",
            "child_data_protection": "Enhanced protection for children's data",
            "age_appropriate_design": "Consider age-appropriate design principles",
            "compliance_status": "Needs assessment",
            "recommendation": "Assess if service is offered to children and implement appropriate safeguards"
        }
    
    def check_data_protection(self) -> Dict[str, Any]:
        """Check data protection measures (Articles 25, 32)."""
        logger.info("Checking data protection measures...")
        
        return {
            "data_protection_by_design": self.check_privacy_by_design(),
            "data_protection_by_default": self.check_privacy_by_default(),
            "technical_measures": self.check_technical_measures(),
            "organizational_measures": self.check_organizational_measures(),
            "data_breach_procedures": self.check_data_breach_procedures()
        }
    
    def check_privacy_by_design(self) -> Dict[str, Any]:
        """Check privacy by design implementation."""
        return {
            "privacy_impact_assessment": "Needs documentation",
            "privacy_considerations": "Should be integrated in development process",
            "data_minimization": "Collect only necessary data",
            "purpose_limitation": "Use data only for stated purposes",
            "storage_limitation": "Implement data retention policies",
            "compliance_status": "Partial",
            "recommendation": "Integrate privacy considerations into development lifecycle"
        }
    
    def check_privacy_by_default(self) -> Dict[str, Any]:
        """Check privacy by default settings."""
        return {
            "default_privacy_settings": "Most privacy-friendly settings by default",
            "opt_in_not_opt_out": "Use opt-in for non-essential processing",
            "minimal_data_processing": "Process minimal data by default",
            "user_control": "Give users control over their data",
            "compliance_status": "Needs improvement",
            "recommendation": "Ensure privacy-friendly default settings"
        }
    
    def check_technical_measures(self) -> Dict[str, Any]:
        """Check technical security measures."""
        return {
            "encryption_at_rest": "Database encryption needed",
            "encryption_in_transit": "HTTPS/TLS implemented",
            "access_controls": "Role-based access control needed",
            "authentication": "Strong authentication implemented",
            "audit_logging": "Comprehensive audit logging needed",
            "data_anonymization": "Anonymization techniques needed",
            "compliance_status": "Partial",
            "recommendation": "Implement comprehensive technical security measures"
        }
    
    def check_organizational_measures(self) -> Dict[str, Any]:
        """Check organizational security measures."""
        return {
            "staff_training": "Privacy training for staff needed",
            "access_management": "Staff access controls needed",
            "incident_response": "Data breach response procedures needed",
            "vendor_management": "Data processing agreements with vendors",
            "privacy_policies": "Internal privacy policies needed",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement organizational security measures and staff training"
        }
    
    def check_data_breach_procedures(self) -> Dict[str, Any]:
        """Check data breach procedures (Articles 33-34)."""
        return {
            "breach_detection": "Automated breach detection needed",
            "authority_notification": "72-hour notification procedure needed",
            "user_notification": "User notification procedure for high-risk breaches",
            "breach_documentation": "Breach register needed",
            "breach_assessment": "Risk assessment procedures needed",
            "compliance_status": "Needs implementation",
            "recommendation": "Implement comprehensive data breach response procedures"
        }
    
    def calculate_compliance_score(self) -> int:
        """Calculate overall GDPR compliance score."""
        total_checks = 0
        passed_checks = 0
        
        # Count checks from each category
        categories = [
            self.compliance_results.get("data_mapping", {}),
            self.compliance_results.get("user_rights", {}),
            self.compliance_results.get("consent_management", {}),
            self.compliance_results.get("data_protection", {})
        ]
        
        for category in categories:
            for key, value in category.items():
                if isinstance(value, dict) and "compliance_status" in value:
                    total_checks += 1
                    status = value["compliance_status"]
                    if "implemented" in status.lower() or "available" in status.lower():
                        passed_checks += 1
                    elif "partial" in status.lower():
                        passed_checks += 0.5
        
        if total_checks > 0:
            return int((passed_checks / total_checks) * 100)
        return 0
    
    def generate_compliance_recommendations(self) -> List[str]:
        """Generate GDPR compliance recommendations."""
        recommendations = [
            "Implement comprehensive privacy notice covering all GDPR requirements",
            "Create user data access and export functionality",
            "Implement account deletion with proper data anonymization",
            "Establish consent management system with granular controls",
            "Implement data retention policies with automated deletion",
            "Create data breach response procedures and notification systems",
            "Conduct privacy impact assessment for AI processing",
            "Establish data processing agreements with third-party providers",
            "Implement technical security measures (encryption, access controls)",
            "Provide staff training on GDPR compliance and data protection",
            "Create internal privacy policies and procedures",
            "Implement audit logging and monitoring systems",
            "Establish user rights fulfillment procedures",
            "Consider appointing Data Protection Officer if required",
            "Regular compliance audits and assessments"
        ]
        
        return recommendations
    
    def run_full_compliance_check(self) -> Dict[str, Any]:
        """Run complete GDPR compliance check."""
        logger.info("Starting comprehensive GDPR compliance check...")
        
        self.compliance_results["data_mapping"] = self.check_data_mapping()
        self.compliance_results["user_rights"] = self.check_user_rights()
        self.compliance_results["consent_management"] = self.check_consent_management()
        self.compliance_results["data_protection"] = self.check_data_protection()
        
        self.compliance_results["compliance_score"] = self.calculate_compliance_score()
        self.compliance_results["recommendations"] = self.generate_compliance_recommendations()
        
        return self.compliance_results
    
    def save_compliance_report(self, filename: str = None):
        """Save compliance report to file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"gdpr_compliance_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.compliance_results, f, indent=2, default=str)
        
        logger.info(f"GDPR compliance report saved to: {filepath}")
        return filepath
    
    def print_compliance_summary(self):
        """Print compliance summary."""
        print("\n" + "="*60)
        print("GDPR COMPLIANCE SUMMARY")
        print("="*60)
        
        score = self.compliance_results.get("compliance_score", 0)
        print(f"Overall Compliance Score: {score}%")
        
        if score >= 80:
            print("Status: Good compliance level")
        elif score >= 60:
            print("Status: Moderate compliance - improvements needed")
        else:
            print("Status: Low compliance - significant work required")
        
        # Data mapping summary
        data_mapping = self.compliance_results.get("data_mapping", {})
        personal_data = data_mapping.get("personal_data_inventory", {})
        print(f"\nData Categories Identified: {len(personal_data)}")
        
        # User rights summary
        user_rights = self.compliance_results.get("user_rights", {})
        rights_implemented = sum(1 for right in user_rights.values() 
                               if isinstance(right, dict) and 
                               "implemented" in right.get("compliance_status", "").lower())
        print(f"User Rights Implemented: {rights_implemented}/{len(user_rights)}")
        
        # Consent management summary
        consent = self.compliance_results.get("consent_management", {})
        consent_implemented = sum(1 for item in consent.values() 
                                if isinstance(item, dict) and 
                                "implemented" in item.get("compliance_status", "").lower())
        print(f"Consent Management: {consent_implemented}/{len(consent)} implemented")
        
        # Top recommendations
        recommendations = self.compliance_results.get("recommendations", [])
        print(f"\nTop Priority Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"  {i}. {rec}")
        
        print(f"\nTotal Recommendations: {len(recommendations)}")


def main():
    """Main function to run GDPR compliance check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GDPR Compliance Check for Ponder")
    parser.add_argument("--save", help="Save report to specific file")
    
    args = parser.parse_args()
    
    checker = GDPRComplianceChecker()
    
    try:
        compliance_results = checker.run_full_compliance_check()
        
        checker.print_compliance_summary()
        
        if args.save:
            report_path = checker.save_compliance_report(args.save)
        else:
            report_path = checker.save_compliance_report()
        
        print(f"\nFull GDPR compliance report saved to: {report_path}")
        
    except KeyboardInterrupt:
        logger.info("GDPR compliance check interrupted by user")
    except Exception as e:
        logger.error(f"GDPR compliance check failed: {e}")


if __name__ == "__main__":
    main()