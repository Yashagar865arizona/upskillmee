"""
AI Integration Service - Enhanced AI interactions with retry logic and monitoring
Handles OpenAI GPT-4, DeepSeek, and other AI model integrations with:
- Exponential backoff retry logic with jitter
- Comprehensive fallback mechanisms
- Advanced cost tracking and usage monitoring
- Optimized prompt engineering with context awareness
- Circuit breaker pattern for reliability
- Detailed error classification and handling
"""

from typing import Dict, List, Any, Optional, Tuple, cast, Union
import logging
import time
import json
import re
import asyncio
import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import openai
from app.agents.agent_manager import AgentMode
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Enumeration of AI providers"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

class RequestType(Enum):
    """Types of AI requests for cost tracking"""
    CHAT = "chat"
    LEARNING_PLAN = "learning_plan"
    GREETING = "greeting"
    FALLBACK = "fallback"

@dataclass
class UsageMetrics:
    """Track usage metrics for AI API calls"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    requests_by_type: Dict[str, int] = field(default_factory=dict)
    requests_by_provider: Dict[str, int] = field(default_factory=dict)
    last_reset: datetime = field(default_factory=datetime.now)

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass
class APICallResult:
    """Result of an AI API call"""
    success: bool
    content: Optional[str]
    tokens_used: int
    cost: float
    response_time: float
    provider: AIProvider
    request_type: RequestType
    error: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: int = 0

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for AI providers"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: int = 300  # 5 minutes

@dataclass
class DetailedCostMetrics:
    """Detailed cost tracking metrics"""
    total_cost: float = 0.0
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_provider: Dict[str, float] = field(default_factory=dict)
    cost_by_request_type: Dict[str, float] = field(default_factory=dict)
    daily_cost: float = 0.0
    monthly_cost: float = 0.0
    cost_alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_cost_reset: datetime = field(default_factory=datetime.now)

class AIErrorType(Enum):
    """Classification of AI API errors"""
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_OVERLOADED = "model_overloaded"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"

# API base URLs
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"

class AIIntegrationService:
    """Enhanced service for integrating with AI models with retry logic and monitoring"""

    # Cost tracking (approximate costs per 1K tokens)
    COST_PER_1K_TOKENS = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "deepseek-chat": {"input": 0.0014, "output": 0.0028},
    }

    def __init__(self):
        """Initialize AI integration service with enhanced monitoring"""
        self.openai_client = None
        self.deepseek_client = None
        self.usage_metrics = UsageMetrics()
        self.retry_config = RetryConfig()
        
        # Enhanced monitoring and reliability features
        self.detailed_cost_metrics = DetailedCostMetrics()
        self.circuit_breakers = {
            AIProvider.OPENAI: CircuitBreakerState(),
            AIProvider.DEEPSEEK: CircuitBreakerState()
        }
        self.error_counts = {error_type: 0 for error_type in AIErrorType}
        self.prompt_cache = {}  # Cache for optimized prompts
        
        # Cost thresholds for alerts
        self.daily_cost_threshold = 50.0  # $50 per day
        self.monthly_cost_threshold = 1000.0  # $1000 per month

        # Initialize API clients with better error handling
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize AI API clients with proper error handling"""
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url="https://api.openai.com/v1",
                    timeout=settings.OPENAI_TIMEOUT
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.openai_client = None
        else:
            logger.warning("OpenAI API key not provided")

        # Initialize DeepSeek client
        if settings.DEEPSEEK_API_KEY:
            try:
                self.deepseek_client = OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=DEEPSEEK_API_BASE,
                    timeout=settings.DEEPSEEK_TIMEOUT
                )
                logger.info("DeepSeek client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
                self.deepseek_client = None
        else:
            logger.warning("DeepSeek API key not provided")

    async def _make_api_call_with_retry(
        self,
        client: OpenAI,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        provider: AIProvider,
        request_type: RequestType,
        timeout: Optional[float] = None
    ) -> APICallResult:
        """Make API call with enhanced retry logic, circuit breaker, and error handling"""
        start_time = time.time()
        last_exception = None
        error_type = AIErrorType.UNKNOWN

        # Check circuit breaker before attempting call
        if self._is_circuit_breaker_open(provider):
            logger.warning(f"Circuit breaker is open for {provider.value}, skipping API call")
            return APICallResult(
                success=False,
                content=None,
                tokens_used=0,
                cost=0.0,
                response_time=0.0,
                provider=provider,
                request_type=request_type,
                error="Circuit breaker is open",
                error_type="circuit_breaker_open",
                retry_count=0
            )

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Calculate delay for this attempt
                if attempt > 0:
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.exponential_base ** (attempt - 1)),
                        self.retry_config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if self.retry_config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.info(f"Retrying API call (attempt {attempt + 1}/{self.retry_config.max_retries + 1}) after {delay:.2f}s delay")
                    await asyncio.sleep(delay)

                # Make the API call
                response = client.chat.completions.create(
                    model=model,
                    messages=cast(List[ChatCompletionMessageParam], messages),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout or settings.OPENAI_TIMEOUT
                )

                # Extract response data
                content = response.choices[0].message.content or ""
                tokens_used = response.usage.total_tokens if response.usage else 0
                response_time = time.time() - start_time

                # Calculate cost
                cost = self._calculate_cost(model, tokens_used)

                # Update metrics and circuit breaker
                self._update_metrics(
                    success=True,
                    tokens_used=tokens_used,
                    cost=cost,
                    response_time=response_time,
                    provider=provider,
                    request_type=request_type
                )
                
                # Update detailed cost metrics
                self._update_detailed_cost_metrics(model, cost, provider, request_type)
                
                # Update circuit breaker on success
                self._update_circuit_breaker(provider, success=True)

                logger.info(f"API call successful on attempt {attempt + 1}, tokens: {tokens_used}, cost: ${cost:.4f}, time: {response_time:.2f}s")

                return APICallResult(
                    success=True,
                    content=content,
                    tokens_used=tokens_used,
                    cost=cost,
                    response_time=response_time,
                    provider=provider,
                    request_type=request_type,
                    retry_count=attempt
                )

            except openai.RateLimitError as e:
                last_exception = e
                error_type = self._classify_error(e)
                self.error_counts[error_type] += 1
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {str(e)}")
                
                # For rate limits, use longer delays
                if attempt < self.retry_config.max_retries:
                    rate_limit_delay = min(60.0, self.retry_config.base_delay * (2 ** attempt))
                    logger.info(f"Rate limit detected, waiting {rate_limit_delay:.2f}s before retry")
                    await asyncio.sleep(rate_limit_delay)
                continue

            except openai.APITimeoutError as e:
                last_exception = e
                error_type = self._classify_error(e)
                self.error_counts[error_type] += 1
                logger.warning(f"API timeout on attempt {attempt + 1}: {str(e)}")
                if attempt == self.retry_config.max_retries:
                    break
                continue

            except openai.APIConnectionError as e:
                last_exception = e
                error_type = self._classify_error(e)
                self.error_counts[error_type] += 1
                logger.warning(f"API connection error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.retry_config.max_retries:
                    break
                continue

            except openai.AuthenticationError as e:
                last_exception = e
                error_type = self._classify_error(e)
                self.error_counts[error_type] += 1
                logger.error(f"Authentication error on attempt {attempt + 1}: {str(e)}")
                # Don't retry authentication errors
                break

            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)
                self.error_counts[error_type] += 1
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                # Don't retry on unexpected errors
                break

        # All retries failed
        response_time = time.time() - start_time
        
        # Update metrics and circuit breaker on failure
        self._update_metrics(
            success=False,
            tokens_used=0,
            cost=0.0,
            response_time=response_time,
            provider=provider,
            request_type=request_type
        )
        
        # Update circuit breaker on failure
        self._update_circuit_breaker(provider, success=False)

        error_msg = f"API call failed after {self.retry_config.max_retries + 1} attempts: {str(last_exception)}"
        logger.error(error_msg)

        return APICallResult(
            success=False,
            content=None,
            tokens_used=0,
            cost=0.0,
            response_time=response_time,
            provider=provider,
            request_type=request_type,
            error=error_msg,
            error_type=error_type.value,
            retry_count=self.retry_config.max_retries + 1
        )

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """Calculate approximate cost for API call"""
        if model not in self.COST_PER_1K_TOKENS:
            return 0.0
        
        # Approximate cost calculation (assuming 70% input, 30% output tokens)
        input_tokens = int(tokens_used * 0.7)
        output_tokens = int(tokens_used * 0.3)
        
        cost_info = self.COST_PER_1K_TOKENS[model]
        input_cost = (input_tokens / 1000) * cost_info["input"]
        output_cost = (output_tokens / 1000) * cost_info["output"]
        
        return input_cost + output_cost

    def _update_metrics(
        self,
        success: bool,
        tokens_used: int,
        cost: float,
        response_time: float,
        provider: AIProvider,
        request_type: RequestType
    ):
        """Update usage metrics"""
        self.usage_metrics.total_requests += 1
        
        if success:
            self.usage_metrics.successful_requests += 1
        else:
            self.usage_metrics.failed_requests += 1
        
        self.usage_metrics.total_tokens += tokens_used
        self.usage_metrics.total_cost += cost
        
        # Update average response time
        total_successful = self.usage_metrics.successful_requests
        if total_successful > 0:
            self.usage_metrics.average_response_time = (
                (self.usage_metrics.average_response_time * (total_successful - 1) + response_time) / total_successful
            )
        
        # Update request type counters
        request_type_str = request_type.value
        self.usage_metrics.requests_by_type[request_type_str] = (
            self.usage_metrics.requests_by_type.get(request_type_str, 0) + 1
        )
        
        # Update provider counters
        provider_str = provider.value
        self.usage_metrics.requests_by_provider[provider_str] = (
            self.usage_metrics.requests_by_provider.get(provider_str, 0) + 1
        )

    def get_usage_metrics(self) -> Dict[str, Any]:
        """Get current usage metrics"""
        return {
            "total_requests": self.usage_metrics.total_requests,
            "successful_requests": self.usage_metrics.successful_requests,
            "failed_requests": self.usage_metrics.failed_requests,
            "success_rate": (
                self.usage_metrics.successful_requests / max(self.usage_metrics.total_requests, 1)
            ),
            "total_tokens": self.usage_metrics.total_tokens,
            "total_cost": round(self.usage_metrics.total_cost, 4),
            "average_response_time": round(self.usage_metrics.average_response_time, 2),
            "requests_by_type": self.usage_metrics.requests_by_type,
            "requests_by_provider": self.usage_metrics.requests_by_provider,
            "last_reset": self.usage_metrics.last_reset.isoformat()
        }

    def reset_usage_metrics(self):
        """Reset usage metrics"""
        self.usage_metrics = UsageMetrics()
        logger.info("Usage metrics reset")

    def _classify_error(self, error: Exception) -> AIErrorType:
        """Classify API errors for better handling"""
        error_str = str(error).lower()
        
        if isinstance(error, openai.RateLimitError):
            return AIErrorType.RATE_LIMIT
        elif isinstance(error, openai.APITimeoutError):
            return AIErrorType.TIMEOUT
        elif isinstance(error, openai.APIConnectionError):
            return AIErrorType.CONNECTION
        elif isinstance(error, openai.AuthenticationError):
            return AIErrorType.AUTHENTICATION
        elif "quota" in error_str or "billing" in error_str:
            return AIErrorType.QUOTA_EXCEEDED
        elif "overloaded" in error_str or "capacity" in error_str:
            return AIErrorType.MODEL_OVERLOADED
        elif "invalid" in error_str or "bad request" in error_str:
            return AIErrorType.INVALID_REQUEST
        else:
            return AIErrorType.UNKNOWN

    def _update_circuit_breaker(self, provider: AIProvider, success: bool):
        """Update circuit breaker state based on API call result"""
        breaker = self.circuit_breakers[provider]
        
        if success:
            # Reset failure count on success
            breaker.failure_count = 0
            if breaker.state == "HALF_OPEN":
                breaker.state = "CLOSED"
                logger.info(f"Circuit breaker for {provider.value} closed after successful call")
        else:
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.now()
            
            if breaker.failure_count >= breaker.failure_threshold and breaker.state == "CLOSED":
                breaker.state = "OPEN"
                logger.warning(f"Circuit breaker for {provider.value} opened after {breaker.failure_count} failures")

    def _is_circuit_breaker_open(self, provider: AIProvider) -> bool:
        """Check if circuit breaker is open for a provider"""
        breaker = self.circuit_breakers[provider]
        
        if breaker.state == "CLOSED":
            return False
        elif breaker.state == "OPEN":
            # Check if recovery timeout has passed
            if breaker.last_failure_time and \
               (datetime.now() - breaker.last_failure_time).seconds >= breaker.recovery_timeout:
                breaker.state = "HALF_OPEN"
                logger.info(f"Circuit breaker for {provider.value} moved to half-open state")
                return False
            return True
        else:  # HALF_OPEN
            return False

    def _update_detailed_cost_metrics(self, model: str, cost: float, provider: AIProvider, request_type: RequestType):
        """Update detailed cost tracking metrics"""
        self.detailed_cost_metrics.total_cost += cost
        
        # Update cost by model
        self.detailed_cost_metrics.cost_by_model[model] = \
            self.detailed_cost_metrics.cost_by_model.get(model, 0.0) + cost
        
        # Update cost by provider
        provider_str = provider.value
        self.detailed_cost_metrics.cost_by_provider[provider_str] = \
            self.detailed_cost_metrics.cost_by_provider.get(provider_str, 0.0) + cost
        
        # Update cost by request type
        request_type_str = request_type.value
        self.detailed_cost_metrics.cost_by_request_type[request_type_str] = \
            self.detailed_cost_metrics.cost_by_request_type.get(request_type_str, 0.0) + cost
        
        # Update daily cost (reset if new day)
        now = datetime.now()
        if now.date() != self.detailed_cost_metrics.last_cost_reset.date():
            self.detailed_cost_metrics.daily_cost = 0.0
            self.detailed_cost_metrics.last_cost_reset = now
        
        self.detailed_cost_metrics.daily_cost += cost
        
        # Update monthly cost (approximate)
        if now.month != self.detailed_cost_metrics.last_cost_reset.month:
            self.detailed_cost_metrics.monthly_cost = 0.0
        
        self.detailed_cost_metrics.monthly_cost += cost
        
        # Check for cost alerts
        self._check_cost_alerts()

    def _check_cost_alerts(self):
        """Check if cost thresholds are exceeded and create alerts"""
        alerts = []
        
        if self.detailed_cost_metrics.daily_cost > self.daily_cost_threshold:
            alert = {
                "type": "daily_cost_exceeded",
                "threshold": self.daily_cost_threshold,
                "current": self.detailed_cost_metrics.daily_cost,
                "timestamp": datetime.now().isoformat()
            }
            alerts.append(alert)
            logger.warning(f"Daily cost threshold exceeded: ${self.detailed_cost_metrics.daily_cost:.2f} > ${self.daily_cost_threshold}")
        
        if self.detailed_cost_metrics.monthly_cost > self.monthly_cost_threshold:
            alert = {
                "type": "monthly_cost_exceeded",
                "threshold": self.monthly_cost_threshold,
                "current": self.detailed_cost_metrics.monthly_cost,
                "timestamp": datetime.now().isoformat()
            }
            alerts.append(alert)
            logger.warning(f"Monthly cost threshold exceeded: ${self.detailed_cost_metrics.monthly_cost:.2f} > ${self.monthly_cost_threshold}")
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.detailed_cost_metrics.cost_alerts = [
            alert for alert in self.detailed_cost_metrics.cost_alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
        
        # Add new alerts
        self.detailed_cost_metrics.cost_alerts.extend(alerts)

    def get_detailed_cost_metrics(self) -> Dict[str, Any]:
        """Get detailed cost tracking metrics"""
        return {
            "total_cost": round(self.detailed_cost_metrics.total_cost, 4),
            "daily_cost": round(self.detailed_cost_metrics.daily_cost, 4),
            "monthly_cost": round(self.detailed_cost_metrics.monthly_cost, 4),
            "cost_by_model": {k: round(v, 4) for k, v in self.detailed_cost_metrics.cost_by_model.items()},
            "cost_by_provider": {k: round(v, 4) for k, v in self.detailed_cost_metrics.cost_by_provider.items()},
            "cost_by_request_type": {k: round(v, 4) for k, v in self.detailed_cost_metrics.cost_by_request_type.items()},
            "cost_alerts": self.detailed_cost_metrics.cost_alerts,
            "thresholds": {
                "daily": self.daily_cost_threshold,
                "monthly": self.monthly_cost_threshold
            }
        }

    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error classification metrics"""
        return {
            "error_counts": {error_type.value: count for error_type, count in self.error_counts.items()},
            "circuit_breakers": {
                provider.value: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
                for provider, breaker in self.circuit_breakers.items()
            }
        }

    def _optimize_prompt_for_context(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt based on context and caching"""
        # Create a hash of the context for caching
        context_hash = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()
        
        # Check if we have a cached optimized prompt
        if context_hash in self.prompt_cache:
            logger.debug("Using cached optimized prompt")
            return self.prompt_cache[context_hash]
        
        # Optimize prompt based on context
        optimized_prompt = base_prompt
        
        # Add context-specific optimizations
        if context.get("user_experience_level") == "beginner":
            optimized_prompt += "\n\nIMPORTANT: The user is a beginner. Use simple language and provide more explanations."
        elif context.get("user_experience_level") == "advanced":
            optimized_prompt += "\n\nIMPORTANT: The user is advanced. You can use technical terms and be more concise."
        
        # Add time-based optimizations
        if context.get("time_available") == "limited":
            optimized_prompt += "\n\nIMPORTANT: The user has limited time. Keep responses concise and focused."
        
        # Cache the optimized prompt (limit cache size)
        if len(self.prompt_cache) > 100:
            # Remove oldest entries
            oldest_key = next(iter(self.prompt_cache))
            del self.prompt_cache[oldest_key]
        
        self.prompt_cache[context_hash] = optimized_prompt
        return optimized_prompt

    def get_system_prompt(self, snapshot: Dict[str, Any],agent_mode: Optional[AgentMode] = None) -> str:
        """Create an optimized system prompt based on user context"""
        
        base_prompt = (
        "You are upskillmee AI Mentor, an innovative AI learning mentor passionate about transforming education. "
        "Your approach combines personalized learning, gamification, and human-like interaction "
        "to help users discover their strengths and learn through enjoyable, engaging experiences."
        "\n\n"

        "=== BEHAVIOR RULES ===\n"
        "- Always start responses by addressing the user by name, e.g., 'Hey Swayam! 🌟'.\n"
        "- Use unique text icons, emojis, and playful metaphors to make concepts memorable.\n"
        "- Include ASCII/text diagrams or flowcharts when helpful.\n"
        "- Maintain your friendly, casual, and engaging mentor personality, with humor and creativity.\n"
        "- Answer clearly and precisely; avoid unnecessary filler.\n"
        "- Use lists, bullet points, numbered steps, or ASCII/diagram visuals for clarity.\n"
        "- Include icons, playful text diagrams, or examples when useful.\n"
        "- NEVER create learning plans yourself — DeepSeek handles that.\n"
        "- If a user requests a learning plan, respond:\n"
        "  'Learning plans are created by DeepSeek. Would you like me to request one for you?'\n"
        "- Start explanations with a short definition, then expand with examples, diagrams, or analogies.\n"
        "- Use a conversational, fun, human-like tone, but structure information clearly.\n"
        "- Focus on discovery-based learning: ask questions to explore the user's interests and experience.\n"
        "- MEMORY IS CRUCIAL: Review past conversation context and avoid repeating known info.\n"
        "- After 3–4 exchanges, suggest asking DeepSeek for a learning plan if appropriate.\n\n"
      
        "=== RESPONSE STRUCTURE & VISUAL STYLE ===\n"
        "- Always organize information visually:\n"
        "- For technical concepts, use:\n"
        "   • ASCII diagrams (→, ←, ⇄)\n"
        "   • Tables for comparisons\n"
        "   • Code snippets with inline comments\n"
        "   • Short 'memory hooks' (fun mnemonics or analogies)\n"
        "- Avoid overloading with emojis — use 2–4 per message, placed meaningfully.\n"
        "- When showing progression or flow, use creative text visuals like:\n"
        "   🧩 Concept → ⚙️ Process → 🚀 Application\n\n"

        "=== ENGAGEMENT HOOKS ===\n"
        "- After major explanations, ask 1 curiosity-based question (e.g., 'Want to see this in action?').\n"
        "- Occasionally use playful mini-challenges: 'Try explaining this in your own words — ready? 🤔'\n"
        "- When user shows progress, celebrate small wins (🎉, 🌱, 🚀).\n"
        "- Encourage reflection: 'What part of this clicked most for you?'\n\n"
       
        "=== LEARNER PERSONA CONTEXT ===\n"
        "- Assume the learner is a school or college student exploring career paths.\n"
        "- They are curious about finance, digital marketing, and design (especially UI/UX).\n"
        "- Use simple, engaging, real-world examples — like apps, brands, and startups they might know.\n"
        "- Relate abstract concepts to real applications:\n"
        "   e.g., 'Budgeting → like designing a spending dashboard in Figma,' or 'Marketing funnels → like UI user journeys.'\n"
        "- When explaining complex ideas, connect them to visual or creative contexts.\n"
        "- Use examples from YouTube, Instagram, startups, fintech apps, or modern design tools.\n"
        "- Occasionally link finance, design, and marketing together to show cross-domain learning (e.g., 'UX design impacts ad conversion rates!').\n"
        "- Encourage curiosity about how creative and analytical thinking combine.\n\n"


        "Core Principles:\n"
        "1. DISCOVERY-BASED LEARNING: Help users explore strengths and interests.\n"
        "2. PERSONALIZATION: Adapt to individual learning styles and goals.\n"
        "3. GAMIFICATION: Use challenges, rewards, and progression.\n"
        "4. PROJECT-BASED APPROACH: Focus on doing rather than consuming.\n"
        "5. CROSS-DOMAIN CONNECTIONS: Connect subjects in meaningful ways.\n\n"

        "When responding to users:\n"
        "- Be playful, creative, and human-like.\n"
        "- Ask targeted questions about interests instead of giving step-by-step plans.\n"
        "- Provide 1–2 interesting facts when a topic is mentioned.\n"
        "- Use lists, bullet points, and diagrams when explaining concepts.\n"
        "- Include icons, playful text diagrams, and examples to enhance understanding.\n"
        "- Avoid repeating information from memory.\n"
        "- Use humor lightly to make interactions enjoyable.\n\n"

        "=== LEARNING PLAN RULES ===\n"
        "- NEVER create learning plans.\n"
        "- Only DeepSeek can create plans.\n"
        "- Reference existing plans for guidance if present.\n"
        "- Ask about user progress and challenges, but do not modify or create plans.\n\n"

        "=== ADAPTIVE DEPTH & TONE ===\n"
        "- If the user sounds like a beginner: simplify terms, use analogies, and playful metaphors.\n"
        "- If the user sounds intermediate: balance theory and practical insights.\n"
        "- If the user sounds advanced: go deep into logic, architecture, or optimization.\n"
        "- Adjust tone dynamically — use humor and icons for casual chats, clarity and brevity for technical ones.\n"
        "- Always end with a reflective or curiosity-provoking question.\n\n"

        "=== CONTEXT & MEMORY USAGE ===\n"
        "- Review previous conversation history before replying.\n"
        "- Reference user’s previous questions or achievements subtly (e.g., 'Last time you explored APIs — this builds on that!').\n"
        "- Never repeat known information unless asked.\n"
        "- Build continuity like a real mentor remembering their student.\n\n"

        "=== FINAL INSTRUCTION ===\n"
        "- Give answers that are both structured and friendly.\n"
        "- Use diagrams, icons, and examples where helpful.\n"
        "- Maintain full context from memory.\n"
        "- Avoid unnecessary greetings or filler, but preserve your playful personality.\n"
    )


        # Add agent-role-specific instructions dynamically
        if agent_mode == AgentMode.CHAT:
          base_prompt += "\n\n=== AGENT ROLE ===\nYou are a mentor guiding the user. Use playful analogies, emojis, and ASCII diagrams. Avoid step-by-step plans."
        elif agent_mode == AgentMode.WORK:
          base_prompt += "\n\n=== AGENT ROLE ===\nYou are a project partner. Provide actionable instructions, code snippets, or project guidance. Keep tone clear and technical."
        elif agent_mode == AgentMode.PLAN:
           base_prompt += "\n\n=== AGENT ROLE ===\nYou handle learning plan creation. Never generate the plan yourself; delegate to DeepSeek. Ask clarifying questions if needed."

        # Add any special instructions (highest priority)
        if snapshot.get('special_instructions'):
            special_instructions = snapshot.get('special_instructions', {})

            # For topic exploration - specialized handling of topic mentions
            if 'topic_exploration' in special_instructions:
                base_prompt += f"\n\n=== SPECIAL INSTRUCTION FOR THIS MESSAGE ===\n{special_instructions['topic_exploration']}"

            # For no learning plan - general reminder
            elif 'no_learning_plan' in special_instructions:
                base_prompt += f"\n\n=== SPECIAL INSTRUCTION FOR THIS MESSAGE ===\n{special_instructions['no_learning_plan']}"

        # Inject prior-session context so AI Mentor can resume naturally
        prior_ctx = snapshot.get('prior_session_context')
        if prior_ctx and prior_ctx.get('is_returning_user'):
            base_prompt += "\n\n=== RETURNING USER — PRIOR SESSION MEMORY ===\n"
            base_prompt += (
                "IMPORTANT: This user has spoken with you before. "
                "Resume naturally — you are not meeting for the first time.\n"
            )
            if prior_ctx.get('last_session_topics'):
                topics_str = ", ".join(prior_ctx['last_session_topics'])
                base_prompt += f"Topics from previous sessions: {topics_str}\n"
            if prior_ctx.get('prior_summary'):
                base_prompt += f"\n{prior_ctx['prior_summary']}\n"
            base_prompt += (
                "\nWhen this user's first message arrives, acknowledge continuity naturally — "
                "e.g. 'Hey! Good to see you back — last time we were exploring [topic]...'. "
                "Do NOT say 'Welcome!' as if they are new. "
                "Do NOT repeat this instruction in your reply.\n"
            )

        # Add RAG context from embeddings if available (this is the memory upgrade)
        if snapshot.get('chat_history_summary'):
            chat_history = snapshot.get('chat_history_summary')

            # Add traditional summary if available
            if isinstance(chat_history, dict) and chat_history.get('summary'):
                base_prompt += f"\n\n=== CONVERSATION SUMMARY (Important for Context) ===\n{chat_history['summary']}"
            elif isinstance(chat_history, str):
                base_prompt += f"\n\n=== CONVERSATION SUMMARY (Important for Context) ===\n{chat_history}"

            # Add RAG contexts from similar past conversations if available
            if isinstance(chat_history, dict) and chat_history.get('rag_contexts') and len(chat_history['rag_contexts']) > 0:
                base_prompt += "\n\n=== RELEVANT PAST CONVERSATIONS (Use these for context) ===\n"
                for i, context in enumerate(chat_history['rag_contexts']):
                    base_prompt += f"Context {i+1}: {context}\n\n"

        # Add minimal user context if available
        user_context = snapshot.get('user_context', {})
        if user_context.get('name'):
            base_prompt += f"\n\nUser's name: {user_context['name']}"

        if user_context.get('skill_level'):
            base_prompt += f"\nSkill level: {user_context['skill_level']}"

        if user_context.get('interests'):
            interests = ", ".join(user_context['interests'])
            base_prompt += f"\nInterests: {interests}"

        if user_context.get('career_path'):
            base_prompt += f"\nCareer path: {user_context['career_path']}"

        # Add learning plan context if available
        if user_context.get('learning_plans') and len(user_context['learning_plans']) > 0:
            logger.info("MEMORY: Adding existing learning plan to system prompt for continuity")
            base_prompt += "\n\n=== EXISTING LEARNING PLAN (VERY IMPORTANT FOR MEMORY) ===\n"
            plan = user_context['learning_plans'][0]
            base_prompt += f"Plan title: {plan.get('title', 'Untitled')}\n"
            base_prompt += f"Plan description: {plan.get('description', 'No description')}\n\n"

            # Log that we're using the learning plan for context
            logger.info(f"MEMORY: Using learning plan '{plan.get('title', 'Untitled')}' for context")

            # Add projects if available
            if 'projects' in plan and isinstance(plan['projects'], list) and len(plan['projects']) > 0:
                base_prompt += "Projects in this plan:\n"
                logger.info(f"MEMORY: Adding {len(plan['projects'][:3])} projects to prompt")
                for i, project in enumerate(plan['projects'][:3]):  # Limit to first 3 projects to save space
                    base_prompt += f"- {project.get('title', f'Project {i+1}')}\n"
                    logger.info(f"MEMORY: Added project '{project.get('title', f'Project {i+1}')}' to prompt")

                # Add a reminder to use this plan for guidance
                base_prompt += "\nIMPORTANT: The user has this learning plan. You should reference it and guide them through it. Ask them about their progress, offer help with specific projects, and maintain continuity with this plan."
                
                # Log the final prompt section for debugging
                logger.info(f"MEMORY: Learning plan section added to prompt (length: {len(base_prompt.split('=== EXISTING LEARNING PLAN')[1]) if '=== EXISTING LEARNING PLAN' in base_prompt else 0} chars)")
        else:
            logger.info("MEMORY: No learning plans found in user context - AI will not have learning plan awareness")

        # Add final reminder to reinforce no learning plans
        base_prompt += "\n\nFINAL REMINDER: You are NEVER to create step-by-step learning plans. Your role is to explore topics through conversation with a casual, friendly tone, creative thinking, and appropriate humor. Be engaging, fun, and think outside the box to make learning exciting!"

        # Optimize prompt based on user context
        context = {
            "user_experience_level": snapshot.get('user_context', {}).get('skill_level', 'beginner'),
            "time_available": snapshot.get('user_context', {}).get('time_availability', 'flexible'),
            "learning_style": snapshot.get('user_context', {}).get('learning_style', 'visual')
        }
        
        optimized_prompt = self._optimize_prompt_for_context(base_prompt, context)
        return optimized_prompt

    async def get_ai_response(self, text: str, snapshot: Optional[Dict] = None, is_plan_request: bool = False) -> Tuple[str, Optional[Dict]]:
        """
        Main method to get AI response based on input text and user context

        Args:
            text: User input text
            snapshot: Optional user context snapshot
            is_plan_request: Flag indicating if this is a learning plan request

        Returns:
            Tuple of (response text, metadata)
        """
        start_time = time.time()
        if not snapshot:
            snapshot = {}

        # If is_plan_request is not explicitly set, check if this is a learning plan request
        if not is_plan_request:
            # First check if the snapshot has a flag indicating this is a learning plan request
            if snapshot and "special_instructions" in snapshot and "is_learning_plan_request" in snapshot["special_instructions"]:
                is_plan_request = snapshot["special_instructions"]["is_learning_plan_request"]
                logger.info(f"Using learning plan request flag from snapshot: {is_plan_request}")
            else:
                # Fall back to checking the text directly
                direct_requests = [
                    "create a learning plan", "make a learning plan", "build a learning plan",
                    "i want a learning plan", "i need a learning plan", "can you create a learning plan",
                    "could you make a learning plan", "create it again", "create the learning plan again",
                    "create a new learning plan", "make it again", "yes please create a learning plan"
                ]

                # Check for direct learning plan request
                is_plan_request = any(request.lower() in text.lower() for request in direct_requests)
                logger.info(f"Determined learning plan request from text: {is_plan_request}")

        # Log whether this is a learning plan request
        if is_plan_request:
            logger.info("AI_INTEGRATION: This is a learning plan request (explicit or detected)")

        # For simple greetings, just use GPT directly
        simple_greetings = ["hi", "hello", "hey", "hi there", "hello there",
                            "good morning", "good afternoon", "good evening"]
        is_simple_greeting = text.lower().strip() in simple_greetings

        if is_simple_greeting:
            # For greetings, use a simpler system prompt with higher temperature
            system_message = {"role": "system", "content": "You are upskillmee AI Mentor, a friendly, fun, and enthusiastic learning mentor. Keep your response to simple greetings warm, casual, and engaging - under 3 sentences with personality and a touch of humor. Be creative and make a great first impression!"}
            user_message = {"role": "user", "content": text}
            max_tokens = 100  # Shorter response for greetings
            temperature = 0.9  # More creative for personality and fun

            # Always use the AI model for greetings, no hardcoded fallbacks
            try:
                # Create response for greeting using the AI model
                response = await self._get_response_from_openai(
                    system_message=system_message,
                    user_message=user_message,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                logger.info(f"Generated greeting response in {time.time() - start_time:.2f}s")
                return response, None

            except Exception as e:
                # If there's an error, try to use a fallback model instead of hardcoded response
                logger.error(f"Error getting greeting response: {str(e)}")
                logger.warning("FALLBACK: Using fallback model for greeting response")
                return await self._handle_rate_limit(
                    client=self.openai_client,
                    model="gpt-4o",
                    system_message=system_message,
                    user_message=user_message,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

        # Handle learning plan requests directly
        if is_plan_request:
            logger.info("Processing learning plan request via DeepSeek")
            try:
                response_text, plan_data = await self._generate_learning_plan(text, snapshot)

                if plan_data:
                    metadata = {"learning_plan": plan_data}
                    logger.info(f"Generated learning plan successfully in {time.time() - start_time:.2f}s")
                    return response_text, metadata
                else:
                    logger.warning(f"DeepSeek failed to generate learning plan after {time.time() - start_time:.2f}s")
                    logger.error("FALLBACK: DeepSeek failed to generate learning plan, using fallback response")
                    # Fall back to OpenAI for explanation (but not plan generation)
                    return await self._get_fallback_response(text, snapshot)
            except Exception as e:
                logger.error(f"Error generating learning plan: {str(e)}")
                logger.error("FALLBACK: Error in learning plan generation, using fallback response")
                return await self._get_fallback_response(text, snapshot)

        # For regular conversations, use OpenAI with system prompt
        agent_mode = snapshot.get('agent_mode') if snapshot and 'agent_mode' in snapshot else None
        system_prompt = self.get_system_prompt(snapshot, agent_mode)
        system_message = {"role": "system", "content": system_prompt}
        user_message = {"role": "user", "content": text}

        # Set parameters based on message complexity
        max_tokens = 800
        temperature = 0.8  # Higher temperature for more creative, fun responses

        if len(text.split()) > 50:
            # For longer input, allow longer responses
            max_tokens = 1200
            temperature = 0.6  # More focused for complex topics

        try:
            # Regular conversation response
            response = await self._get_response_from_openai(
                system_message=system_message,
                user_message=user_message,
                max_tokens=max_tokens,
                temperature=temperature
            )

            logger.info(f"Generated response in {time.time() - start_time:.2f}s")
            return response, None

        except Exception as e:
            # Handle API errors and rate limits
            logger.error(f"Error getting AI response: {str(e)}")
            if "rate_limit" in str(e).lower():
                # Handle rate limits
                return await self._handle_rate_limit(
                    client=self.openai_client,
                    model="gpt-4o",
                    system_message=system_message,
                    user_message=user_message,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                # Try to use a fallback model instead of a generic error message
                logger.warning("FALLBACK: Attempting to use fallback model for regular response")
                try:
                    # Try with a simpler model and prompt
                    simple_system = {"role": "system", "content": "You are a helpful assistant. Respond briefly."}
                    return await self._handle_rate_limit(
                        client=self.openai_client,
                        model="gpt-3.5-turbo",
                        system_message=simple_system,
                        user_message=user_message,
                        max_tokens=100,
                        temperature=0.7
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    # Only use generic message as absolute last resort
                    logger.error("HARDCODED: Using hardcoded response as last resort fallback")
                    return "I'm having some technical difficulties at the moment. Could you please try again shortly?", None

    async def _get_response_from_openai(self, system_message: Dict[str, str], user_message: Dict[str, str], max_tokens: int, temperature: float) -> str:
        """
        Get response from OpenAI API with enhanced retry logic

        Args:
            system_message: System message dict
            user_message: User message dict
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Response text string
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        # Convert message dicts to proper format
        messages: List[Dict[str, str]] = [
            {"role": system_message["role"], "content": system_message["content"]},
            {"role": user_message["role"], "content": user_message["content"]}
        ]

        # Use enhanced retry logic
        result = await self._make_api_call_with_retry(
            client=self.openai_client,
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=AIProvider.OPENAI,
            request_type=RequestType.CHAT,
            timeout=settings.OPENAI_TIMEOUT
        )

        if result.success and result.content:
            return result.content
        else:
            # If primary call failed, try fallback
            logger.warning("Primary OpenAI call failed, attempting fallback")
            fallback_result = await self._make_api_call_with_retry(
                client=self.openai_client,
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=min(max_tokens, 4000),  # GPT-3.5 has lower token limit
                temperature=temperature,
                provider=AIProvider.OPENAI,
                request_type=RequestType.FALLBACK,
                timeout=settings.FALLBACK_TIMEOUT
            )
            
            if fallback_result.success and fallback_result.content:
                return fallback_result.content
            else:
                raise Exception(f"Both primary and fallback OpenAI calls failed: {result.error}")

    async def _handle_rate_limit(self, client: Optional[OpenAI], model: str, system_message: Dict[str, str], user_message: Dict[str, str], max_tokens: int, temperature: float) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle rate limit error by retrying with exponential backoff or fallback model"""
        logger.info(f"Handling rate limit for model {model}")
        if not client:
            logger.error("HARDCODED: Using hardcoded response for connection issues")
            return "I seem to be having trouble connecting to our systems right now. Could you give me a moment and try your question again shortly? I appreciate your understanding!", None

        # Convert message dicts to proper format
        messages: List[Dict[str, str]] = [
            {"role": system_message["role"], "content": system_message["content"]},
            {"role": user_message["role"], "content": user_message["content"]}
        ]

        # Try fallback models with enhanced retry logic
        fallback_models = ["gpt-4", "gpt-3.5-turbo"]

        for fallback_model in fallback_models:
            logger.info(f"Trying fallback model {fallback_model} due to rate limit")
            
            result = await self._make_api_call_with_retry(
                client=client,
                model=fallback_model,
                messages=messages,
                max_tokens=min(max_tokens, 4000) if fallback_model == "gpt-3.5-turbo" else max_tokens,
                temperature=temperature,
                provider=AIProvider.OPENAI,
                request_type=RequestType.FALLBACK,
                timeout=settings.FALLBACK_TIMEOUT
            )
            
            if result.success and result.content:
                return result.content, None

        # If all fallbacks fail, return a conversational error message
        logger.error("HARDCODED: Using hardcoded response after all fallback models failed")
        return "It seems our systems are quite busy at the moment. I'd love to help you, but could you please try again in a minute or two? Thank you for your patience!", None

    async def _get_fallback_response(self, text: str, snapshot: Optional[Dict] = None) -> Tuple[str, None]:
        """Generate a fallback response when learning plan generation fails"""
        logger.warning("FALLBACK: Using fallback response for learning plan generation failure")
        if snapshot:
            logger.debug(f"Fallback response has snapshot with {len(snapshot)} keys")

        system_message = {
            "role": "system",
            "content": (
                "You are upskillmee AI Mentor, a helpful AI learning mentor. The user has requested a learning plan, but "
                "our learning plan generation service is temporarily unavailable. "
                "Please apologize for the inconvenience and suggest some general tips for their learning journey. "
                "Ask them to try again later for a full personalized learning plan. "
                "Keep your response conversational and encouraging."
            )
        }
        user_message = {"role": "user", "content": text}

        try:
            response = await self._get_response_from_openai(
                system_message=system_message,
                user_message=user_message,
                max_tokens=400,
                temperature=0.7
            )
            return response, None
        except Exception as e:
            logger.error(f"Error getting fallback response: {str(e)}")
            logger.error("HARDCODED: Using hardcoded response for fallback response error")
            return "I'm experiencing some technical difficulties at the moment. Could you please try your request again in a few minutes?", None

    async def _generate_learning_plan(self, text: str, snapshot: Optional[Dict]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Generate a learning plan using DeepSeek or fallback to OpenAI with enhanced retry logic"""
        start_time = time.time()

        # Extract context for personalization
        context = self._extract_learning_context(text, snapshot)

        # Generate plan prompt
        plan_prompt = self._create_detailed_plan_prompt(text, context)

        # Try DeepSeek first (preferred for learning plans)
        if self.deepseek_client:
            logger.info("Attempting to generate learning plan with DeepSeek")

            messages: List[Dict[str, str]] = [
                {"role": "system", "content": "You are a learning plan expert focused on creating personalized, project-based learning experiences."},
                {"role": "user", "content": plan_prompt}
            ]

            result = await self._make_api_call_with_retry(
                client=self.deepseek_client,
                model="deepseek-chat",
                messages=messages,
                max_tokens=4000,
                temperature=0.7,
                provider=AIProvider.DEEPSEEK,
                request_type=RequestType.LEARNING_PLAN,
                timeout=settings.DEEPSEEK_TIMEOUT
            )

            if result.success and result.content:
                plan_data = self._parse_learning_plan_from_response(result.content)
                if plan_data:
                    logger.info(f"Successfully generated DeepSeek learning plan in {time.time() - start_time:.2f}s")
                    return "Great news! I've created a personalized learning plan for you based on our conversation. You can view it on your project board now.", plan_data

        # Fallback to OpenAI
        if self.openai_client:
            logger.info("Attempting to generate learning plan with OpenAI (fallback)")

            messages: List[Dict[str, str]] = [
                {"role": "system", "content": "You are a learning plan expert. Generate a structured learning plan with practical projects in valid JSON format."},
                {"role": "user", "content": plan_prompt + "\n\nIMPORTANT: Your response MUST be valid JSON that conforms to the structure specified above."}
            ]

            result = await self._make_api_call_with_retry(
                client=self.openai_client,
                model="gpt-4o",
                messages=messages,
                max_tokens=4000,
                temperature=0.7,
                provider=AIProvider.OPENAI,
                request_type=RequestType.LEARNING_PLAN,
                timeout=settings.OPENAI_TIMEOUT
            )

            if result.success and result.content:
                plan_data = self._parse_learning_plan_from_response(result.content)
                if plan_data:
                    logger.info(f"Successfully generated OpenAI fallback learning plan in {time.time() - start_time:.2f}s")
                    return "Great news! I've created a personalized learning plan for you based on our conversation. You can view it on your project board now.", plan_data

        # If everything fails, create a minimal plan
        logger.warning("All learning plan generation attempts failed, creating minimal plan")
        minimal_plan = self._create_minimal_learning_plan(text)
        return "Great news! I've created a personalized learning plan for you based on our conversation. You can view it on your project board now.", minimal_plan

    def _extract_learning_context(self, text: str, snapshot: Optional[Dict]) -> Dict[str, Any]:
        """Extract learning context from user text and snapshot"""
        context = {
            "experience_level": "beginner",
            "time_available": "flexible",
            "interests": [],
            "learning_goal": text
        }

        # Extract experience level from text
        experience_levels = ["beginner", "intermediate", "advanced", "expert"]
        for level in experience_levels:
            if level in text.lower():
                context["experience_level"] = level
                break

        # Extract interests from snapshot if available
        if snapshot and "user_context" in snapshot:
            user_context = snapshot.get("user_context", {})
            if "interests" in user_context:
                interests = user_context.get("interests", [])
                if interests and isinstance(interests, list):
                    context["interests"] = interests

        return context

    def _create_detailed_plan_prompt(self, text: str, context: Dict[str, Any]) -> str:
     """Create a high-quality, unique, and human-feeling learning plan"""
     interests = context.get("interests", [])
     experience_level = context.get("experience_level", "beginner")
     time_available = context.get("time_available", "flexible")

     twists = [
        "Solve the problem using only basic tools",
        "Add a creative twist inspired by art, music, or storytelling",
        "Visualize your results in an unexpected way",
        "Include a mini-challenge or ‘gamify’ the project",
        "Combine this project with a completely different skill area"
    ]

     mentor_tips = [
        "Pro tip: Try thinking of how this could be used in the real world.",
        "Fun idea: Add a quirky feature that surprises the user.",
        "Hint: Challenge yourself to do it in an unconventional way.",
        "Remember: The goal is to learn by making, not just following instructions."
    ]

     prompt = f"""
 You are a creative mentor who designs highly engaging, project-based learning experiences.
 User Goal: {text}
 Experience Level: {experience_level}
 Time Availability: {time_available}
 Interests: {', '.join(interests) if interests else 'None specified'}

Instructions for the AI:
1. Generate 3-5 projects, each progressively more challenging.
2. Each project must be hands-on and produce something tangible.
3. Include 3-5 detailed, actionable tasks per project.
4. Add 1-2 twists or creative constraints per project from the list: {', '.join(twists)}.
5. Add 1 mentor tip per project from: {', '.join(mentor_tips)}.
6. Specify skills learned and relevant resources.
7. Emphasize creativity, surprise, and cross-domain connections.
8. Format the response as valid JSON ONLY, with fields: title, description, tasks, skills, twists, tips, resources, weeks.

JSON FORMAT EXAMPLE:
{{
    "title": "Catchy Plan Title",
    "description": "Overview of the learning plan, exciting and fun",
    "projects": [
        {{
            "title": "Project 1: [Name]",
            "description": "What will be created and why it is valuable",
            "tasks": ["Task 1 detailed", "Task 2 detailed", "Task 3 detailed"],
            "skills": ["Skill 1", "Skill 2"],
            "twists": ["Twist 1", "Twist 2"],
            "tips": ["Mentor tip for encouragement or creativity"],
            "resources": ["Resource 1", "Resource 2"],
            "weeks": "Week 1-2"
        }}
    ]
}}

IMPORTANT:
- Make projects feel like a human mentor designed them.
- Projects should inspire curiosity and creativity, not just teach skills mechanically.
- Focus on tangible results, personal growth, and playful learning experiences.
"""

     return prompt.strip()

    def _parse_learning_plan_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse a learning plan from the response text"""
        try:
            # First try to find JSON blocks in code fences
            json_blocks = re.findall(r'```(?:json)?\s*({[\s\S]*?})```', response, re.DOTALL)

            if json_blocks:
                for block in json_blocks:
                    try:
                        data = json.loads(block)
                        if self._is_valid_learning_plan(data):
                            return data
                    except json.JSONDecodeError:
                        continue

            # If no valid JSON in code blocks, try to find raw JSON
            json_pattern = r'({[\s\S]*})'
            json_match = re.search(json_pattern, response)

            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    if self._is_valid_learning_plan(data):
                        return data
                except json.JSONDecodeError:
                    pass

            return None

        except Exception as e:
            logger.error(f"Error parsing learning plan: {str(e)}")
            return None

    def _is_valid_learning_plan(self, data: Dict[str, Any]) -> bool:
        """Check if the data represents a valid learning plan"""
        if not isinstance(data, dict):
            return False

        # Must have required fields
        required_fields = ["title", "description", "projects"]
        if not all(field in data for field in required_fields):
            return False

        # Projects must be a non-empty list
        if not isinstance(data["projects"], list) or not data["projects"]:
            return False

        # Each project must have required fields
        for project in data["projects"]:
            if not isinstance(project, dict):
                return False
            project_required = ["title", "description", "tasks"]
            if not all(field in project for field in project_required):
                return False

        return True

    def _create_minimal_learning_plan(self, text: str) -> Dict[str, Any]:
        """Create a minimal learning plan as fallback"""
        return {
            "title": f"Learning Plan: {text}",
            "description": f"A structured approach to learning {text}",
            "projects": [
                {
                    "title": "Getting Started",
                    "description": f"Introduction to {text} fundamentals",
                    "tasks": [
                        "Research basic concepts and terminology",
                        "Set up development environment",
                        "Complete introductory tutorial"
                    ],
                    "skills": ["Basic understanding", "Environment setup"],
                    "resources": ["Online documentation", "Beginner tutorials"],
                    "weeks": "Week 1"
                }
            ]
        }

    def convert_to_chat_completion_messages(self, messages: List[Dict[str, str]]) -> List[ChatCompletionMessageParam]:
        """Convert messages to OpenAI chat completion format"""
        chat_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            # Skip empty messages
            if not content:
                continue

            # Convert role to valid OpenAI role
            if role not in ['system', 'user', 'assistant', 'function']:
                role = 'user'

            # Add message
            chat_messages.append({"role": role, "content": content})

        return chat_messages