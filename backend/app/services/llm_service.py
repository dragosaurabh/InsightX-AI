"""
InsightX AI - LLM Service

Gemini API wrapper with intent extraction and explanation generation.
Includes rate limiting and anti-hallucination guardrails.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from collections import defaultdict

import httpx

from app.config import get_settings
from app.models.schemas import (
    AnalysisResult,
    ComparisonRequest,
    IntentSchema,
    IntentType,
    PrimaryFilters,
    TimeWindow,
)
from app.prompts.templates import (
    CLARIFICATION_SYSTEM,
    EXPLANATION_SYSTEM,
    EXPLANATION_USER_TEMPLATE,
    INSUFFICIENT_DATA_RESPONSE,
    INTENT_EXTRACTION_SYSTEM,
    INTENT_EXTRACTION_USER_TEMPLATE,
    RATE_LIMIT_RESPONSE,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter per session."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, session_id: str) -> bool:
        """Check if request is allowed for session."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self._requests[session_id] = [
            ts for ts in self._requests[session_id] 
            if ts > window_start
        ]
        
        if len(self._requests[session_id]) >= self.max_requests:
            return False
        
        self._requests[session_id].append(now)
        return True


class LLMService:
    """
    Service for LLM interactions using Google Gemini API.
    
    Provides intent extraction and explanation generation with
    anti-hallucination guardrails and rate limiting.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self):
        """Initialize LLM service."""
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_per_min,
            window_seconds=60
        )
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def _call_gemini(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Make a call to Gemini API.
        
        Args:
            prompt: User prompt.
            system_instruction: System instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.
            
        Returns:
            Tuple of (response_text, error_message).
        """
        url = f"{self.GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            }
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract text from response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"], None
            
            return None, "No response generated"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text}")
            return None, f"API error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            return None, str(e)
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        if not text:
            return None
        
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nText: {text[:500]}")
            return None
    
    async def extract_intent(
        self,
        user_message: str,
        context: str = "",
        session_id: str = ""
    ) -> IntentSchema:
        """
        Extract intent from user message.
        
        Args:
            user_message: User's natural language query.
            context: Previous conversation context.
            session_id: Session ID for rate limiting.
            
        Returns:
            Extracted IntentSchema.
        """
        # Rate limit check
        if session_id and not self.rate_limiter.is_allowed(session_id):
            return IntentSchema(
                intent_type=IntentType.CLARIFICATION,
                follow_up_needed=True,
                follow_up_question=RATE_LIMIT_RESPONSE,
                raw_query=user_message
            )
        
        prompt = INTENT_EXTRACTION_USER_TEMPLATE.format(
            user_message=user_message,
            context=context or "No previous context."
        )
        
        response_text, error = await self._call_gemini(
            prompt=prompt,
            system_instruction=INTENT_EXTRACTION_SYSTEM,
            temperature=0.0,
            max_tokens=800
        )
        
        if error:
            logger.error(f"Intent extraction failed: {error}")
            return IntentSchema(
                intent_type=IntentType.UNKNOWN,
                follow_up_needed=True,
                follow_up_question="I'm having trouble understanding your request. Could you rephrase it?",
                raw_query=user_message
            )
        
        parsed = self._parse_json_response(response_text)
        
        if not parsed:
            return IntentSchema(
                intent_type=IntentType.UNKNOWN,
                follow_up_needed=True,
                follow_up_question="I couldn't parse your request. Could you be more specific?",
                raw_query=user_message
            )
        
        # Build IntentSchema from parsed JSON
        try:
            intent_type = IntentType(parsed.get("intent_type", "unknown"))
        except ValueError:
            intent_type = IntentType.UNKNOWN
        
        # Parse primary filters
        filters_data = parsed.get("primary_filters", {})
        primary_filters = PrimaryFilters(
            device=filters_data.get("device"),
            state=filters_data.get("state"),
            age_group=filters_data.get("age_group"),
            network=filters_data.get("network"),
            category=filters_data.get("category"),
            payment_method=filters_data.get("payment_method"),
            status=filters_data.get("status")
        )
        
        # Parse time window
        time_data = parsed.get("time_window", {})
        time_window = None
        if time_data:
            time_window = TimeWindow(
                from_date=time_data.get("from"),
                to_date=time_data.get("to"),
                period=time_data.get("period")
            )
        
        # Parse comparison
        comparison_data = parsed.get("comparison", {})
        comparison = None
        if comparison_data and comparison_data.get("compare_with"):
            comparison = ComparisonRequest(
                compare_with=comparison_data.get("compare_with"),
                time_window=comparison_data.get("time_window")
            )
        
        return IntentSchema(
            intent_type=intent_type,
            metric=parsed.get("metric"),
            primary_filters=primary_filters,
            comparison=comparison,
            time_window=time_window,
            follow_up_needed=parsed.get("follow_up_needed", False),
            follow_up_question=parsed.get("follow_up_question"),
            raw_query=user_message
        )
    
    async def explain_results(
        self,
        analysis_result: AnalysisResult,
        user_message: str,
        context: str = "",
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate explanation for analysis results.
        
        Args:
            analysis_result: Deterministic analysis result.
            user_message: Original user query.
            context: Conversation context.
            session_id: Session ID for rate limiting.
            
        Returns:
            Explanation dictionary with summary, details, method, etc.
        """
        if not analysis_result.success:
            return {
                "summary_line": "Analysis could not be completed due to an error.",
                "details": [],
                "method": "N/A",
                "recommended_actions": ["Try a different query"],
                "suggested_followups": ["What data is available?"],
                "error": analysis_result.error
            }
        
        # Rate limit check
        if session_id and not self.rate_limiter.is_allowed(session_id):
            return {
                "summary_line": "Rate limit exceeded. Please wait.",
                "details": [],
                "method": "N/A",
                "recommended_actions": [],
                "suggested_followups": [],
                "rate_limited": True
            }
        
        # Prepare analysis JSON for prompt
        analysis_json = {
            "metric": analysis_result.metric,
            "numbers": [
                {
                    "label": n.label,
                    "value": n.value,
                    "raw_value": n.raw_value,
                    "calculation": n.calculation.model_dump() if n.calculation else None
                }
                for n in analysis_result.numbers
            ],
            "query_executed": analysis_result.query_executed,
            "has_chart": analysis_result.chart_data is not None,
            "execution_time_ms": analysis_result.execution_time_ms
        }
        
        prompt = EXPLANATION_USER_TEMPLATE.format(
            user_message=user_message,
            analysis_json=json.dumps(analysis_json, indent=2, default=str)
        )
        
        response_text, error = await self._call_gemini(
            prompt=prompt,
            system_instruction=EXPLANATION_SYSTEM,
            temperature=0.2,
            max_tokens=1000
        )
        
        if error:
            logger.error(f"Explanation generation failed: {error}")
            # Fallback to basic explanation
            return self._generate_fallback_explanation(analysis_result, user_message)
        
        parsed = self._parse_json_response(response_text)
        
        if not parsed:
            return self._generate_fallback_explanation(analysis_result, user_message)
        
        return {
            "summary_line": parsed.get("summary_line", "Analysis complete."),
            "details": parsed.get("details", []),
            "method": parsed.get("method", "Aggregation query on transaction data."),
            "recommended_actions": parsed.get("recommended_actions", []),
            "suggested_followups": parsed.get("suggested_followups", [])
        }
    
    def _generate_fallback_explanation(
        self,
        analysis_result: AnalysisResult,
        user_message: str
    ) -> Dict[str, Any]:
        """Generate a basic explanation without LLM."""
        numbers = analysis_result.numbers
        
        if not numbers:
            return {
                "summary_line": "No data found matching your criteria.",
                "details": [],
                "method": "Query executed but returned no results.",
                "recommended_actions": ["Broaden your filters", "Check date range"],
                "suggested_followups": [
                    "What is the overall failure rate?",
                    "Show me all transactions"
                ]
            }
        
        # Build summary from first number
        first_num = numbers[0]
        summary = f"{first_num.label}: {first_num.value}"
        
        details = [
            {
                "label": n.label,
                "value": n.value,
                "insight": ""
            }
            for n in numbers
        ]
        
        return {
            "summary_line": summary,
            "details": details,
            "method": f"Computed using: {analysis_result.query_executed[:100]}...",
            "recommended_actions": [
                "Compare with other segments",
                "Analyze trend over time"
            ],
            "suggested_followups": [
                "How does this compare to last month?",
                "What are the top failure reasons?",
                "Show breakdown by device"
            ]
        }
    
    async def generate_clarification(
        self,
        user_message: str,
        reason: str = ""
    ) -> str:
        """
        Generate a clarification question for ambiguous queries.
        
        Args:
            user_message: Original user message.
            reason: Why clarification is needed.
            
        Returns:
            Clarification question string.
        """
        prompt = f"""User asked: "{user_message}"

Reason for clarification: {reason or "Query is ambiguous."}

Generate a helpful clarification question."""
        
        response_text, error = await self._call_gemini(
            prompt=prompt,
            system_instruction=CLARIFICATION_SYSTEM,
            temperature=0.3,
            max_tokens=200
        )
        
        if error or not response_text:
            return "Could you please be more specific about what you'd like to analyze?"
        
        return response_text.strip()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
