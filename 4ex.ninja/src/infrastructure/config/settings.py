"""
Application Settings and Configuration Models
Defines configuration data structures with validation.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field
import os


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    host: str = "localhost"
    port: int = 27017
    name: str = "trading_db"
    username: Optional[str] = None
    password: Optional[str] = None

    # Connection settings
    max_pool_size: int = 100
    min_pool_size: int = 10
    max_idle_time_ms: int = 30000
    connect_timeout_ms: int = 10000
    server_selection_timeout_ms: int = 30000
    socket_timeout_ms: int = 5000

    # Retry settings
    retry_writes: bool = True
    retry_reads: bool = True

    # TLS/SSL settings
    tls_enabled: bool = False
    tls_ca_file: Optional[str] = None
    tls_cert_file: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")

        if self.max_pool_size < 1:
            raise ValueError("Max pool size must be at least 1")

    def get_connection_string(self) -> str:
        """Get MongoDB connection string."""
        auth_part = ""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"

        tls_part = ""
        if self.tls_enabled:
            tls_part = "?tls=true"
            if self.tls_ca_file:
                tls_part += f"&tlsCAFile={self.tls_ca_file}"

        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.name}{tls_part}"


@dataclass
class TradingConfig:
    """Trading configuration settings."""

    # Risk management
    max_position_size: Decimal = field(default_factory=lambda: Decimal("1000"))
    max_daily_loss: Decimal = field(default_factory=lambda: Decimal("500"))
    risk_per_trade: Decimal = field(default_factory=lambda: Decimal("0.02"))

    # Trading pairs
    enabled_pairs: List[str] = field(
        default_factory=lambda: ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]
    )

    # Timeframes
    default_timeframe: str = "H1"
    supported_timeframes: List[str] = field(
        default_factory=lambda: ["M5", "M15", "M30", "H1", "H4", "D"]
    )

    # Strategy settings
    max_concurrent_signals: int = 10
    signal_timeout_hours: int = 24

    # Performance tracking
    performance_calculation_interval: int = 300

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not Decimal("0") < self.risk_per_trade <= Decimal("0.1"):
            raise ValueError("Risk per trade must be between 0 and 0.1 (10%)")

        valid_pairs = [
            "EUR_USD",
            "GBP_USD",
            "USD_JPY",
            "AUD_USD",
            "USD_CAD",
            "USD_CHF",
            "NZD_USD",
            "EUR_GBP",
            "EUR_JPY",
            "GBP_JPY",
        ]
        for pair in self.enabled_pairs:
            if pair not in valid_pairs:
                raise ValueError(f"Invalid trading pair: {pair}")


@dataclass
class AppConfig:
    """Main application configuration."""

    # Application info
    app_name: str = "4ex.ninja"
    version: str = "1.0.0"
    debug: bool = False

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Security
    secret_key: str = "dev-secret-key"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None

    # External services
    oanda_api_url: str = "https://api-fxtrade.oanda.com"
    oanda_stream_url: str = "https://stream-fxtrade.oanda.com"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 1024 <= self.api_port <= 65535:
            raise ValueError("API port must be between 1024 and 65535")

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")

        self.log_level = self.log_level.upper()


@dataclass
class OandaConfig:
    """OANDA API configuration."""

    api_key: str = ""
    account_id: str = ""
    api_url: str = "https://api-fxtrade.oanda.com"
    stream_url: str = "https://stream-fxtrade.oanda.com"

    # Request settings
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1

    # Rate limiting
    requests_per_second: int = 100

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.api_key and len(self.api_key) < 10:
            raise ValueError("OANDA API key must be at least 10 characters")

        if self.account_id and not self.account_id.isdigit():
            raise ValueError("OANDA account ID must be numeric")


@dataclass
class Settings:
    """Main settings container."""

    app: AppConfig
    database: DatabaseConfig
    trading: TradingConfig
    oanda: OandaConfig

    @classmethod
    def from_environment(cls) -> "Settings":
        """
        Create settings from environment variables.

        Returns:
            Settings instance
        """
        # Load from environment with prefixes
        app_config = AppConfig(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
        )

        database_config = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "27017")),
            name=os.getenv("DB_NAME", "trading_db"),
            username=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
        )

        trading_config = TradingConfig(
            max_position_size=Decimal(os.getenv("MAX_POSITION_SIZE", "1000")),
            max_daily_loss=Decimal(os.getenv("MAX_DAILY_LOSS", "500")),
            risk_per_trade=Decimal(os.getenv("RISK_PER_TRADE", "0.02")),
        )

        oanda_config = OandaConfig(
            api_key=os.getenv("OANDA_API_KEY", ""),
            account_id=os.getenv("OANDA_ACCOUNT_ID", ""),
            api_url=os.getenv("OANDA_API_URL", "https://api-fxtrade.oanda.com"),
            stream_url=os.getenv(
                "OANDA_STREAM_URL", "https://stream-fxtrade.oanda.com"
            ),
        )

        return cls(
            app=app_config,
            database=database_config,
            trading=trading_config,
            oanda=oanda_config,
        )

    @classmethod
    def create_default(cls) -> "Settings":
        """
        Create settings with default values.

        Returns:
            Settings instance with defaults
        """
        return cls(
            app=AppConfig(),
            database=DatabaseConfig(),
            trading=TradingConfig(),
            oanda=OandaConfig(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary.

        Returns:
            Settings as dictionary
        """
        import dataclasses

        return {
            "app": dataclasses.asdict(self.app),
            "database": dataclasses.asdict(self.database),
            "trading": dataclasses.asdict(self.trading),
            "oanda": dataclasses.asdict(self.oanda),
        }

    def validate_production_settings(self) -> List[str]:
        """
        Validate settings for production environment.

        Returns:
            List of validation errors
        """
        errors = []

        # Check required production settings
        if self.app.secret_key == "dev-secret-key":
            errors.append("Production requires a secure secret key")

        if not self.oanda.api_key:
            errors.append("OANDA API key is required")

        if not self.oanda.account_id:
            errors.append("OANDA account ID is required")

        if self.app.debug:
            errors.append("Debug mode should be disabled in production")

        # Check database security
        if self.database.username is None:
            errors.append("Database username should be set in production")

        if self.database.password is None:
            errors.append("Database password should be set in production")

        return errors
