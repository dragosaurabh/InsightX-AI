"""
InsightX AI - Chat Flow Integration Tests

End-to-end tests for the /api/chat endpoint.
"""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_csv():
    """Create a temporary CSV file with sample data."""
    data = {
        "transaction_id": [f"txn_{i}" for i in range(100)],
        "timestamp": pd.date_range("2025-01-01", periods=100, freq="H"),
        "amount": [100.0 + i * 10 for i in range(100)],
        "payment_method": ["UPI", "Card", "NetBanking"] * 33 + ["UPI"],
        "device": ["Android", "iOS", "Web"] * 33 + ["Android"],
        "state": ["Maharashtra", "Karnataka", "Tamil Nadu"] * 33 + ["Maharashtra"],
        "age_group": ["<25", "25-34", "35-44", "45+"] * 25,
        "network": ["4G", "5G", "WiFi", "3G"] * 25,
        "category": ["Food", "Entertainment", "Travel", "Utilities", "Others"] * 20,
        "status": ["Success"] * 90 + ["Failed"] * 10,
        "failure_code": [""] * 90 + ["TIMEOUT", "NETWORK_ERROR", "BANK_DECLINED"] * 3 + ["TIMEOUT"],
        "fraud_flag": [0] * 98 + [1, 1],
        "review_flag": [0] * 95 + [1] * 5,
    }
    
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f, index=False)
        return f.name


@pytest.fixture
def mock_env(sample_csv):
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_api_key",
        "GEMINI_MODEL": "gemini-1.5-flash",
        "DATA_PATH": sample_csv,
        "FRONTEND_ORIGIN": "http://localhost:3000",
        "MAX_CONTEXT_TURNS": "6",
        "RATE_LIMIT_PER_MIN": "100"
    }):
        yield


@pytest.fixture
def app(mock_env):
    """Create test FastAPI app."""
    # Reset singletons
    import app.services.analysis_service as analysis_module
    import app.services.llm_service as llm_module
    import app.services.session_service as session_module
    import app.config as config_module
    
    analysis_module._analysis_service = None
    llm_module._llm_service = None
    session_module._session_service = None
    config_module.get_settings.cache_clear()
    
    from app.main import app
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""
    
    def test_chat_failure_rate_query(self, client, mock_env):
        """Test chat with failure rate query."""
        # Mock LLM responses
        intent_response = {
            "intent_type": "metric_query",
            "metric": "failure_rate",
            "primary_filters": {},
            "time_window": None,
            "follow_up_needed": False
        }
        
        explanation_response = {
            "summary_line": "Overall failure rate is 10% based on 100 transactions.",
            "details": [{"label": "Failure Rate", "value": "10%", "insight": "Within normal range"}],
            "method": "Calculated as failed / total transactions.",
            "recommended_actions": ["Monitor trends"],
            "suggested_followups": ["Show by device", "Compare last week"]
        }
        
        with patch('app.services.llm_service.LLMService._call_gemini', new_callable=AsyncMock) as mock_gemini:
            # First call for intent, second for explanation
            mock_gemini.side_effect = [
                (json.dumps(intent_response), None),
                (json.dumps(explanation_response), None)
            ]
            
            response = client.post(
                "/api/chat",
                json={
                    "session_id": "test_session_1",
                    "message": "What is the overall failure rate?"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "answer_text" in data
            assert "summary_line" in data
            assert "numbers" in data
            assert "query" in data
            assert "session_id" in data
            assert "request_id" in data
            
            # Check summary line
            assert "10%" in data["summary_line"]
            
            # Check numbers are present
            assert len(data["numbers"]) > 0
            
            # Check SQL query is included
            assert "SELECT" in data["query"]
    
    def test_chat_comparison_query(self, client, mock_env):
        """Test chat with comparison query."""
        intent_response = {
            "intent_type": "comparison",
            "metric": "failure_rate",
            "primary_filters": {"device": "Android"},
            "comparison": {"compare_with": "iOS"},
            "follow_up_needed": False
        }
        
        explanation_response = {
            "summary_line": "Android has 12% failure rate vs iOS at 8%.",
            "details": [],
            "method": "Compared failure rates across device types.",
            "recommended_actions": [],
            "suggested_followups": []
        }
        
        with patch('app.services.llm_service.LLMService._call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.side_effect = [
                (json.dumps(intent_response), None),
                (json.dumps(explanation_response), None)
            ]
            
            response = client.post(
                "/api/chat",
                json={
                    "session_id": "test_session_2",
                    "message": "Compare Android vs iOS failure rate"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "numbers" in data
    
    def test_chat_clarification_needed(self, client, mock_env):
        """Test chat returns clarification when needed."""
        intent_response = {
            "intent_type": "clarification",
            "metric": None,
            "primary_filters": {},
            "follow_up_needed": True,
            "follow_up_question": "Which metric would you like to analyze: failure rate, volume, or average amount?"
        }
        
        with patch('app.services.llm_service.LLMService._call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = (json.dumps(intent_response), None)
            
            response = client.post(
                "/api/chat",
                json={
                    "session_id": "test_session_3",
                    "message": "Analyze something"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should be a clarification response
            assert data.get("needs_clarification") is True
            assert "clarification_question" in data
    
    def test_chat_maintains_session(self, client, mock_env):
        """Test chat maintains session context across messages."""
        intent_response = {
            "intent_type": "metric_query",
            "metric": "volume",
            "primary_filters": {},
            "follow_up_needed": False
        }
        
        explanation_response = {
            "summary_line": "Total volume is 100 transactions.",
            "details": [],
            "method": "Count of transactions.",
            "recommended_actions": [],
            "suggested_followups": []
        }
        
        with patch('app.services.llm_service.LLMService._call_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.side_effect = [
                (json.dumps(intent_response), None),
                (json.dumps(explanation_response), None),
                (json.dumps(intent_response), None),
                (json.dumps(explanation_response), None)
            ]
            
            # First message
            response1 = client.post(
                "/api/chat",
                json={
                    "session_id": "test_session_context",
                    "message": "Show me transaction volume"
                }
            )
            
            assert response1.status_code == 200
            
            # Second message with same session
            response2 = client.post(
                "/api/chat",
                json={
                    "session_id": "test_session_context",
                    "message": "Now show by category"
                }
            )
            
            assert response2.status_code == 200
            
            # Session IDs should match
            assert response1.json()["session_id"] == response2.json()["session_id"]
    
    def test_chat_empty_message_rejected(self, client, mock_env):
        """Test that empty messages are rejected."""
        response = client.post(
            "/api/chat",
            json={
                "session_id": "test_session_4",
                "message": ""
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_missing_session_id_rejected(self, client, mock_env):
        """Test that missing session_id is rejected."""
        response = client.post(
            "/api/chat",
            json={
                "message": "What is the failure rate?"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "InsightX AI API"
        assert "version" in data
        assert "docs" in data


# Cleanup
@pytest.fixture(autouse=True)
def cleanup(sample_csv):
    """Clean up temporary files after tests."""
    yield
    try:
        os.unlink(sample_csv)
    except:
        pass
