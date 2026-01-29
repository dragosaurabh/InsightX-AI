"""
InsightX AI - Chat API Endpoint

Main chat endpoint that orchestrates intent extraction, analysis, and explanation.
"""

import logging
import uuid
from typing import Union

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import (
    AnalysisResult,
    ChatRequest,
    ChatResponse,
    ClarificationResponse,
    ErrorResponse,
    IntentType,
    NumberDetail,
)
from app.services.analysis_service import get_analysis_service
from app.services.llm_service import get_llm_service
from app.services.session_service import get_session_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/chat",
    response_model=Union[ChatResponse, ClarificationResponse],
    responses={
        200: {"model": ChatResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    tags=["Chat"]
)
async def chat(request: ChatRequest) -> Union[ChatResponse, ClarificationResponse]:
    """
    Main chat endpoint for conversational analytics.
    
    Flow:
    1. Fetch session context
    2. Extract intent from user message using LLM
    3. Validate intent (ask for clarification if ambiguous)
    4. Map intent to analysis functions
    5. Execute deterministic analysis
    6. Generate explanation using LLM
    7. Persist turn in session
    8. Return structured response
    
    Args:
        request: ChatRequest with session_id and message.
        
    Returns:
        ChatResponse with analysis results, or ClarificationResponse if clarification needed.
    """
    request_id = str(uuid.uuid4())[:8]
    
    try:
        settings = get_settings()
        session_service = get_session_service()
        llm_service = get_llm_service()
        analysis_service = get_analysis_service(settings.data_path)
        
        # 1. Get session context
        context = session_service.get_context_string(request.session_id)
        
        # 2. Extract intent
        logger.info(f"[{request_id}] Extracting intent from: {request.message[:100]}...")
        intent = await llm_service.extract_intent(
            user_message=request.message,
            context=context,
            session_id=request.session_id
        )
        
        # 3. Check if clarification is needed
        if intent.follow_up_needed or intent.intent_type == IntentType.CLARIFICATION:
            clarification = intent.follow_up_question or await llm_service.generate_clarification(
                user_message=request.message,
                reason="Ambiguous query"
            )
            
            # Persist user message
            session_service.add_turn(request.session_id, "user", request.message)
            session_service.add_turn(request.session_id, "assistant", clarification)
            
            return ClarificationResponse(
                needs_clarification=True,
                clarification_question=clarification,
                session_id=request.session_id,
                request_id=request_id
            )
        
        # 4. Validate intent can be computed
        if intent.intent_type == IntentType.UNKNOWN:
            return ClarificationResponse(
                needs_clarification=True,
                clarification_question="I'm not sure what analysis you're looking for. Could you please specify what metric or comparison you'd like to see?",
                session_id=request.session_id,
                request_id=request_id
            )
        
        can_compute, reason = analysis_service.is_metric_computable(intent)
        if not can_compute:
            return ClarificationResponse(
                needs_clarification=True,
                clarification_question=reason,
                session_id=request.session_id,
                request_id=request_id
            )
        
        # 5. Map intent to analysis and execute
        logger.info(f"[{request_id}] Executing analysis: {intent.intent_type} - {intent.metric}")
        analysis_result = await _execute_analysis(intent, analysis_service)
        
        if not analysis_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {analysis_result.error}"
            )
        
        # 6. Generate explanation
        logger.info(f"[{request_id}] Generating explanation...")
        explanation = await llm_service.explain_results(
            analysis_result=analysis_result,
            user_message=request.message,
            context=context,
            session_id=request.session_id
        )
        
        # 7. Build response
        response = ChatResponse(
            answer_text=_build_answer_text(explanation, analysis_result),
            summary_line=explanation.get("summary_line", "Analysis complete."),
            numbers=analysis_result.numbers,
            query=analysis_result.query_executed,
            chart=analysis_result.chart_data,
            suggested_followups=explanation.get("suggested_followups", [])[:3],
            method=explanation.get("method"),
            session_id=request.session_id,
            request_id=request_id
        )
        
        # 8. Persist turn in session
        session_service.add_turn(request.session_id, "user", request.message)
        session_service.add_turn(request.session_id, "assistant", response.answer_text)
        
        logger.info(f"[{request_id}] Response generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred processing your request. Request ID: {request_id}"
        )


