"""
InsightX AI - Analysis Service

Provides deterministic data analysis functions using DuckDB/Pandas.
All functions return structured JSON with query transparency for explainability.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
import pandas as pd

from app.models.schemas import (
    AnalysisResult,
    CalculationDetail,
    ChartData,
    ChartDataPoint,
    ChartType,
    IntentSchema,
    NumberDetail,
    PrimaryFilters,
)


class AnalysisService:
    """
    Service for performing deterministic analytics on transaction data.
    
    Uses DuckDB for fast SQL aggregations with full query transparency.
    All methods return AnalysisResult with the executed query for explainability.
    """
    
    def __init__(self, data_path: str):
        """
        Initialize the analysis service.
        
        Args:
            data_path: Path to the transactions CSV file.
        """
        self.data_path = data_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.table_name = "transactions"
        self._required_columns = {
            "transaction_id", "timestamp", "amount", "payment_method",
            "device", "state", "age_group", "network", "category",
            "status", "failure_code", "fraud_flag", "review_flag"
        }
    
    def load_dataset(self) -> bool:
        """
        Load the CSV dataset into DuckDB.
        
        Returns:
            True if loaded successfully, False otherwise.
            
        Raises:
            FileNotFoundError: If the data file doesn't exist.
            ValueError: If required columns are missing.
        """
        path = Path(self.data_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        # Create in-memory DuckDB connection
        self.conn = duckdb.connect(":memory:")
        
        # Load CSV into DuckDB
        self.conn.execute(f"""
            CREATE TABLE {self.table_name} AS 
            SELECT * FROM read_csv_auto('{self.data_path}', header=true)
        """)
        
        # Validate columns
        columns = self.conn.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{self.table_name}'
        """).fetchall()
        actual_columns = {col[0].lower() for col in columns}
        
        missing = self._required_columns - actual_columns
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Add computed columns
        self.conn.execute(f"""
            ALTER TABLE {self.table_name} 
            ADD COLUMN IF NOT EXISTS date_only DATE;
        """)
        self.conn.execute(f"""
            UPDATE {self.table_name} 
            SET date_only = CAST(timestamp AS DATE);
        """)
        
        return True
    
    def _build_where_clause(self, filters: PrimaryFilters) -> tuple[str, List[Any]]:
        """Build WHERE clause from filters."""
        conditions = []
        params = []
        
        filter_map = {
            "device": filters.device,
            "state": filters.state,
            "age_group": filters.age_group,
            "network": filters.network,
            "category": filters.category,
            "payment_method": filters.payment_method,
            "status": filters.status,
        }
        
        for col, val in filter_map.items():
            if val is not None:
                conditions.append(f"{col} = ?")
                params.append(val)
        
        where = " AND ".join(conditions) if conditions else "1=1"
        return where, params
    
    def _apply_time_window(
        self, 
        base_where: str, 
        time_window: Optional[Dict[str, Any]] = None
    ) -> tuple[str, List[Any]]:
        """Apply time window filters."""
        if not time_window:
            return base_where, []
        
        params = []
        
        # Handle relative periods
        period = time_window.get("period")
        if period:
            now = datetime.now()
            if period == "last_7_days":
                start = now - timedelta(days=7)
            elif period == "last_30_days":
                start = now - timedelta(days=30)
            elif period == "last_90_days":
                start = now - timedelta(days=90)
            else:
                start = now - timedelta(days=30)  # Default
            
            base_where += f" AND timestamp >= '{start.strftime('%Y-%m-%d')}'"
        
        # Handle explicit date ranges
        from_date = time_window.get("from_date") or time_window.get("from")
        to_date = time_window.get("to_date") or time_window.get("to")
        
        if from_date:
            base_where += f" AND timestamp >= '{from_date}'"
        if to_date:
            base_where += f" AND timestamp <= '{to_date}'"
        
        return base_where, params
    
    def compute_failure_rate(
        self, 
        filters: Optional[PrimaryFilters] = None,
        time_window: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Compute transaction failure rate.
        
        Args:
            filters: Optional filters to apply.
            time_window: Optional time window.
            
        Returns:
            AnalysisResult with failure rate, counts, and sample rows.
        """
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric="failure_rate",
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        filters = filters or PrimaryFilters()
        where, params = self._build_where_clause(filters)
        where, time_params = self._apply_time_window(where, time_window)
        
        query = f"""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_transactions,
                ROUND(
                    100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / 
                    NULLIF(COUNT(*), 0), 2
                ) as failure_rate_pct
            FROM {self.table_name}
            WHERE {where}
        """
        
        try:
            result = self.conn.execute(query).fetchone()
            total = result[0] or 0
            failed = result[1] or 0
            rate = result[2] or 0.0
            
            # Get sample failed rows
            sample_query = f"""
                SELECT transaction_id, timestamp, amount, device, state, 
                       category, failure_code
                FROM {self.table_name}
                WHERE {where} AND status = 'Failed'
                LIMIT 5
            """
            sample_rows = self.conn.execute(sample_query).fetchdf().to_dict('records')
            
            execution_time = (time.time() - start_time) * 1000
            
            return AnalysisResult(
                success=True,
                metric="failure_rate",
                numbers=[
                    NumberDetail(
                        label="Failure Rate",
                        value=f"{rate}%",
                        raw_value=rate,
                        calculation=CalculationDetail(
                            numerator=failed,
                            denominator=total,
                            formula="(failed_transactions / total_transactions) * 100"
                        )
                    ),
                    NumberDetail(
                        label="Total Transactions",
                        value=f"{total:,}",
                        raw_value=total
                    ),
                    NumberDetail(
                        label="Failed Transactions",
                        value=f"{failed:,}",
                        raw_value=failed
                    )
                ],
                query_executed=query.strip(),
                sample_rows=sample_rows,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric="failure_rate",
                query_executed=query.strip(),
                error=str(e)
            )
    
    def aggregate(
        self,
        metric: str,
        by: Optional[List[str]] = None,
        filters: Optional[PrimaryFilters] = None,
        time_window: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Perform aggregation on a metric.
        
        Args:
            metric: Metric to aggregate (volume, avg_amount, total_amount, count).
            by: Columns to group by.
            filters: Optional filters.
            time_window: Optional time window.
            
        Returns:
            AnalysisResult with aggregated values.
        """
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        filters = filters or PrimaryFilters()
        where, params = self._build_where_clause(filters)
        where, _ = self._apply_time_window(where, time_window)
        
        # Build aggregation expression
        metric_expr_map = {
            "volume": "COUNT(*)",
            "count": "COUNT(*)",
            "avg_amount": "ROUND(AVG(amount), 2)",
            "total_amount": "ROUND(SUM(amount), 2)",
            "avg_transaction_amount": "ROUND(AVG(amount), 2)",
            "failure_rate": "ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2)"
        }
        
        metric_expr = metric_expr_map.get(metric.lower(), "COUNT(*)")
        
        if by:
            group_cols = ", ".join(by)
            query = f"""
                SELECT {group_cols}, {metric_expr} as {metric}
                FROM {self.table_name}
                WHERE {where}
                GROUP BY {group_cols}
                ORDER BY {metric} DESC
                LIMIT 20
            """
        else:
            query = f"""
                SELECT {metric_expr} as {metric}
                FROM {self.table_name}
                WHERE {where}
            """
        
        try:
            df = self.conn.execute(query).fetchdf()
            execution_time = (time.time() - start_time) * 1000
            
            numbers = []
            chart_data = None
            
            if by:
                # Create chart data for grouped results
                data_points = []
                for _, row in df.iterrows():
                    label_parts = [str(row[col]) for col in by]
                    label = " - ".join(label_parts)
                    value = row[metric]
                    numbers.append(NumberDetail(
                        label=label,
                        value=self._format_metric_value(metric, value),
                        raw_value=float(value) if pd.notna(value) else 0
                    ))
                    data_points.append(ChartDataPoint(
                        x=label,
                        y=float(value) if pd.notna(value) else 0
                    ))
                
                chart_data = ChartData(
                    type=ChartType.BAR,
                    title=f"{metric.replace('_', ' ').title()} by {', '.join(by)}",
                    data=data_points
                )
            else:
                value = df.iloc[0][metric] if len(df) > 0 else 0
                numbers.append(NumberDetail(
                    label=metric.replace("_", " ").title(),
                    value=self._format_metric_value(metric, value),
                    raw_value=float(value) if pd.notna(value) else 0
                ))
            
            return AnalysisResult(
                success=True,
                metric=metric,
                numbers=numbers,
                query_executed=query.strip(),
                chart_data=chart_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed=query.strip(),
                error=str(e)
            )
    
    def compare_segments(
        self,
        segment_a: Dict[str, str],
        segment_b: Dict[str, str],
        metric: str,
        filters: Optional[PrimaryFilters] = None,
        time_window: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Compare a metric between two segments.
        
        Args:
            segment_a: First segment filter (e.g., {"device": "Android"}).
            segment_b: Second segment filter (e.g., {"device": "iOS"}).
            metric: Metric to compare.
            filters: Additional base filters.
            time_window: Optional time window.
            
        Returns:
            AnalysisResult with comparison values.
        """
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        filters = filters or PrimaryFilters()
        base_where, _ = self._build_where_clause(filters)
        base_where, _ = self._apply_time_window(base_where, time_window)
        
        # Build segment conditions
        seg_a_conds = " AND ".join([f"{k} = '{v}'" for k, v in segment_a.items()])
        seg_b_conds = " AND ".join([f"{k} = '{v}'" for k, v in segment_b.items()])
        
        metric_expr_map = {
            "failure_rate": "ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2)",
            "avg_amount": "ROUND(AVG(amount), 2)",
            "volume": "COUNT(*)",
            "total_amount": "ROUND(SUM(amount), 2)"
        }
        metric_expr = metric_expr_map.get(metric.lower(), "COUNT(*)")
        
        query = f"""
            SELECT 
                'Segment A' as segment,
                {metric_expr} as {metric},
                COUNT(*) as sample_size
            FROM {self.table_name}
            WHERE {base_where} AND {seg_a_conds}
            
            UNION ALL
            
            SELECT 
                'Segment B' as segment,
                {metric_expr} as {metric},
                COUNT(*) as sample_size
            FROM {self.table_name}
            WHERE {base_where} AND {seg_b_conds}
        """
        
        try:
            df = self.conn.execute(query).fetchdf()
            execution_time = (time.time() - start_time) * 1000
            
            seg_a_label = " & ".join([f"{k}: {v}" for k, v in segment_a.items()])
            seg_b_label = " & ".join([f"{k}: {v}" for k, v in segment_b.items()])
            
            val_a = float(df.iloc[0][metric]) if len(df) > 0 else 0
            val_b = float(df.iloc[1][metric]) if len(df) > 1 else 0
            size_a = int(df.iloc[0]["sample_size"]) if len(df) > 0 else 0
            size_b = int(df.iloc[1]["sample_size"]) if len(df) > 1 else 0
            
            diff = val_a - val_b
            pct_diff = (diff / val_b * 100) if val_b != 0 else 0
            
            numbers = [
                NumberDetail(
                    label=f"{metric.replace('_', ' ').title()} ({seg_a_label})",
                    value=self._format_metric_value(metric, val_a),
                    raw_value=val_a,
                    calculation=CalculationDetail(sample_size=size_a)
                ),
                NumberDetail(
                    label=f"{metric.replace('_', ' ').title()} ({seg_b_label})",
                    value=self._format_metric_value(metric, val_b),
                    raw_value=val_b,
                    calculation=CalculationDetail(sample_size=size_b)
                ),
                NumberDetail(
                    label="Difference",
                    value=f"{diff:+.2f} ({pct_diff:+.1f}%)",
                    raw_value=diff
                )
            ]
            
            chart_data = ChartData(
                type=ChartType.BAR,
                title=f"{metric.replace('_', ' ').title()} Comparison",
                data=[
                    ChartDataPoint(x=seg_a_label, y=val_a),
                    ChartDataPoint(x=seg_b_label, y=val_b)
                ]
            )
            
            return AnalysisResult(
                success=True,
                metric=metric,
                numbers=numbers,
                query_executed=query.strip(),
                chart_data=chart_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed=query.strip(),
                error=str(e)
            )
    
    def time_series(
        self,
        metric: str,
        time_col: str = "date_only",
        period: str = "day",
        filters: Optional[PrimaryFilters] = None,
        time_window: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None
    ) -> AnalysisResult:
        """
        Generate time series data for a metric.
        
        Args:
            metric: Metric to analyze.
            time_col: Time column to use.
            period: Aggregation period (day, week, month).
            filters: Optional filters.
            time_window: Optional time window.
            group_by: Optional additional grouping column.
            
        Returns:
            AnalysisResult with time series data.
        """
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        filters = filters or PrimaryFilters()
        where, _ = self._build_where_clause(filters)
        where, _ = self._apply_time_window(where, time_window)
        
        # Build time truncation
        if period == "week":
            time_expr = f"DATE_TRUNC('week', {time_col})"
        elif period == "month":
            time_expr = f"DATE_TRUNC('month', {time_col})"
        else:
            time_expr = time_col
        
        metric_expr_map = {
            "volume": "COUNT(*)",
            "count": "COUNT(*)",
            "avg_amount": "ROUND(AVG(amount), 2)",
            "total_amount": "ROUND(SUM(amount), 2)",
            "failure_rate": "ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2)"
        }
        metric_expr = metric_expr_map.get(metric.lower(), "COUNT(*)")
        
        if group_by:
            query = f"""
                SELECT {time_expr} as time_period, {group_by}, {metric_expr} as {metric}
                FROM {self.table_name}
                WHERE {where}
                GROUP BY {time_expr}, {group_by}
                ORDER BY time_period, {group_by}
            """
        else:
            query = f"""
                SELECT {time_expr} as time_period, {metric_expr} as {metric}
                FROM {self.table_name}
                WHERE {where}
                GROUP BY {time_expr}
                ORDER BY time_period
            """
        
        try:
            df = self.conn.execute(query).fetchdf()
            execution_time = (time.time() - start_time) * 1000
            
            numbers = []
            data_points = []
            
            for _, row in df.iterrows():
                time_val = str(row["time_period"])
                metric_val = float(row[metric]) if pd.notna(row[metric]) else 0
                
                label = time_val
                if group_by:
                    label = f"{time_val} ({row[group_by]})"
                
                numbers.append(NumberDetail(
                    label=label,
                    value=self._format_metric_value(metric, metric_val),
                    raw_value=metric_val
                ))
                data_points.append(ChartDataPoint(
                    x=time_val,
                    y=metric_val,
                    label=str(row[group_by]) if group_by else None
                ))
            
            chart_data = ChartData(
                type=ChartType.LINE,
                title=f"{metric.replace('_', ' ').title()} over Time",
                x_label="Date",
                y_label=metric.replace("_", " ").title(),
                data=data_points
            )
            
            return AnalysisResult(
                success=True,
                metric=metric,
                numbers=numbers[:20],  # Limit for display
                query_executed=query.strip(),
                chart_data=chart_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric=metric,
                query_executed=query.strip(),
                error=str(e)
            )
    
    def get_top_failure_codes(
        self,
        filters: Optional[PrimaryFilters] = None,
        time_window: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> AnalysisResult:
        """Get top failure codes by frequency."""
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric="failure_codes",
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        filters = filters or PrimaryFilters()
        where, _ = self._build_where_clause(filters)
        where, _ = self._apply_time_window(where, time_window)
        
        query = f"""
            SELECT 
                COALESCE(failure_code, 'Unknown') as failure_code,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM {self.table_name}
            WHERE {where} AND status = 'Failed'
            GROUP BY failure_code
            ORDER BY count DESC
            LIMIT {limit}
        """
        
        try:
            df = self.conn.execute(query).fetchdf()
            execution_time = (time.time() - start_time) * 1000
            
            numbers = []
            data_points = []
            
            for _, row in df.iterrows():
                code = row["failure_code"]
                count = int(row["count"])
                pct = float(row["percentage"])
                
                numbers.append(NumberDetail(
                    label=code,
                    value=f"{count:,} ({pct}%)",
                    raw_value=count
                ))
                data_points.append(ChartDataPoint(x=code, y=count))
            
            chart_data = ChartData(
                type=ChartType.BAR,
                title="Top Failure Codes",
                data=data_points
            )
            
            return AnalysisResult(
                success=True,
                metric="failure_codes",
                numbers=numbers,
                query_executed=query.strip(),
                chart_data=chart_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric="failure_codes",
                query_executed=query.strip(),
                error=str(e)
            )
    
    def get_executive_summary(
        self,
        time_window: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """Generate executive summary with key metrics."""
        if not self.conn:
            return AnalysisResult(
                success=False,
                metric="executive_summary",
                query_executed="N/A",
                error="Dataset not loaded"
            )
        
        start_time = time.time()
        where = "1=1"
        where, _ = self._apply_time_window(where, time_window)
        
        query = f"""
            SELECT 
                COUNT(*) as total_transactions,
                ROUND(SUM(amount), 2) as total_volume,
                ROUND(AVG(amount), 2) as avg_transaction_amount,
                ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as failure_rate,
                ROUND(100.0 * SUM(CASE WHEN fraud_flag = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4) as fraud_rate,
                ROUND(100.0 * SUM(CASE WHEN review_flag = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as review_rate
            FROM {self.table_name}
            WHERE {where}
        """
        
        try:
            result = self.conn.execute(query).fetchone()
            execution_time = (time.time() - start_time) * 1000
            
            numbers = [
                NumberDetail(
                    label="Total Transactions",
                    value=f"{result[0]:,}",
                    raw_value=result[0]
                ),
                NumberDetail(
                    label="Total Volume",
                    value=f"₹{result[1]:,.2f}",
                    raw_value=result[1]
                ),
                NumberDetail(
                    label="Average Transaction",
                    value=f"₹{result[2]:,.2f}",
                    raw_value=result[2]
                ),
                NumberDetail(
                    label="Failure Rate",
                    value=f"{result[3]}%",
                    raw_value=result[3]
                ),
                NumberDetail(
                    label="Fraud Rate",
                    value=f"{result[4]}%",
                    raw_value=result[4]
                ),
                NumberDetail(
                    label="Review Rate",
                    value=f"{result[5]}%",
                    raw_value=result[5]
                )
            ]
            
            return AnalysisResult(
                success=True,
                metric="executive_summary",
                numbers=numbers,
                query_executed=query.strip(),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                metric="executive_summary",
                query_executed=query.strip(),
                error=str(e)
            )
    
    def is_metric_computable(self, intent: IntentSchema) -> tuple[bool, str]:
        """
        Guard function to check if a metric can be computed from available data.
        
        Args:
            intent: Extracted intent from user query.
            
        Returns:
            Tuple of (can_compute, reason_if_not).
        """
        supported_metrics = {
            "failure_rate", "volume", "count", "avg_amount", 
            "avg_transaction_amount", "total_amount", "failure_codes",
            "fraud_rate", "review_rate", "executive_summary"
        }
        
        if intent.metric and intent.metric.lower() not in supported_metrics:
            return False, f"Metric '{intent.metric}' is not supported. Available metrics: {', '.join(supported_metrics)}"
        
        # Validate filters against known columns
        valid_devices = {"android", "ios", "web"}
        valid_networks = {"4g", "5g", "wifi", "3g"}
        valid_age_groups = {"<25", "25-34", "35-44", "45+"}
        valid_categories = {"food", "entertainment", "travel", "utilities", "others"}
        
        filters = intent.primary_filters
        
        if filters.device and filters.device.lower() not in valid_devices:
            return False, f"Unknown device type: {filters.device}. Valid options: {', '.join(valid_devices)}"
        
        if filters.network and filters.network.lower() not in valid_networks:
            return False, f"Unknown network type: {filters.network}. Valid options: {', '.join(valid_networks)}"
        
        return True, ""
    
    def _format_metric_value(self, metric: str, value: Union[int, float]) -> str:
        """Format a metric value for display."""
        if pd.isna(value):
            return "N/A"
        
        metric_lower = metric.lower()
        
        if "rate" in metric_lower or "percentage" in metric_lower:
            return f"{value:.2f}%"
        elif "amount" in metric_lower or "volume" in metric_lower:
            if isinstance(value, float):
                return f"₹{value:,.2f}"
            return f"₹{value:,}"
        elif "count" in metric_lower or metric_lower == "volume":
            return f"{int(value):,}"
        else:
            if isinstance(value, float):
                return f"{value:,.2f}"
            return f"{value:,}"


# Global instance (lazy loaded)
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service(data_path: str) -> AnalysisService:
    """Get or create the analysis service singleton."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService(data_path)
        _analysis_service.load_dataset()
    return _analysis_service
