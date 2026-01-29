"""
InsightX AI - Analysis Service Tests

Unit tests for the deterministic analysis functions.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schemas import PrimaryFilters, IntentSchema, IntentType
from app.services.analysis_service import AnalysisService


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
def analysis_service(sample_csv):
    """Create analysis service with sample data."""
    service = AnalysisService(sample_csv)
    service.load_dataset()
    return service


class TestLoadDataset:
    """Tests for dataset loading."""
    
    def test_load_valid_csv(self, sample_csv):
        """Test loading a valid CSV file."""
        service = AnalysisService(sample_csv)
        result = service.load_dataset()
        assert result is True
        assert service.conn is not None
    
    def test_load_missing_file(self):
        """Test loading a non-existent file."""
        service = AnalysisService("/nonexistent/path.csv")
        with pytest.raises(FileNotFoundError):
            service.load_dataset()


class TestComputeFailureRate:
    """Tests for failure rate computation."""
    
    def test_overall_failure_rate(self, analysis_service):
        """Test computing overall failure rate."""
        result = analysis_service.compute_failure_rate()
        
        assert result.success is True
        assert result.metric == "failure_rate"
        assert len(result.numbers) >= 3
        
        # Check failure rate is around 10% (10 failed out of 100)
        failure_rate = result.numbers[0]
        assert failure_rate.label == "Failure Rate"
        assert "10" in failure_rate.value  # 10%
        
        # Check query was executed
        assert "SELECT" in result.query_executed
    
    def test_failure_rate_with_device_filter(self, analysis_service):
        """Test failure rate with device filter."""
        filters = PrimaryFilters(device="Android")
        result = analysis_service.compute_failure_rate(filters=filters)
        
        assert result.success is True
        assert "device = ?" in result.query_executed.lower() or "device =" in result.query_executed.lower()
    
    def test_failure_rate_with_time_window(self, analysis_service):
        """Test failure rate with time window."""
        time_window = {"period": "last_30_days"}
        result = analysis_service.compute_failure_rate(time_window=time_window)
        
        assert result.success is True


class TestAggregate:
    """Tests for aggregation functions."""
    
    def test_aggregate_volume(self, analysis_service):
        """Test aggregating transaction volume."""
        result = analysis_service.aggregate(metric="volume")
        
        assert result.success is True
        assert result.metric == "volume"
        assert len(result.numbers) >= 1
        assert result.numbers[0].raw_value == 100  # Total transactions
    
    def test_aggregate_by_category(self, analysis_service):
        """Test aggregating by category."""
        result = analysis_service.aggregate(metric="volume", by=["category"])
        
        assert result.success is True
        assert len(result.numbers) == 5  # 5 categories
        assert result.chart_data is not None
        assert result.chart_data.type.value == "bar"
    
    def test_aggregate_avg_amount(self, analysis_service):
        """Test aggregating average amount."""
        result = analysis_service.aggregate(metric="avg_amount")
        
        assert result.success is True
        assert result.numbers[0].raw_value > 0


class TestCompareSegments:
    """Tests for segment comparison."""
    
    def test_compare_android_vs_ios(self, analysis_service):
        """Test comparing Android vs iOS failure rate."""
        result = analysis_service.compare_segments(
            segment_a={"device": "Android"},
            segment_b={"device": "iOS"},
            metric="failure_rate"
        )
        
        assert result.success is True
        assert len(result.numbers) == 3  # A, B, and difference
        assert result.chart_data is not None
    
    def test_compare_with_filters(self, analysis_service):
        """Test comparison with additional filters."""
        filters = PrimaryFilters(category="Food")
        result = analysis_service.compare_segments(
            segment_a={"device": "Android"},
            segment_b={"device": "iOS"},
            metric="volume",
            filters=filters
        )
        
        assert result.success is True


class TestTimeSeries:
    """Tests for time series generation."""
    
    def test_time_series_volume(self, analysis_service):
        """Test generating time series of volume."""
        result = analysis_service.time_series(metric="volume")
        
        assert result.success is True
        assert result.chart_data is not None
        assert result.chart_data.type.value == "line"
    
    def test_time_series_failure_rate(self, analysis_service):
        """Test generating time series of failure rate."""
        result = analysis_service.time_series(metric="failure_rate")
        
        assert result.success is True


class TestTopFailureCodes:
    """Tests for top failure codes."""
    
    def test_get_top_failure_codes(self, analysis_service):
        """Test getting top failure codes."""
        result = analysis_service.get_top_failure_codes()
        
        assert result.success is True
        assert len(result.numbers) <= 10
        assert result.chart_data is not None


class TestExecutiveSummary:
    """Tests for executive summary."""
    
    def test_executive_summary(self, analysis_service):
        """Test generating executive summary."""
        result = analysis_service.get_executive_summary()
        
        assert result.success is True
        assert len(result.numbers) >= 5
        
        # Check key metrics are present
        labels = [n.label for n in result.numbers]
        assert "Total Transactions" in labels
        assert "Failure Rate" in labels


class TestIsMetricComputable:
    """Tests for metric computability guard."""
    
    def test_valid_metric(self, analysis_service):
        """Test valid metric check."""
        intent = IntentSchema(
            intent_type=IntentType.METRIC_QUERY,
            metric="failure_rate",
            primary_filters=PrimaryFilters()
        )
        
        can_compute, reason = analysis_service.is_metric_computable(intent)
        assert can_compute is True
    
    def test_invalid_metric(self, analysis_service):
        """Test invalid metric check."""
        intent = IntentSchema(
            intent_type=IntentType.METRIC_QUERY,
            metric="nonexistent_metric",
            primary_filters=PrimaryFilters()
        )
        
        can_compute, reason = analysis_service.is_metric_computable(intent)
        assert can_compute is False
        assert "not supported" in reason.lower()


# Cleanup
@pytest.fixture(autouse=True)
def cleanup(sample_csv):
    """Clean up temporary files after tests."""
    yield
    try:
        os.unlink(sample_csv)
    except:
        pass
