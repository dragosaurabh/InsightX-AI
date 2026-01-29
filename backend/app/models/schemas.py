"""
InsightX AI - Pydantic Models/Schemas

Defines request/response models for the API and internal data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class IntentType(str, Enum):
    """Types of user intents that can be extracted from queries."""
    METRIC_QUERY = "metric_query"
    COMPARISON = "comparison"
    TIME_SERIES = "time_series"
    SEGMENTATION = "segmentation"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class ChartType(str, Enum):
    """Types of charts that can be rendered in responses."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SPARKLINE = "sparkline"


# =============================================================================
# Intent Extraction Models
# =============================================================================

class PrimaryFilters(BaseModel):
    """Filters extracted from user query for data analysis."""
    device: Optional[str] = Field(None, description="Device type: Android, iOS, Web")
    state: Optional[str] = Field(None, description="Indian state name")
    age_group: Optional[str] = Field(None, description="Age group: <25, 25-34, 35-44, 45+")
    network: Optional[str] = Field(None, description="Network type: 4G, 5G, WiFi, 3G")
    category: Optional[str] = Field(None, description="Transaction category")
    payment_method: Optional[str] = Field(None, description="Payment method: UPI, Card, NetBanking")
    status: Optional[str] = Field(None, description="Transaction status: Success, Failed")


class ComparisonRequest(BaseModel):
    """Comparison parameters extracted from user query."""
    compare_with: Optional[str] = Field(None, description="Segment to compare with")
    time_window: Optional[str] = Field(None, description="Time window for comparison")


class TimeWindow(BaseModel):
    """Time window specification for queries."""
    from_date: Optional[str] = Field(None, alias="from", description="Start date YYYY-MM-DD or relative")
    to_date: Optional[str] = Field(None, alias="to", description="End date YYYY-MM-DD or relative")
    period: Optional[str] = Field(None, description="Relative period: last_7_days, last_30_days, etc.")


class IntentSchema(BaseModel):
    """Schema for extracted user intent from natural language query."""
    intent_type: IntentType = Field(..., description="Type of analytical intent")
    metric: Optional[str] = Field(None, description="Metric to analyze: failure_rate, avg_transaction_amount, volume")
    primary_filters: PrimaryFilters = Field(default_factory=PrimaryFilters, description="Data filters")
    comparison: Optional[ComparisonRequest] = Field(None, description="Comparison parameters if applicable")
    time_window: Optional[TimeWindow] = Field(None, description="Time window for analysis")
    follow_up_needed: bool = Field(False, description="Whether clarification is needed")
    follow_up_question: Optional[str] = Field(None, description="Clarification question if needed")
    raw_query: Optional[str] = Field(None, description="Original user query")


# =============================================================================
# Analysis Result Models
# =============================================================================

class CalculationDetail(BaseModel):
    """Details of a calculation performed."""
    numerator: Optional[Union[int, float]] = None
    denominator: Optional[Union[int, float]] = None
    formula: Optional[str] = None
    sample_size: Optional[int] = None


class NumberDetail(BaseModel):
    """A single numeric result with label and calculation details."""
    label: str = Field(..., description="Human-readable label for the number")
    value: str = Field(..., description="Formatted value with units")
    raw_value: Optional[Union[int, float]] = Field(None, description="Raw numeric value")
    calculation: Optional[CalculationDetail] = Field(None, description="How this was calculated")


class ChartDataPoint(BaseModel):
    """A single data point for charts."""
    x: Union[str, int, float, datetime]
    y: Union[int, float]
    label: Optional[str] = None


class ChartData(BaseModel):
    """Chart data for visualization."""
    type: ChartType = Field(..., description="Type of chart to render")
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    data: List[ChartDataPoint] = Field(default_factory=list)
    series_name: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of a deterministic analysis operation."""
    success: bool = True
    metric: str = Field(..., description="Metric that was analyzed")
    numbers: List[NumberDetail] = Field(default_factory=list, description="Computed numbers")
    query_executed: str = Field(..., description="SQL/DuckDB query that was executed")
    sample_rows: Optional[List[Dict[str, Any]]] = Field(None, description="Sample data rows")
    chart_data: Optional[ChartData] = Field(None, description="Data for chart visualization")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    execution_time_ms: Optional[float] = Field(None, description="Query execution time")


# =============================================================================
# API Request/Response Models
# =============================================================================

class ChatRequest(BaseModel):
    """Request body for /api/chat endpoint."""
    session_id: str = Field(..., description="Session identifier for context tracking")
    message: str = Field(..., min_length=1, max_length=2000, description="User's natural language query")


class ChatResponse(BaseModel):
    """Response from /api/chat endpoint."""
    answer_text: str = Field(..., description="Full natural language response")
    summary_line: str = Field(..., description="One-line summary for leadership (≤30 words)")
    numbers: List[NumberDetail] = Field(default_factory=list, description="Key statistics")
    query: str = Field(..., description="SQL query executed for transparency")
    chart: Optional[ChartData] = Field(None, description="Chart data if applicable")
    suggested_followups: List[str] = Field(default_factory=list, description="3 suggested follow-up questions")
    method: Optional[str] = Field(None, description="Brief explanation of analysis method")
    session_id: str = Field(..., description="Session ID for reference")
    request_id: str = Field(..., description="Unique request ID for audit logging")


class ClarificationResponse(BaseModel):
    """Response when clarification is needed."""
    needs_clarification: bool = True
    clarification_question: str = Field(..., description="Question to ask user")
    session_id: str
    request_id: str


class ErrorResponse(BaseModel):
    """Error response structure."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for categorization")
    request_id: str = Field(..., description="Request ID for debugging")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = Field(default_factory=dict)


# =============================================================================
# Session Models
# =============================================================================

class ConversationTurn(BaseModel):
    """A single turn in the conversation history."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    intent: Optional[IntentSchema] = Field(None, description="Extracted intent for user messages")
    analysis: Optional[AnalysisResult] = Field(None, description="Analysis result for assistant messages")


class SessionContext(BaseModel):
    """Session context for maintaining conversation history."""
    session_id: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
