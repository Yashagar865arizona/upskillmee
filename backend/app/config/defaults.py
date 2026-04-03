"""
Default configuration values for the application.
These can be overridden by environment variables.
"""

# User profile schema
USER_PROFILE_SCHEMA = {
    # Demographics and Background
    'demographics': {
        'age': None,
        'location': None,
        'education_level': ['high_school', 'undergraduate', 'postgraduate', 'professional'],
        'languages': [],
        'learning_style': ['visual', 'auditory', 'kinesthetic', 'reading_writing']
    },
    
    # Interests and Preferences
    'interests': {
        'hobbies': [],
        'preferred_subjects': [],
        'work_style': ['independent', 'team_based', 'hybrid'],
        'work_preferences': ['creative', 'analytical', 'strategic', 'technical'],
        'career_interests': [],
        'long_term_goals': []
    },
    
    # Skills and Competencies
    'skills': {
        'technical_skills': [],
        'soft_skills': [
            'communication',
            'leadership',
            'teamwork',
            'problem_solving',
            'time_management',
            'adaptability'
        ],
        'certifications': [],
        'achievements': []
    },
    
    # Personality and Aptitude
    'personality': {
        'traits': {
            'introversion_extroversion': None,  # Scale 1-10
            'detail_big_picture': None,  # Scale 1-10
            'risk_taking': None  # Scale 1-10
        },
        'cognitive_strengths': [
            'logical_reasoning',
            'creativity',
            'critical_thinking',
            'analytical_thinking',
            'emotional_intelligence'
        ],
        'learning_preferences': {
            'preferred_resources': ['documentation', 'video', 'interactive', 'mentorship'],
            'learning_pace': ['self_paced', 'structured', 'intensive'],
            'project_preference': ['practical', 'theoretical', 'research', 'creative']
        }
    }
}

# Project tracking schema
PROJECT_TRACKING_SCHEMA = {
    # Project Details
    'project_metrics': {
        'completion_rate': None,  # Percentage
        'quality_score': None,  # Scale 1-10
        'innovation_score': None,  # Scale 1-10
        'technical_accuracy': None,  # Scale 1-10
        'time_management': None  # Scale 1-10
    },
    
    # Activity Monitoring
    'activity_metrics': {
        'engagement_level': None,  # Scale 1-10
        'consistency': None,  # Scale 1-10
        'resource_utilization': None,  # Scale 1-10
        'problem_solving_approach': [
            'methodical',
            'experimental',
            'collaborative',
            'innovative'
        ]
    },
    
    # Learning Progress
    'learning_metrics': {
        'concept_understanding': None,  # Scale 1-10
        'skill_improvement': None,  # Scale 1-10
        'feedback_responsiveness': None,  # Scale 1-10
        'challenge_handling': None  # Scale 1-10
    },
    
    # Collaboration (for team projects)
    'collaboration_metrics': {
        'team_contribution': None,  # Scale 1-10
        'communication_effectiveness': None,  # Scale 1-10
        'leadership_score': None,  # Scale 1-10
        'peer_feedback': []
    }
}

# Learning levels with detailed criteria
LEARNING_LEVELS = {
    'beginner': {
        'description': 'New to the field, learning fundamentals',
        'expected_skills': ['basic_concepts', 'tool_familiarity'],
        'project_complexity': 'low',
        'guidance_level': 'high'
    },
    'intermediate': {
        'description': 'Understanding core concepts, gaining practical experience',
        'expected_skills': ['problem_solving', 'independent_work'],
        'project_complexity': 'medium',
        'guidance_level': 'moderate'
    },
    'advanced': {
        'description': 'Proficient in the field, tackling complex problems',
        'expected_skills': ['advanced_concepts', 'project_leadership'],
        'project_complexity': 'high',
        'guidance_level': 'low'
    },
    'expert': {
        'description': 'Deep expertise, innovating and mentoring others',
        'expected_skills': ['innovation', 'mentorship'],
        'project_complexity': 'very_high',
        'guidance_level': 'minimal'
    }
}

# Engagement thresholds for metrics
ENGAGEMENT_THRESHOLDS = {
    'messages_per_day': 10,  # target messages per day
    'response_time': 300,    # target response time in seconds
    'session_duration': 30,  # target session duration in minutes
    'active_streak': 7,      # target consecutive active days
}

# Learning pace baseline (skill points per day)
LEARNING_PACE_BASELINE = 0.1  # baseline improvement rate

# Skill levels
SKILL_LEVELS = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4
}

# Chat settings
CHAT_SETTINGS = {
    'max_message_length': 4096,
    'batch_size': 5,  # Maximum number of messages to process in a single batch
    'min_batch_interval': 100,  # Minimum time (ms) between messages to consider them part of different batches
    'max_batch_wait': 1000,  # Maximum time (ms) to wait for batch completion
}

# Learning plan settings
LEARNING_PLAN_SETTINGS = {
    'min_steps': 3,
    'max_steps': 10,
    'required_sections': [
        'overview',
        'prerequisites',
        'learning_outcomes',
        'timeline',
        'resources',
        'assessment_criteria',
        'practical_applications'
    ],
    'assessment_methods': [
        'project_completion',
        'skill_demonstration',
        'peer_review',
        'self_assessment',
        'mentor_evaluation'
    ]
}

# Project settings
PROJECT_SETTINGS = {
    'min_steps': 2,
    'max_steps': 8,
    'difficulty_levels': ['beginner', 'intermediate', 'advanced'],
    'required_sections': [
        'description',
        'prerequisites',
        'steps',
        'learning_outcomes',
        'resources',
        'evaluation_criteria',
        'real_world_applications'
    ],
    'evaluation_metrics': [
        'technical_accuracy',
        'creativity',
        'problem_solving',
        'documentation',
        'code_quality',
        'project_impact'
    ]
}
