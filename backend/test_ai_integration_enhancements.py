#!/usr/bin/env python3
"""
Test script for enhanced AI Integration Service improvements
Tests retry logic, cost tracking, error handling, and monitoring features
"""

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai_integration_service import (
    AIIntegrationService, 
    AIProvider, 
    RequestType, 
    AIErrorType,
    CircuitBreakerState,
    DetailedCostMetrics
)
from app.config import settings

class TestAIIntegrationEnhancements:
    """Test suite for AI integration enhancements"""
    
    def __init__(self):
        self.ai_service = AIIntegrationService()
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_error_classification(self):
        """Test error classification functionality"""
        print("\n=== Testing Error Classification ===")
        
        # Mock different types of errors
        import openai
        
        # Test rate limit error
        rate_limit_error = openai.RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        error_type = self.ai_service._classify_error(rate_limit_error)
        self.log_test(
            "Rate Limit Error Classification",
            error_type == AIErrorType.RATE_LIMIT,
            f"Expected RATE_LIMIT, got {error_type}"
        )
        
        # Test timeout error
        timeout_error = openai.APITimeoutError("Request timed out")
        error_type = self.ai_service._classify_error(timeout_error)
        self.log_test(
            "Timeout Error Classification",
            error_type == AIErrorType.TIMEOUT,
            f"Expected TIMEOUT, got {error_type}"
        )
        
        # Test connection error
        connection_error = openai.APIConnectionError("Connection failed")
        error_type = self.ai_service._classify_error(connection_error)
        self.log_test(
            "Connection Error Classification",
            error_type == AIErrorType.CONNECTION,
            f"Expected CONNECTION, got {error_type}"
        )
        
        # Test authentication error
        auth_error = openai.AuthenticationError("Invalid API key", response=Mock(), body=None)
        error_type = self.ai_service._classify_error(auth_error)
        self.log_test(
            "Authentication Error Classification",
            error_type == AIErrorType.AUTHENTICATION,
            f"Expected AUTHENTICATION, got {error_type}"
        )
        
        # Test unknown error
        unknown_error = Exception("Some unknown error")
        error_type = self.ai_service._classify_error(unknown_error)
        self.log_test(
            "Unknown Error Classification",
            error_type == AIErrorType.UNKNOWN,
            f"Expected UNKNOWN, got {error_type}"
        )
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        print("\n=== Testing Circuit Breaker ===")
        
        provider = AIProvider.OPENAI
        breaker = self.ai_service.circuit_breakers[provider]
        
        # Test initial state
        self.log_test(
            "Circuit Breaker Initial State",
            breaker.state == "CLOSED",
            f"Expected CLOSED, got {breaker.state}"
        )
        
        # Test failure tracking
        for i in range(breaker.failure_threshold):
            self.ai_service._update_circuit_breaker(provider, success=False)
        
        self.log_test(
            "Circuit Breaker Opens After Failures",
            breaker.state == "OPEN",
            f"Expected OPEN after {breaker.failure_threshold} failures, got {breaker.state}"
        )
        
        # Test circuit breaker check
        is_open = self.ai_service._is_circuit_breaker_open(provider)
        self.log_test(
            "Circuit Breaker Check When Open",
            is_open == True,
            f"Expected True, got {is_open}"
        )
        
        # Test success resets failure count
        self.ai_service._update_circuit_breaker(provider, success=True)
        self.log_test(
            "Circuit Breaker Resets on Success",
            breaker.failure_count == 0,
            f"Expected 0 failures, got {breaker.failure_count}"
        )
    
    def test_cost_tracking(self):
        """Test detailed cost tracking"""
        print("\n=== Testing Cost Tracking ===")
        
        # Test cost calculation
        cost = self.ai_service._calculate_cost("gpt-4o", 1000)
        expected_cost = (700 * 0.0025 / 1000) + (300 * 0.01 / 1000)  # 70% input, 30% output
        self.log_test(
            "Cost Calculation Accuracy",
            abs(cost - expected_cost) < 0.0001,
            f"Expected ~{expected_cost:.4f}, got {cost:.4f}"
        )
        
        # Test detailed cost metrics update
        initial_cost = self.ai_service.detailed_cost_metrics.total_cost
        self.ai_service._update_detailed_cost_metrics(
            "gpt-4o", 0.05, AIProvider.OPENAI, RequestType.CHAT
        )
        
        self.log_test(
            "Cost Metrics Update",
            self.ai_service.detailed_cost_metrics.total_cost == initial_cost + 0.05,
            f"Expected {initial_cost + 0.05}, got {self.ai_service.detailed_cost_metrics.total_cost}"
        )
        
        # Test cost breakdown by model
        model_cost = self.ai_service.detailed_cost_metrics.cost_by_model.get("gpt-4o", 0)
        self.log_test(
            "Cost Breakdown by Model",
            model_cost >= 0.05,
            f"Expected at least 0.05 for gpt-4o, got {model_cost}"
        )
        
        # Test cost breakdown by provider
        provider_cost = self.ai_service.detailed_cost_metrics.cost_by_provider.get("openai", 0)
        self.log_test(
            "Cost Breakdown by Provider",
            provider_cost >= 0.05,
            f"Expected at least 0.05 for openai, got {provider_cost}"
        )
    
    def test_cost_alerts(self):
        """Test cost alert functionality"""
        print("\n=== Testing Cost Alerts ===")
        
        # Set low threshold for testing
        original_threshold = self.ai_service.daily_cost_threshold
        self.ai_service.daily_cost_threshold = 0.01
        
        # Trigger cost alert
        self.ai_service._update_detailed_cost_metrics(
            "gpt-4o", 0.02, AIProvider.OPENAI, RequestType.CHAT
        )
        
        # Check if alert was created
        alerts = self.ai_service.detailed_cost_metrics.cost_alerts
        daily_alert_exists = any(alert["type"] == "daily_cost_exceeded" for alert in alerts)
        
        self.log_test(
            "Daily Cost Alert Generation",
            daily_alert_exists,
            f"Expected daily cost alert, got {len(alerts)} alerts"
        )
        
        # Restore original threshold
        self.ai_service.daily_cost_threshold = original_threshold
    
    def test_prompt_optimization(self):
        """Test prompt optimization and caching"""
        print("\n=== Testing Prompt Optimization ===")
        
        base_prompt = "You are a helpful assistant."
        context = {
            "user_experience_level": "beginner",
            "time_available": "limited"
        }
        
        # Test prompt optimization
        optimized_prompt = self.ai_service._optimize_prompt_for_context(base_prompt, context)
        
        self.log_test(
            "Prompt Contains Base Content",
            base_prompt in optimized_prompt,
            "Base prompt should be included in optimized version"
        )
        
        self.log_test(
            "Prompt Contains Beginner Optimization",
            "beginner" in optimized_prompt.lower(),
            "Should contain beginner-specific instructions"
        )
        
        self.log_test(
            "Prompt Contains Time Optimization",
            "limited time" in optimized_prompt.lower(),
            "Should contain time-limited instructions"
        )
        
        # Test caching
        cached_prompt = self.ai_service._optimize_prompt_for_context(base_prompt, context)
        self.log_test(
            "Prompt Caching Works",
            optimized_prompt == cached_prompt,
            "Cached prompt should be identical"
        )
        
        # Test cache size limit
        cache_size_before = len(self.ai_service.prompt_cache)
        self.log_test(
            "Prompt Cache Populated",
            cache_size_before > 0,
            f"Cache should have entries, found {cache_size_before}"
        )
    
    def test_metrics_collection(self):
        """Test metrics collection and reporting"""
        print("\n=== Testing Metrics Collection ===")
        
        # Test basic metrics
        basic_metrics = self.ai_service.get_usage_metrics()
        required_fields = [
            "total_requests", "successful_requests", "failed_requests",
            "success_rate", "total_tokens", "total_cost", "average_response_time"
        ]
        
        for field in required_fields:
            self.log_test(
                f"Basic Metrics Contains {field}",
                field in basic_metrics,
                f"Field {field} should be in basic metrics"
            )
            
        # Test detailed cost metrics
        cost_metrics = self.ai_service.get_detailed_cost_metrics()
        cost_fields = [
            "total_cost", "daily_cost", "monthly_cost",
            "cost_by_model", "cost_by_provider", "cost_by_request_type"
        ]
        
        for field in cost_fields:
            self.log_test(
                f"Cost Metrics Contains {field}",
                field in cost_metrics,
                f"Field {field} should be in cost metrics"
            )
        
        # Test error metrics
        error_metrics = self.ai_service.get_error_metrics()
        error_fields = ["error_counts", "circuit_breakers"]
        
        for field in error_fields:
            self.log_test(
                f"Error Metrics Contains {field}",
                field in error_metrics,
                f"Field {field} should be in error metrics"
            )
    
    async def test_retry_logic_simulation(self):
        """Test retry logic with simulated failures"""
        print("\n=== Testing Retry Logic Simulation ===")
        
        # Mock OpenAI client to simulate failures
        mock_client = Mock()
        
        # Test successful retry after failures
        call_count = 0
        def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise openai.RateLimitError("Rate limit", response=Mock(), body=None)
            
            # Success on 3rd attempt
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.total_tokens = 100
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        
        # Test the retry logic
        result = await self.ai_service._make_api_call_with_retry(
            client=mock_client,
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=100,
            temperature=0.7,
            provider=AIProvider.OPENAI,
            request_type=RequestType.CHAT
        )
        
        self.log_test(
            "Retry Logic Success After Failures",
            result.success and result.retry_count == 2,
            f"Expected success with 2 retries, got success={result.success}, retries={result.retry_count}"
        )
        
        self.log_test(
            "Retry Logic Response Content",
            result.content == "Test response",
            f"Expected 'Test response', got '{result.content}'"
        )
    
    def test_configuration_validation(self):
        """Test configuration and initialization"""
        print("\n=== Testing Configuration ===")
        
        # Test retry configuration
        retry_config = self.ai_service.retry_config
        self.log_test(
            "Retry Config Max Retries",
            retry_config.max_retries >= 1,
            f"Max retries should be at least 1, got {retry_config.max_retries}"
        )
        
        self.log_test(
            "Retry Config Base Delay",
            retry_config.base_delay > 0,
            f"Base delay should be positive, got {retry_config.base_delay}"
        )
        
        # Test cost tracking configuration
        self.log_test(
            "Daily Cost Threshold Set",
            self.ai_service.daily_cost_threshold > 0,
            f"Daily threshold should be positive, got {self.ai_service.daily_cost_threshold}"
        )
        
        self.log_test(
            "Monthly Cost Threshold Set",
            self.ai_service.monthly_cost_threshold > 0,
            f"Monthly threshold should be positive, got {self.ai_service.monthly_cost_threshold}"
        )
        
        # Test circuit breaker configuration
        for provider in [AIProvider.OPENAI, AIProvider.DEEPSEEK]:
            breaker = self.ai_service.circuit_breakers[provider]
            self.log_test(
                f"Circuit Breaker Config for {provider.value}",
                breaker.failure_threshold > 0 and breaker.recovery_timeout > 0,
                f"Threshold: {breaker.failure_threshold}, Timeout: {breaker.recovery_timeout}"
            )
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting AI Integration Enhancement Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run synchronous tests
        self.test_error_classification()
        self.test_circuit_breaker()
        self.test_cost_tracking()
        self.test_cost_alerts()
        self.test_prompt_optimization()
        self.test_metrics_collection()
        self.test_configuration_validation()
        
        # Run asynchronous tests
        await self.test_retry_logic_simulation()
        
        # Summary
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("🏁 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Execution Time: {end_time - start_time:.2f}s")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Export test results
        with open("ai_integration_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "execution_time": end_time - start_time
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results exported to: ai_integration_test_results.json")
        
        return failed_tests == 0

async def main():
    """Main test execution"""
    tester = TestAIIntegrationEnhancements()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! AI Integration enhancements are working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Please review the results above.")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)