"""
Database Schema for Phase 2 Risk Metrics Storage
Stores VaR calculations, correlation data, and risk alerts
"""

import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Import will be handled in main block for testing
try:
    from .var_monitor import VaRResult
    from .correlation_manager import CorrelationAlert, PositionAdjustment
except ImportError:
    # For standalone testing
    pass

logger = logging.getLogger(__name__)


class RiskMetricsDatabase:
    """Database manager for Phase 2 risk metrics"""

    def __init__(self, db_path: str = "risk_metrics.db"):
        """Initialize database connection and create tables"""
        self.db_path = db_path
        self._create_tables()
        logger.info(f"RiskMetricsDatabase initialized at {db_path}")

    def _create_tables(self):
        """Create all necessary tables for risk metrics storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # VaR calculations table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS var_calculations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        method TEXT NOT NULL,
                        currency_pair TEXT NOT NULL,
                        confidence_level REAL NOT NULL,
                        var_value REAL NOT NULL,
                        position_size REAL NOT NULL,
                        volatility REAL NOT NULL,
                        portfolio_total_var REAL,
                        breach_detected BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Correlation matrix table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS correlation_matrices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        pair1 TEXT NOT NULL,
                        pair2 TEXT NOT NULL,
                        correlation REAL NOT NULL,
                        correlation_window INTEGER NOT NULL,
                        breach_detected BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Risk alerts table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS risk_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        currency_pair TEXT,
                        pair1 TEXT,
                        pair2 TEXT,
                        metric_value REAL,
                        threshold_value REAL,
                        message TEXT NOT NULL,
                        recommendation TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Position adjustments table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS position_adjustments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        currency_pair TEXT NOT NULL,
                        current_size REAL NOT NULL,
                        recommended_size REAL NOT NULL,
                        adjustment_ratio REAL NOT NULL,
                        reason TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        applied BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Correlation trends table - NEW for Phase 2
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS correlation_trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        pair1 TEXT NOT NULL,
                        pair2 TEXT NOT NULL,
                        current_correlation REAL NOT NULL,
                        trend_slope REAL NOT NULL,
                        trend_direction TEXT NOT NULL,
                        volatility REAL NOT NULL,
                        prediction_1d REAL NOT NULL,
                        prediction_3d REAL NOT NULL,
                        breach_probability REAL NOT NULL,
                        confidence_lower REAL NOT NULL,
                        confidence_upper REAL NOT NULL,
                        r_squared REAL NOT NULL,
                        lookback_days INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Market regime table - NEW for Phase 2
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS market_regimes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        regime_type TEXT NOT NULL,
                        expected_corr_min REAL NOT NULL,
                        expected_corr_max REAL NOT NULL,
                        regime_confidence REAL NOT NULL,
                        characteristics TEXT NOT NULL, -- JSON string
                        regime_start TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Trend alerts table - NEW for Phase 2
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trend_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        pair1 TEXT,
                        pair2 TEXT,
                        metric_value REAL,
                        message TEXT NOT NULL,
                        recommendation TEXT,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Risk metrics summary table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS risk_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        portfolio_var_95 REAL,
                        max_correlation REAL,
                        avg_correlation REAL,
                        total_positions INTEGER,
                        breach_count INTEGER DEFAULT 0,
                        emergency_level INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_var_timestamp ON var_calculations(timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_var_pair ON var_calculations(currency_pair)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_corr_timestamp ON correlation_matrices(timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_corr_pairs ON correlation_matrices(pair1, pair2)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON risk_alerts(timestamp)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_alerts_type ON risk_alerts(alert_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_summary_timestamp ON risk_summary(timestamp)"
                )

                conn.commit()
                logger.info("Risk metrics database tables created successfully")

        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def store_var_calculation(
        self, var_result, portfolio_total_var: Optional[float] = None
    ) -> bool:
        """Store VaR calculation result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO var_calculations 
                    (timestamp, method, currency_pair, confidence_level, var_value, 
                     position_size, volatility, portfolio_total_var, breach_detected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        var_result.timestamp.isoformat(),
                        var_result.method,
                        var_result.currency_pair,
                        var_result.confidence_level,
                        var_result.value,
                        var_result.position_size,
                        var_result.volatility,
                        portfolio_total_var,
                        False,  # Breach detection will be updated separately
                    ),
                )

                conn.commit()
                logger.debug(
                    f"Stored VaR calculation: {var_result.method} for {var_result.currency_pair}"
                )
                return True

        except Exception as e:
            logger.error(f"Error storing VaR calculation: {e}")
            return False

    def store_correlation_data(
        self,
        pair1: str,
        pair2: str,
        correlation: float,
        timestamp: datetime,
        window: int = 60,
    ) -> bool:
        """Store correlation calculation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO correlation_matrices 
                    (timestamp, pair1, pair2, correlation, correlation_window, breach_detected)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        timestamp.isoformat(),
                        pair1,
                        pair2,
                        correlation,
                        window,
                        False,  # Breach detection will be updated separately
                    ),
                )

                conn.commit()
                logger.debug(f"Stored correlation: {pair1}-{pair2} = {correlation:.3f}")
                return True

        except Exception as e:
            logger.error(f"Error storing correlation data: {e}")
            return False

    def store_risk_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        currency_pair: Optional[str] = None,
        pair1: Optional[str] = None,
        pair2: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        recommendation: Optional[str] = None,
    ) -> bool:
        """Store risk alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO risk_alerts 
                    (timestamp, alert_type, severity, currency_pair, pair1, pair2, 
                     metric_value, threshold_value, message, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        alert_type,
                        severity,
                        currency_pair,
                        pair1,
                        pair2,
                        metric_value,
                        threshold_value,
                        message,
                        recommendation,
                    ),
                )

                conn.commit()
                logger.info(f"Stored risk alert: {alert_type} - {severity}")
                return True

        except Exception as e:
            logger.error(f"Error storing risk alert: {e}")
            return False

    def store_position_adjustment(self, adjustment) -> bool:
        """Store position adjustment recommendation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO position_adjustments 
                    (timestamp, currency_pair, current_size, recommended_size, 
                     adjustment_ratio, reason, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        adjustment.currency_pair,
                        adjustment.current_size,
                        adjustment.recommended_size,
                        adjustment.adjustment_ratio,
                        adjustment.reason,
                        adjustment.priority,
                    ),
                )

                conn.commit()
                logger.debug(
                    f"Stored position adjustment for {adjustment.currency_pair}"
                )
                return True

        except Exception as e:
            logger.error(f"Error storing position adjustment: {e}")
            return False

    def store_risk_summary(
        self,
        portfolio_var: Optional[float],
        max_correlation: Optional[float],
        avg_correlation: Optional[float],
        total_positions: int,
        breach_count: int = 0,
        emergency_level: int = 0,
    ) -> bool:
        """Store risk metrics summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO risk_summary 
                    (timestamp, portfolio_var_95, max_correlation, avg_correlation, 
                     total_positions, breach_count, emergency_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        portfolio_var,
                        max_correlation,
                        avg_correlation,
                        total_positions,
                        breach_count,
                        emergency_level,
                    ),
                )

                conn.commit()
                logger.debug("Stored risk summary")
                return True

        except Exception as e:
            logger.error(f"Error storing risk summary: {e}")
            return False

    def get_recent_var_calculations(
        self, hours: int = 24, method: Optional[str] = None
    ) -> List[Dict]:
        """Get recent VaR calculations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM var_calculations 
                    WHERE datetime(timestamp) >= datetime('now', '-{} hours')
                """.format(
                    hours
                )

                if method:
                    query += " AND method = ?"
                    cursor.execute(query + " ORDER BY timestamp DESC", (method,))
                else:
                    cursor.execute(query + " ORDER BY timestamp DESC")

                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return results

        except Exception as e:
            logger.error(f"Error retrieving VaR calculations: {e}")
            return []

    def get_recent_correlation_data(self, hours: int = 24) -> List[Dict]:
        """Get recent correlation data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM correlation_matrices 
                    WHERE datetime(timestamp) >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(
                        hours
                    )
                )

                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return results

        except Exception as e:
            logger.error(f"Error retrieving correlation data: {e}")
            return []

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """Get active (unresolved) risk alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM risk_alerts WHERE resolved = FALSE"

                if severity:
                    query += " AND severity = ?"
                    cursor.execute(query + " ORDER BY timestamp DESC", (severity,))
                else:
                    cursor.execute(query + " ORDER BY timestamp DESC")

                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return results

        except Exception as e:
            logger.error(f"Error retrieving active alerts: {e}")
            return []

    def get_risk_summary_history(self, days: int = 7) -> List[Dict]:
        """Get risk summary history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM risk_summary 
                    WHERE datetime(timestamp) >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(
                        days
                    )
                )

                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return results

        except Exception as e:
            logger.error(f"Error retrieving risk summary history: {e}")
            return []

    def mark_alert_resolved(self, alert_id: int) -> bool:
        """Mark an alert as resolved"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE risk_alerts 
                    SET resolved = TRUE 
                    WHERE id = ?
                """,
                    (alert_id,),
                )

                conn.commit()
                logger.info(f"Marked alert {alert_id} as resolved")
                return True

        except Exception as e:
            logger.error(f"Error marking alert as resolved: {e}")
            return False

    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """Clean up old data to manage database size"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Clean up old VaR calculations
                cursor.execute(
                    """
                    DELETE FROM var_calculations 
                    WHERE datetime(timestamp) < datetime('now', '-{} days')
                """.format(
                        days_to_keep
                    )
                )

                # Clean up old correlation data
                cursor.execute(
                    """
                    DELETE FROM correlation_matrices 
                    WHERE datetime(timestamp) < datetime('now', '-{} days')
                """.format(
                        days_to_keep
                    )
                )

                # Clean up resolved old alerts
                cursor.execute(
                    """
                    DELETE FROM risk_alerts 
                    WHERE resolved = TRUE 
                    AND datetime(timestamp) < datetime('now', '-{} days')
                """.format(
                        days_to_keep
                    )
                )

                # Clean up old summaries (keep more history)
                cursor.execute(
                    """
                    DELETE FROM risk_summary 
                    WHERE datetime(timestamp) < datetime('now', '-{} days')
                """.format(
                        days_to_keep * 3
                    )
                )

                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Count records in each table
                tables = [
                    "var_calculations",
                    "correlation_matrices",
                    "risk_alerts",
                    "position_adjustments",
                    "risk_summary",
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = count

                # Get active alerts count
                cursor.execute(
                    "SELECT COUNT(*) FROM risk_alerts WHERE resolved = FALSE"
                )
                stats["active_alerts"] = cursor.fetchone()[0]

                return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    # Test database functionality
    db = RiskMetricsDatabase("test_risk_metrics.db")

    # Create a simple test VaR result
    class TestVaRResult:
        def __init__(self):
            self.method = "historical"
            self.value = 150.25
            self.confidence_level = 0.95
            self.timestamp = datetime.now()
            self.currency_pair = "EUR_USD"
            self.position_size = 1000.0
            self.volatility = 0.012

    # Test storing VaR calculation
    var_result = TestVaRResult()
    success = db.store_var_calculation(var_result, portfolio_total_var=500.0)
    print(f"VaR storage success: {success}")

    # Test storing correlation
    success = db.store_correlation_data("EUR_USD", "GBP_USD", 0.65, datetime.now())
    print(f"Correlation storage success: {success}")

    # Test storing alert
    success = db.store_risk_alert(
        alert_type="VAR_BREACH",
        severity="HIGH",
        message="VaR exceeded target threshold",
        currency_pair="EUR_USD",
        metric_value=0.0045,
        threshold_value=0.0031,
        recommendation="Reduce position size",
    )
    print(f"Alert storage success: {success}")

    # Get recent data
    recent_var = db.get_recent_var_calculations(hours=1)
    print(f"Recent VaR calculations: {len(recent_var)}")

    # Get stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")

    print("Database testing completed successfully!")
