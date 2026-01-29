"""
InsightX AI - LLM Service Tests

Tests for LLM service with mocked Gemini API responses.
"""

import json
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import AnalysisResult, IntentType, NumberDetail


# Mock settings before importing llm_service
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_api_key",
        "GEMINI_MODEL": "gemini-1.5-flash",
        "RATE_LIMIT_PER_MIN": "100"
    }):
        yield


class TestIntentExtraction:
    """Tests for intent extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_failure_rate_intent(self, mock_settings):
        """Test extracting failure rate intent."""
        from app.services.llm_service import LLMService
        
        mock_response = {
            "intent_type": "metric_query",
            "metric": "failure_rate",
            "primary_filters": {"device": None, "state": None},
            "time_window": {"period": "last_30_days"},
            "follow_up_needed": False
        }
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (json.dumps(mock_response), None)
            
            intent = await service.extract_intent(
                user_message="What is the failure rate in the last 30 days?",
                context="",
                session_id="test_session"
            )
            
            assert intent.intent_type == IntentType.METRIC_QUERY
            assert intent.metric == "failure_rate"
            assert intent.time_window.period == "last_30_days"
            assert intent.follow_up_needed is False
    
    @pytest.mark.asyncio
    async def test_extract_comparison_intent(self, mock_settings):
        """Test extracting comparison intent."""
        from app.services.llm_service import LLMService
        
        mock_response = {
            "intent_type": "comparison",
            "metric": "failure_rate",
            "primary_filters": {"device": "Android", "state": "Maharashtra"},
            "comparison": {"compare_with": "iOS"},
            "follow_up_needed": False
        }
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (json.dumps(mock_response), None)
            
            intent = await service.extract_intent(
                user_message="Compare Android vs iOS failure rate in Maharashtra",
                context=""
            )
            
            assert intent.intent_type == IntentType.COMPARISON
            assert intent.comparison.compare_with == "iOS"
    
    @pytest.mark.asyncio
    async def test_extract_ambiguous_intent(self, mock_settings):
        """Test extracting ambiguous intent that needs clarification."""
        from app.services.llm_service import LLMService
        
        mock_response = {
            "intent_type": "clarification",
            "follow_up_needed": True,
            "follow_up_question": "Which metric would you like to analyze?"
        }
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (json.dumps(mock_response), None)
            
            intent = await service.extract_intent(
                user_message="Tell me something",
                context=""
            )
            
            assert intent.follow_up_needed is True
            assert intent.follow_up_question is not None
    
    @pytest.mark.asyncio
    async def test_handle_api_error(self, mock_settings):
        """Test handling API errors gracefully."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (None, "API error: 500")
            
            intent = await service.extract_intent(
                user_message="What is the failure rate?",
                context=""
            )
            
            # Should return unknown intent with clarification
            assert intent.intent_type == IntentType.UNKNOWN
            assert intent.follow_up_needed is True


class TestExplanationGeneration:
    """Tests for explanation generation."""
    
    @pytest.mark.asyncio
    async def test_explain_success(self, mock_settings):
        """Test successful explanation generation."""
        from app.services.llm_service import LLMService
        
        mock_response = {
            "summary_line": "Failure rate is 3.5%, below the 5% threshold.",
            "details": [
                {"label": "Failure Rate", "value": "3.5%", "insight": "Healthy level"}
            ],
            "method": "Calculated as failed transactions / total transactions.",
            "recommended_actions": ["Monitor peak hours", "Investigate 3G failures"],
            "suggested_followups": ["Why is 3G failing?", "Show daily trend"]
        }
        
        analysis_result = AnalysisResult(
            success=True,
            metric="failure_rate",
            numbers=[
                NumberDetail(label="Failure Rate", value="3.5%", raw_value=3.5),
                NumberDetail(label="Total Transactions", value="100,000", raw_value=100000)
            ],
            query_executed="SELECT COUNT(*) FROM transactions"
        )
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (json.dumps(mock_response), None)
            
            explanation = await service.explain_results(
                analysis_result=analysis_result,
                user_message="What is the failure rate?",
                context=""
            )
            
            assert "summary_line" in explanation
            assert "3.5%" in explanation["summary_line"]
            assert len(explanation["suggested_followups"]) > 0
    
    @pytest.mark.asyncio
    async def test_explain_with_fallback(self, mock_settings):
        """Test fallback explanation when API fails."""
        from app.services.llm_service import LLMService
        
        analysis_result = AnalysisResult(
            success=True,
            metric="failure_rate",
            numbers=[
                NumberDetail(label="Failure Rate", value="3.5%", raw_value=3.5)
            ],
            query_executed="SELECT COUNT(*) FROM transactions"
        )
        
        service = LLMService()
        
        with patch.object(service, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = (None, "API error")
            
            explanation = await service.explain_results(
                analysis_result=analysis_result,
                user_message="What is the failure rate?",
                context=""
            )
            
            # Should return fallback explanation
            assert "summary_line" in explanation
            assert "Failure Rate: 3.5%" in explanation["summary_line"]


class TestRateLimiting:
    """Tests for rate limiting."""
    
    def test_rate_limiter_allows_normal_usage(self, mock_settings):
        """Test rate limiter allows normal requests."""
        from app.services.llm_service import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        for i in range(10):
            assert limiter.is_allowed("session_1") is True
    
    def test_rate_limiter_blocks_excessive_usage(self, mock_settings):
        """Test rate limiter blocks excessive requests."""
        from app.services.llm_service import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            limiter.is_allowed("session_1")
        
        # 6th request should be blocked
        assert limiter.is_allowed("session_1") is False
    
    def test_rate_limiter_isolates_sessions(self, mock_settings):
        """Test rate limiter isolates different sessions."""
        from app.services.llm_service import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Use up session_1's limit
        limiter.is_allowed("session_1")
        limiter.is_allowed("session_1")
        
        # session_2 should still be allowed
        assert limiter.is_allowed("session_2") is True


class TestJsonParsing:
    """Tests for JSON response parsing."""
    
    def test_parse_clean_json(self, mock_settings):
        """Test parsing clean JSON."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        json_str = '{"key": "value"}'
        result = service._parse_json_response(json_str)
        
        assert result == {"key": "value"}
    
    def test_parse_json_with_markdown(self, mock_settings):
        """Test parsing JSON wrapped in markdown code block."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        json_str = '```json\n{"key": "value"}\n```'
        result = service._parse_json_response(json_str)
        
        assert result == {"key": "value"}
    
    def test_parse_invalid_json(self, mock_settings):
        """Test parsing invalid JSON returns None."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        result = service._parse_json_response("not valid json")
        
        assert result is None