async def _execute_analysis(intent, analysis_service) -> AnalysisResult:
    """Map intent to analysis function and execute."""
    
    # Build time window dict if present
    time_window = None
    if intent.time_window:
        time_window = {
            "from": intent.time_window.from_date,
            "to": intent.time_window.to_date,
            "period": intent.time_window.period
        }
    
    # Handle different intent types
    if intent.intent_type == IntentType.COMPARISON:
        # Parse comparison segments
        segment_a = {}
        segment_b = {}
        
        # Try to determine segments from intent
        if intent.comparison and intent.comparison.compare_with:
            # Simple device comparison
            if intent.comparison.compare_with.lower() in ["android", "ios", "web"]:
                if intent.primary_filters.device:
                    segment_a = {"device": intent.primary_filters.device}
                    segment_b = {"device": intent.comparison.compare_with}
                else:
                    segment_a = {"device": "Android"}
                    segment_b = {"device": intent.comparison.compare_with}
        else:
            # Default comparison
            segment_a = {"device": "Android"}
            segment_b = {"device": "iOS"}
        
        return analysis_service.compare_segments(
            segment_a=segment_a,
            segment_b=segment_b,
            metric=intent.metric or "failure_rate",
            filters=intent.primary_filters,
            time_window=time_window
        )
    
    elif intent.intent_type == IntentType.TIME_SERIES:
        return analysis_service.time_series(
            metric=intent.metric or "volume",
            filters=intent.primary_filters,
            time_window=time_window,
            period="day"
        )
    
    elif intent.intent_type == IntentType.SEGMENTATION:
        # Determine grouping column
        group_by = ["category"]  # Default
        if intent.primary_filters.device:
            group_by = ["device"]
        elif intent.primary_filters.age_group:
            group_by = ["age_group"]
        
        return analysis_service.aggregate(
            metric=intent.metric or "volume",
            by=group_by,
            filters=intent.primary_filters,
            time_window=time_window
        )
    
    else:  # METRIC_QUERY or default
        metric = intent.metric or "failure_rate"
        
        if metric.lower() == "failure_codes":
            return analysis_service.get_top_failure_codes(
                filters=intent.primary_filters,
                time_window=time_window
            )
        elif metric.lower() == "executive_summary":
            return analysis_service.get_executive_summary(time_window=time_window)
        elif "failure" in metric.lower():
            return analysis_service.compute_failure_rate(
                filters=intent.primary_filters,
                time_window=time_window
            )
        else:
            return analysis_service.aggregate(
                metric=metric,
                filters=intent.primary_filters,
                time_window=time_window
            )


def _build_answer_text(explanation: dict, analysis_result: AnalysisResult) -> str:
    """Build full answer text from explanation and analysis."""
    parts = []
    
    # Summary line
    summary = explanation.get("summary_line", "")
    if summary:
        parts.append(f"**{summary}**\n")
    
    # Details
    details = explanation.get("details", [])
    if details:
        parts.append("\n**Key Numbers:**")
        for detail in details[:5]:
            label = detail.get("label", "")
            value = detail.get("value", "")
            insight = detail.get("insight", "")
            if insight:
                parts.append(f"- {label}: {value} — {insight}")
            else:
                parts.append(f"- {label}: {value}")
    
    # Method
    method = explanation.get("method", "")
    if method:
        parts.append(f"\n**Method:** {method}")
    
    # Recommended actions
    actions = explanation.get("recommended_actions", [])
    if actions:
        parts.append("\n**Recommended Actions:**")
        for action in actions[:3]:
            parts.append(f"- {action}")
    
    return "\n".join(parts)
