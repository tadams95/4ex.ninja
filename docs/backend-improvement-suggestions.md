# 4ex.ninja Backend Improvement Checklist - LLM Optimized

## 📋 Project Overview
**Goal:** Transform the 4ex.ninja backend from a collection of scripts into a production-ready, scalable, and maintainable trading system architecture.

### Current State Analysis
**✅ Strengths:**
- OANDA API integration with oandapyV20
- MongoDB data storage infrastructure
- MA crossover strategy implementations
- Real-time price streaming capability
- ATR-based risk management calculations
- Signal generation and storage system

**⚠️ Critical Issues:**
- 16+ duplicated strategy files with copy-paste code
- No proper architecture (missing service layer, repository pattern)
- Direct database access from strategies (no abstraction)
- Poor error handling without recovery mechanisms
- No API layer for external access
- Minimal test coverage (placeholder tests only)
- Basic logging without structured monitoring
- Security vulnerabilities (exposed credentials)
- No data validation or schema enforcement
- Inconsistent database design across multiple DBs
- No caching layer for repeated queries
- Missing authentication and authorization
- No CI/CD pipeline or deployment automation

---

## 🏗️ PHASE 1: ARCHITECTURAL FOUNDATION (Weeks 1-3)

### 1.1 Project Structure Setup (Day 1)

#### Task 1.1.1: Create Clean Architecture Directory Structure
- [ ] **Navigate to project root and create new directory structure**
  ```bash
  cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja
  mkdir -p src/{api,core,infrastructure,application}
  mkdir -p src/core/{entities,use_cases,interfaces}
  mkdir -p src/infrastructure/{database,external_apis,messaging,cache}
  mkdir -p src/application/{services,dto}
  mkdir -p tests/{unit,integration,e2e}
  mkdir -p config
  ```
  **Verification:** Run `tree src/` to confirm directory structure

#### Task 1.1.2: Move Existing Files to New Structure
- [ ] **Move configuration files**
  ```bash
  mv config/settings.py src/core/config.py
  mv api/oanda_api.py src/infrastructure/external_apis/
  mv models/market_data.py src/infrastructure/database/
  ```
  **Verification:** Confirm files exist in new locations

#### Task 1.1.3: Create __init__.py Files for Python Packages
- [ ] **Create empty __init__.py files in all directories**
  ```bash
  find src/ -type d -exec touch {}/__init__.py \;
  find tests/ -type d -exec touch {}/__init__.py \;
  ```
  **Verification:** Check that each directory has __init__.py

### 1.2 Core Entities Definition (Day 2)

#### Task 1.2.1: Create Signal Entity
- [ ] **Create src/core/entities/signal.py**
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from decimal import Decimal
  from enum import Enum
  from typing import Optional

  class SignalType(Enum):
      BUY = "BUY"
      SELL = "SELL"

  class Timeframe(Enum):
      H1 = "H1"
      H4 = "H4"
      D = "D"

  @dataclass
  class TradingSignal:
      id: Optional[str]
      instrument: str
      timeframe: Timeframe
      signal_type: SignalType
      entry_price: Decimal
      stop_loss: Decimal
      take_profit: Decimal
      timestamp: datetime
      risk_reward_ratio: Decimal
      atr: Decimal
      fast_ma: Optional[Decimal] = None
      slow_ma: Optional[Decimal] = None
      created_at: Optional[datetime] = None
      
      def __post_init__(self):
          if self.created_at is None:
              self.created_at = datetime.utcnow()
  ```
  **Verification:** Import the class in Python REPL to check syntax

#### Task 1.2.2: Create Market Data Entity
- [ ] **Create src/core/entities/market_data.py**
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from decimal import Decimal
  from typing import Dict, Any

  @dataclass
  class Candle:
      instrument: str
      timeframe: str
      time: datetime
      open_price: Decimal
      high_price: Decimal
      low_price: Decimal
      close_price: Decimal
      volume: int
      complete: bool = True
      
      @classmethod
      def from_oanda_response(cls, instrument: str, timeframe: str, candle_data: Dict[str, Any]) -> 'Candle':
          return cls(
              instrument=instrument,
              timeframe=timeframe,
              time=datetime.fromisoformat(candle_data['time'].replace('Z', '+00:00')),
              open_price=Decimal(candle_data['mid']['o']),
              high_price=Decimal(candle_data['mid']['h']),
              low_price=Decimal(candle_data['mid']['l']),
              close_price=Decimal(candle_data['mid']['c']),
              volume=int(candle_data['volume']),
              complete=candle_data['complete']
          )
  ```
  **Verification:** Test the from_oanda_response method with sample data

#### Task 1.2.3: Create Strategy Configuration Entity
- [ ] **Create src/core/entities/strategy.py**
  ```python
  from dataclasses import dataclass
  from typing import Dict, Any
  from decimal import Decimal

  @dataclass
  class StrategyConfig:
      name: str
      instrument: str
      timeframe: str
      fast_ma_period: int
      slow_ma_period: int
      atr_period: int = 14
      sl_atr_multiplier: Decimal = Decimal('2.0')
      tp_atr_multiplier: Decimal = Decimal('3.0')
      min_atr_value: Decimal = Decimal('0.0001')
      min_rr_ratio: Decimal = Decimal('1.5')
      parameters: Dict[str, Any] = None
      
      def __post_init__(self):
          if self.parameters is None:
              self.parameters = {}
  ```
  **Verification:** Create a StrategyConfig instance and check all fields

### 1.3 Repository Interfaces (Day 3)

#### Task 1.3.1: Create Base Repository Interface
- [ ] **Create src/core/interfaces/repositories.py**
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  from src.core.entities.signal import TradingSignal
  from src.core.entities.market_data import Candle

  class BaseRepository(ABC):
      @abstractmethod
      async def health_check(self) -> bool:
          pass

  class SignalRepository(BaseRepository):
      @abstractmethod
      async def save(self, signal: TradingSignal) -> str:
          """Save a trading signal and return its ID"""
          pass
      
      @abstractmethod
      async def get_by_id(self, signal_id: str) -> Optional[TradingSignal]:
          """Get signal by ID"""
          pass
      
      @abstractmethod
      async def get_latest(self, limit: int = 20, instrument: Optional[str] = None) -> List[TradingSignal]:
          """Get latest signals with optional instrument filter"""
          pass
      
      @abstractmethod
      async def get_by_timeframe(self, timeframe: str, limit: int = 20) -> List[TradingSignal]:
          """Get signals by timeframe"""
          pass

  class MarketDataRepository(BaseRepository):
      @abstractmethod
      async def save_candle(self, candle: Candle) -> str:
          """Save a market data candle"""
          pass
      
      @abstractmethod
      async def get_latest_candles(self, instrument: str, timeframe: str, count: int = 200) -> List[Candle]:
          """Get latest candles for analysis"""
          pass
      
      @abstractmethod
      async def get_candles_range(self, instrument: str, timeframe: str, start_time: str, end_time: str) -> List[Candle]:
          """Get candles within time range"""
          pass
  ```
  **Verification:** Check imports and ABC inheritance

#### Task 1.3.2: Create External API Interface
- [ ] **Create src/core/interfaces/external_apis.py**
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  from src.core.entities.market_data import Candle

  class MarketDataProvider(ABC):
      @abstractmethod
      async def get_candles(self, instrument: str, granularity: str, count: Optional[int] = None, 
                          start: Optional[str] = None, end: Optional[str] = None) -> List[Candle]:
          """Fetch market data candles"""
          pass
      
      @abstractmethod
      async def get_current_price(self, instrument: str) -> Dict[str, Any]:
          """Get current price for instrument"""
          pass
      
      @abstractmethod
      async def get_account_summary(self) -> Dict[str, Any]:
          """Get account information"""
          pass
      
      @abstractmethod
      async def health_check(self) -> bool:
          """Check if API is accessible"""
          pass
  ```
  **Verification:** Import and check interface definition

### 1.4 Configuration Management (Day 4)

#### Task 1.4.1: Install Required Dependencies
- [ ] **Install new dependencies**
  ```bash
  cd /Users/tyrelle/Desktop/4ex.ninja/4ex.ninja
  pip install pydantic[dotenv] fastapi uvicorn motor
  pip freeze > requirements.txt
  ```
  **Verification:** Check that packages are installed with `pip list`

#### Task 1.4.2: Create Environment Configuration
- [ ] **Create src/core/config.py**
  ```python
  from pydantic import BaseSettings, validator
  from typing import Optional
  import os

  class Settings(BaseSettings):
      # API Configuration
      oanda_api_key: str
      oanda_account_id: str
      oanda_environment: str = "practice"
      
      # Database Configuration
      mongodb_uri: str
      database_name: str = "forex_trading"
      
      # Application Configuration
      environment: str = "development"
      debug: bool = True
      log_level: str = "INFO"
      
      # API Settings
      api_host: str = "0.0.0.0"
      api_port: int = 8000
      api_prefix: str = "/api/v1"
      
      # Security
      api_key_header: str = "X-API-Key"
      allowed_origins: list = ["http://localhost:3000", "https://4ex.ninja"]
      
      @validator('environment')
      def validate_environment(cls, v):
          if v not in ['development', 'staging', 'production']:
              raise ValueError('Environment must be development, staging, or production')
          return v
      
      @validator('oanda_environment')
      def validate_oanda_env(cls, v):
          if v not in ['practice', 'live']:
              raise ValueError('OANDA environment must be practice or live')
          return v
      
      class Config:
          env_file = ".env"
          case_sensitive = False

  # Global settings instance
  settings = Settings()
  ```
  **Verification:** Load settings and check all values are populated

#### Task 1.4.3: Update Environment Variables
- [ ] **Create .env file with required variables**
  ```bash
  cat > .env << EOF
  OANDA_API_KEY=your_api_key_here
  OANDA_ACCOUNT_ID=your_account_id_here
  OANDA_ENVIRONMENT=practice
  MONGODB_URI=your_mongodb_connection_string
  DATABASE_NAME=forex_trading
  ENVIRONMENT=development
  DEBUG=true
  LOG_LEVEL=INFO
  API_HOST=0.0.0.0
  API_PORT=8000
  API_PREFIX=/api/v1
  EOF
  ```
  **Verification:** Source .env and check variables are loaded

### 1.5 Database Implementation (Day 5)

#### Task 1.5.1: Create MongoDB Connection Manager
- [ ] **Create src/infrastructure/database/connection.py**
  ```python
  from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
  from typing import Optional
  import logging
  from src.core.config import settings

  logger = logging.getLogger(__name__)

  class DatabaseManager:
      def __init__(self):
          self._client: Optional[AsyncIOMotorClient] = None
          self._database: Optional[AsyncIOMotorDatabase] = None
      
      async def connect(self) -> None:
          """Create database connection"""
          try:
              self._client = AsyncIOMotorClient(
                  settings.mongodb_uri,
                  maxPoolSize=50,
                  minPoolSize=10,
                  maxIdleTimeMS=30000,
                  socketTimeoutMS=20000,
                  connectTimeoutMS=20000,
                  serverSelectionTimeoutMS=20000
              )
              self._database = self._client[settings.database_name]
              
              # Test connection
              await self._client.admin.command('ping')
              logger.info("Successfully connected to MongoDB")
              
          except Exception as e:
              logger.error(f"Failed to connect to MongoDB: {e}")
              raise
      
      async def disconnect(self) -> None:
          """Close database connection"""
          if self._client:
              self._client.close()
              logger.info("Disconnected from MongoDB")
      
      @property
      def database(self) -> AsyncIOMotorDatabase:
          if self._database is None:
              raise RuntimeError("Database not connected")
          return self._database
      
      async def health_check(self) -> bool:
          """Check database health"""
          try:
              await self._client.admin.command('ping')
              return True
          except Exception:
              return False

  # Global database manager instance
  db_manager = DatabaseManager()
  ```
  **Verification:** Test connection with actual MongoDB URI

#### Task 1.5.2: Implement Signal Repository
- [ ] **Create src/infrastructure/database/signal_repository.py**
  ```python
  from typing import List, Optional
  from bson import ObjectId
  from datetime import datetime
  import logging
  from src.core.interfaces.repositories import SignalRepository
  from src.core.entities.signal import TradingSignal, SignalType, Timeframe
  from src.infrastructure.database.connection import db_manager
  from decimal import Decimal

  logger = logging.getLogger(__name__)

  class MongoSignalRepository(SignalRepository):
      def __init__(self):
          self.collection_name = "trading_signals"
      
      @property
      def collection(self):
          return db_manager.database[self.collection_name]
      
      async def save(self, signal: TradingSignal) -> str:
          """Save trading signal to MongoDB"""
          try:
              signal_dict = {
                  "instrument": signal.instrument,
                  "timeframe": signal.timeframe.value,
                  "signal_type": signal.signal_type.value,
                  "entry_price": float(signal.entry_price),
                  "stop_loss": float(signal.stop_loss),
                  "take_profit": float(signal.take_profit),
                  "timestamp": signal.timestamp,
                  "risk_reward_ratio": float(signal.risk_reward_ratio),
                  "atr": float(signal.atr),
                  "fast_ma": float(signal.fast_ma) if signal.fast_ma else None,
                  "slow_ma": float(signal.slow_ma) if signal.slow_ma else None,
                  "created_at": signal.created_at or datetime.utcnow()
              }
              
              result = await self.collection.insert_one(signal_dict)
              logger.info(f"Saved signal {result.inserted_id} for {signal.instrument}")
              return str(result.inserted_id)
              
          except Exception as e:
              logger.error(f"Failed to save signal: {e}")
              raise
      
      async def get_by_id(self, signal_id: str) -> Optional[TradingSignal]:
          """Get signal by ID"""
          try:
              doc = await self.collection.find_one({"_id": ObjectId(signal_id)})
              return self._document_to_signal(doc) if doc else None
          except Exception as e:
              logger.error(f"Failed to get signal {signal_id}: {e}")
              return None
      
      async def get_latest(self, limit: int = 20, instrument: Optional[str] = None) -> List[TradingSignal]:
          """Get latest signals"""
          try:
              query = {"instrument": instrument} if instrument else {}
              cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
              documents = await cursor.to_list(length=limit)
              return [self._document_to_signal(doc) for doc in documents]
          except Exception as e:
              logger.error(f"Failed to get latest signals: {e}")
              return []
      
      async def get_by_timeframe(self, timeframe: str, limit: int = 20) -> List[TradingSignal]:
          """Get signals by timeframe"""
          try:
              cursor = self.collection.find({"timeframe": timeframe}).sort("timestamp", -1).limit(limit)
              documents = await cursor.to_list(length=limit)
              return [self._document_to_signal(doc) for doc in documents]
          except Exception as e:
              logger.error(f"Failed to get signals for timeframe {timeframe}: {e}")
              return []
      
      async def health_check(self) -> bool:
          """Check repository health"""
          try:
              await self.collection.find_one()
              return True
          except Exception:
              return False
      
      def _document_to_signal(self, doc: dict) -> TradingSignal:
          """Convert MongoDB document to TradingSignal entity"""
          return TradingSignal(
              id=str(doc["_id"]),
              instrument=doc["instrument"],
              timeframe=Timeframe(doc["timeframe"]),
              signal_type=SignalType(doc["signal_type"]),
              entry_price=Decimal(str(doc["entry_price"])),
              stop_loss=Decimal(str(doc["stop_loss"])),
              take_profit=Decimal(str(doc["take_profit"])),
              timestamp=doc["timestamp"],
              risk_reward_ratio=Decimal(str(doc["risk_reward_ratio"])),
              atr=Decimal(str(doc["atr"])),
              fast_ma=Decimal(str(doc["fast_ma"])) if doc.get("fast_ma") else None,
              slow_ma=Decimal(str(doc["slow_ma"])) if doc.get("slow_ma") else None,
              created_at=doc.get("created_at")
          )
  ```
  **Verification:** Test save and retrieve operations

### 1.6 Dependency Injection Setup (Day 6)

#### Task 1.6.1: Create Dependency Container
- [ ] **Create src/core/dependencies.py**
  ```python
  from functools import lru_cache
  from src.core.interfaces.repositories import SignalRepository, MarketDataRepository
  from src.infrastructure.database.signal_repository import MongoSignalRepository
  from src.infrastructure.database.market_data_repository import MongoMarketDataRepository

  class Container:
      def __init__(self):
          self._signal_repository: Optional[SignalRepository] = None
          self._market_data_repository: Optional[MarketDataRepository] = None
      
      @property
      def signal_repository(self) -> SignalRepository:
          if self._signal_repository is None:
              self._signal_repository = MongoSignalRepository()
          return self._signal_repository
      
      @property
      def market_data_repository(self) -> MarketDataRepository:
          if self._market_data_repository is None:
              self._market_data_repository = MongoMarketDataRepository()
          return self._market_data_repository

  # Global container instance
  container = Container()

  # FastAPI dependency functions
  def get_signal_repository() -> SignalRepository:
      return container.signal_repository

  def get_market_data_repository() -> MarketDataRepository:
      return container.market_data_repository
  ```
  **Verification:** Import and test dependency resolution

### 1.7 Basic FastAPI Setup (Day 7)

#### Task 1.7.1: Create FastAPI Application
- [ ] **Create src/api/main.py**
  ```python
  from fastapi import FastAPI, Depends
  from fastapi.middleware.cors import CORSMiddleware
  import logging
  from src.core.config import settings
  from src.infrastructure.database.connection import db_manager

  # Setup logging
  logging.basicConfig(level=getattr(logging, settings.log_level))
  logger = logging.getLogger(__name__)

  app = FastAPI(
      title="4ex.ninja Trading API",
      description="Forex trading signals and market data API",
      version="1.0.0",
      debug=settings.debug
  )

  # CORS middleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.allowed_origins,
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE"],
      allow_headers=["*"],
  )

  @app.on_event("startup")
  async def startup_event():
      """Initialize database connection on startup"""
      await db_manager.connect()
      logger.info("Application started successfully")

  @app.on_event("shutdown")
  async def shutdown_event():
      """Clean up database connection on shutdown"""
      await db_manager.disconnect()
      logger.info("Application shutdown complete")

  @app.get("/health")
  async def health_check():
      """Basic health check endpoint"""
      db_healthy = await db_manager.health_check()
      return {
          "status": "healthy" if db_healthy else "unhealthy",
          "database": "connected" if db_healthy else "disconnected"
      }

  if __name__ == "__main__":
      import uvicorn
      uvicorn.run(app, host=settings.api_host, port=settings.api_port)
  ```
  **Verification:** Run `python src/api/main.py` and check http://localhost:8000/health

#### Task 1.7.2: Create API Router Structure
- [ ] **Create src/api/routes/__init__.py**
  ```python
  from fastapi import APIRouter
  from . import signals, health

  api_router = APIRouter()

  api_router.include_router(health.router, prefix="/health", tags=["health"])
  api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
  ```

- [ ] **Create src/api/routes/health.py**
  ```python
  from fastapi import APIRouter, Depends
  from src.core.dependencies import get_signal_repository
  from src.core.interfaces.repositories import SignalRepository

  router = APIRouter()

  @router.get("/")
  async def health_check():
      return {"status": "healthy", "service": "4ex.ninja API"}

  @router.get("/detailed")
  async def detailed_health_check(
      signal_repo: SignalRepository = Depends(get_signal_repository)
  ):
      db_healthy = await signal_repo.health_check()
      return {
          "status": "healthy" if db_healthy else "degraded",
          "database": "connected" if db_healthy else "disconnected",
          "timestamp": "2025-01-01T00:00:00Z"
      }
  ```

- [ ] **Create src/api/routes/signals.py**
  ```python
  from fastapi import APIRouter, Depends, HTTPException, Query
  from typing import List, Optional
  from src.core.dependencies import get_signal_repository
  from src.core.interfaces.repositories import SignalRepository
  from src.api.schemas.signal_schemas import SignalResponse

  router = APIRouter()

  @router.get("/", response_model=List[SignalResponse])
  async def get_signals(
      limit: int = Query(20, ge=1, le=100),
      instrument: Optional[str] = Query(None),
      signal_repo: SignalRepository = Depends(get_signal_repository)
  ):
      """Get latest trading signals"""
      try:
          signals = await signal_repo.get_latest(limit=limit, instrument=instrument)
          return [SignalResponse.from_entity(signal) for signal in signals]
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

  @router.get("/{signal_id}", response_model=SignalResponse)
  async def get_signal(
      signal_id: str,
      signal_repo: SignalRepository = Depends(get_signal_repository)
  ):
      """Get specific signal by ID"""
      signal = await signal_repo.get_by_id(signal_id)
      if not signal:
          raise HTTPException(status_code=404, detail="Signal not found")
      return SignalResponse.from_entity(signal)
  ```
  **Verification:** Test endpoints with curl or browser

---

## 🔄 PHASE 2: API LAYER & SERVICES (Weeks 4-6)

### 2.1 API Schema Definitions (Day 8)

#### Task 2.1.1: Create Pydantic Response Models
- [ ] **Create src/api/schemas/signal_schemas.py**
  ```python
  from pydantic import BaseModel, validator
  from typing import Optional
  from datetime import datetime
  from decimal import Decimal
  from src.core.entities.signal import TradingSignal

  class SignalResponse(BaseModel):
      id: str
      instrument: str
      timeframe: str
      signal_type: str
      entry_price: float
      stop_loss: float
      take_profit: float
      timestamp: datetime
      risk_reward_ratio: float
      atr: float
      fast_ma: Optional[float] = None
      slow_ma: Optional[float] = None
      created_at: datetime
      
      @classmethod
      def from_entity(cls, signal: TradingSignal) -> 'SignalResponse':
          return cls(
              id=signal.id,
              instrument=signal.instrument,
              timeframe=signal.timeframe.value,
              signal_type=signal.signal_type.value,
              entry_price=float(signal.entry_price),
              stop_loss=float(signal.stop_loss),
              take_profit=float(signal.take_profit),
              timestamp=signal.timestamp,
              risk_reward_ratio=float(signal.risk_reward_ratio),
              atr=float(signal.atr),
              fast_ma=float(signal.fast_ma) if signal.fast_ma else None,
              slow_ma=float(signal.slow_ma) if signal.slow_ma else None,
              created_at=signal.created_at
          )

  class SignalCreateRequest(BaseModel):
      instrument: str
      timeframe: str
      signal_type: str
      entry_price: float
      stop_loss: float
      take_profit: float
      atr: float
      fast_ma: Optional[float] = None
      slow_ma: Optional[float] = None
      
      @validator('signal_type')
      def validate_signal_type(cls, v):
          if v not in ['BUY', 'SELL']:
              raise ValueError('Signal type must be BUY or SELL')
          return v
      
      @validator('timeframe')
      def validate_timeframe(cls, v):
          if v not in ['H1', 'H4', 'D']:
              raise ValueError('Timeframe must be H1, H4, or D')
          return v

  class ErrorResponse(BaseModel):
      error: str
      detail: str
      timestamp: datetime = datetime.utcnow()
  ```
  **Verification:** Import schemas and test validation

#### Task 2.1.2: Create Market Data Schemas
- [ ] **Create src/api/schemas/market_data_schemas.py**
  ```python
  from pydantic import BaseModel
  from typing import List
  from datetime import datetime
  from decimal import Decimal

  class CandleResponse(BaseModel):
      instrument: str
      timeframe: str
      time: datetime
      open_price: float
      high_price: float
      low_price: float
      close_price: float
      volume: int
      complete: bool

  class MarketDataRequest(BaseModel):
      instrument: str
      timeframe: str
      count: int = 200
      
  class MarketDataResponse(BaseModel):
      instrument: str
      timeframe: str
      candles: List[CandleResponse]
      total_count: int
  ```
  **Verification:** Test schema creation and serialization

### 2.2 Service Layer Implementation (Days 9-10)

#### Task 2.2.1: Create Signal Service
- [ ] **Create src/application/services/signal_service.py**
  ```python
  from typing import List, Optional
  from datetime import datetime
  import logging
  from src.core.entities.signal import TradingSignal, SignalType, Timeframe
  from src.core.interfaces.repositories import SignalRepository, MarketDataRepository
  from src.application.dto.signal_dto import CreateSignalDTO

  logger = logging.getLogger(__name__)

  class SignalService:
      def __init__(self, signal_repo: SignalRepository, market_data_repo: MarketDataRepository):
          self.signal_repo = signal_repo
          self.market_data_repo = market_data_repo
      
      async def create_signal(self, signal_data: CreateSignalDTO) -> TradingSignal:
          """Create a new trading signal"""
          try:
              signal = TradingSignal(
                  id=None,
                  instrument=signal_data.instrument,
                  timeframe=Timeframe(signal_data.timeframe),
                  signal_type=SignalType(signal_data.signal_type),
                  entry_price=signal_data.entry_price,
                  stop_loss=signal_data.stop_loss,
                  take_profit=signal_data.take_profit,
                  timestamp=datetime.utcnow(),
                  risk_reward_ratio=signal_data.risk_reward_ratio,
                  atr=signal_data.atr,
                  fast_ma=signal_data.fast_ma,
                  slow_ma=signal_data.slow_ma
              )
              
              signal_id = await self.signal_repo.save(signal)
              signal.id = signal_id
              
              logger.info(f"Created signal {signal_id} for {signal.instrument}")
              return signal
              
          except Exception as e:
              logger.error(f"Failed to create signal: {e}")
              raise
      
      async def get_latest_signals(self, limit: int = 20, instrument: Optional[str] = None) -> List[TradingSignal]:
          """Get latest trading signals"""
          return await self.signal_repo.get_latest(limit=limit, instrument=instrument)
      
      async def get_signal_by_id(self, signal_id: str) -> Optional[TradingSignal]:
          """Get specific signal by ID"""
          return await self.signal_repo.get_by_id(signal_id)
      
      async def get_signals_by_timeframe(self, timeframe: str, limit: int = 20) -> List[TradingSignal]:
          """Get signals filtered by timeframe"""
          return await self.signal_repo.get_by_timeframe(timeframe, limit)
  ```
  **Verification:** Test service methods with mock repositories

#### Task 2.2.2: Create DTO Classes
- [ ] **Create src/application/dto/signal_dto.py**
  ```python
  from dataclasses import dataclass
  from typing import Optional
  from decimal import Decimal

  @dataclass
  class CreateSignalDTO:
      instrument: str
      timeframe: str
      signal_type: str
      entry_price: Decimal
      stop_loss: Decimal
      take_profit: Decimal
      atr: Decimal
      risk_reward_ratio: Decimal
      fast_ma: Optional[Decimal] = None
      slow_ma: Optional[Decimal] = None
  ```

#### Task 2.2.3: Create Market Data Service
- [ ] **Create src/application/services/market_data_service.py**
  ```python
  from typing import List
  import logging
  from src.core.entities.market_data import Candle
  from src.core.interfaces.repositories import MarketDataRepository
  from src.core.interfaces.external_apis import MarketDataProvider

  logger = logging.getLogger(__name__)

  class MarketDataService:
      def __init__(self, market_data_repo: MarketDataRepository, data_provider: MarketDataProvider):
          self.market_data_repo = market_data_repo
          self.data_provider = data_provider
      
      async def get_latest_candles(self, instrument: str, timeframe: str, count: int = 200) -> List[Candle]:
          """Get latest candles from repository"""
          try:
              return await self.market_data_repo.get_latest_candles(instrument, timeframe, count)
          except Exception as e:
              logger.error(f"Failed to get candles for {instrument}: {e}")
              raise
      
      async def fetch_and_store_candles(self, instrument: str, timeframe: str, count: int = 200) -> int:
          """Fetch candles from external API and store in repository"""
          try:
              candles = await self.data_provider.get_candles(instrument, timeframe, count)
              stored_count = 0
              
              for candle in candles:
                  await self.market_data_repo.save_candle(candle)
                  stored_count += 1
              
              logger.info(f"Stored {stored_count} candles for {instrument}_{timeframe}")
              return stored_count
              
          except Exception as e:
              logger.error(f"Failed to fetch and store candles: {e}")
              raise
  ```
  **Verification:** Test service with mock dependencies

### 2.3 API Authentication (Day 11)

#### Task 2.3.1: Create Authentication Middleware
- [ ] **Create src/api/middleware/auth.py**
  ```python
  from fastapi import HTTPException, status, Depends, Header
  from typing import Optional
  import hashlib
  import hmac
  from src.core.config import settings

  class APIKeyAuth:
      def __init__(self):
          # In production, these should be stored in database
          self.valid_api_keys = {
              "dev-key-123": {"name": "Development", "permissions": ["read", "write"]},
              "frontend-key": {"name": "Frontend", "permissions": ["read"]}
          }
      
      async def __call__(self, x_api_key: Optional[str] = Header(None, alias=settings.api_key_header)):
          if not x_api_key:
              raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="API key header missing",
                  headers={"WWW-Authenticate": "API-Key"},
              )
          
          if x_api_key not in self.valid_api_keys:
              raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid API key",
                  headers={"WWW-Authenticate": "API-Key"},
              )
          
          return self.valid_api_keys[x_api_key]

  # Dependency instances
  api_key_auth = APIKeyAuth()

  def require_api_key(auth_data: dict = Depends(api_key_auth)):
      return auth_data

  def require_write_permission(auth_data: dict = Depends(api_key_auth)):
      if "write" not in auth_data.get("permissions", []):
          raise HTTPException(
              status_code=status.HTTP_403_FORBIDDEN,
              detail="Write permission required"
          )
      return auth_data
  ```
  **Verification:** Test authentication with valid/invalid API keys

#### Task 2.3.2: Update API Routes with Authentication
- [ ] **Update src/api/routes/signals.py to include authentication**
  ```python
  from fastapi import APIRouter, Depends, HTTPException, Query
  from typing import List, Optional
  from src.core.dependencies import get_signal_repository
  from src.core.interfaces.repositories import SignalRepository
  from src.api.schemas.signal_schemas import SignalResponse
  from src.api.middleware.auth import require_api_key

  router = APIRouter()

  @router.get("/", response_model=List[SignalResponse])
  async def get_signals(
      limit: int = Query(20, ge=1, le=100),
      instrument: Optional[str] = Query(None),
      signal_repo: SignalRepository = Depends(get_signal_repository),
      auth: dict = Depends(require_api_key)  # Add authentication
  ):
      """Get latest trading signals"""
      try:
          signals = await signal_repo.get_latest(limit=limit, instrument=instrument)
          return [SignalResponse.from_entity(signal) for signal in signals]
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

  @router.get("/{signal_id}", response_model=SignalResponse)
  async def get_signal(
      signal_id: str,
      signal_repo: SignalRepository = Depends(get_signal_repository),
      auth: dict = Depends(require_api_key)  # Add authentication
  ):
      """Get specific signal by ID"""
      signal = await signal_repo.get_by_id(signal_id)
      if not signal:
          raise HTTPException(status_code=404, detail="Signal not found")
      return SignalResponse.from_entity(signal)
  ```
  **Verification:** Test authenticated endpoints

### 2.4 WebSocket Implementation (Day 12)

#### Task 2.4.1: Create WebSocket Manager
- [ ] **Create src/api/websockets/manager.py**
  ```python
  from typing import List, Dict, Set
  from fastapi import WebSocket, WebSocketDisconnect
  import json
  import logging
  from src.core.entities.signal import TradingSignal
  from src.api.schemas.signal_schemas import SignalResponse

  logger = logging.getLogger(__name__)

  class ConnectionManager:
      def __init__(self):
          # Store active connections
          self.active_connections: List[WebSocket] = []
          # Store subscriptions by instrument
          self.subscriptions: Dict[str, Set[WebSocket]] = {}
      
      async def connect(self, websocket: WebSocket):
          """Accept new WebSocket connection"""
          await websocket.accept()
          self.active_connections.append(websocket)
          logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
      
      def disconnect(self, websocket: WebSocket):
          """Remove WebSocket connection"""
          if websocket in self.active_connections:
              self.active_connections.remove(websocket)
          
          # Remove from all subscriptions
          for instrument in list(self.subscriptions.keys()):
              if websocket in self.subscriptions[instrument]:
                  self.subscriptions[instrument].remove(websocket)
                  if not self.subscriptions[instrument]:
                      del self.subscriptions[instrument]
          
          logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
      
      async def subscribe_to_instrument(self, websocket: WebSocket, instrument: str):
          """Subscribe connection to specific instrument signals"""
          if instrument not in self.subscriptions:
              self.subscriptions[instrument] = set()
          self.subscriptions[instrument].add(websocket)
          
          await websocket.send_text(json.dumps({
              "type": "subscription_confirmed",
              "instrument": instrument
          }))
          logger.info(f"WebSocket subscribed to {instrument}")
      
      async def broadcast_signal(self, signal: TradingSignal):
          """Broadcast signal to all relevant subscribers"""
          if not self.active_connections:
              return
          
          signal_data = SignalResponse.from_entity(signal)
          message = {
              "type": "new_signal",
              "data": signal_data.dict()
          }
          
          # Send to all connections
          for connection in self.active_connections.copy():
              try:
                  await connection.send_text(json.dumps(message, default=str))
              except Exception as e:
                  logger.error(f"Failed to send message to WebSocket: {e}")
                  self.disconnect(connection)
          
          # Send to instrument-specific subscribers
          if signal.instrument in self.subscriptions:
              for connection in self.subscriptions[signal.instrument].copy():
                  try:
                      await connection.send_text(json.dumps(message, default=str))
                  except Exception as e:
                      logger.error(f"Failed to send to subscriber: {e}")
                      self.disconnect(connection)

  # Global connection manager
  connection_manager = ConnectionManager()
  ```
  **Verification:** Test WebSocket connections and message broadcasting

#### Task 2.4.2: Create WebSocket Routes
- [ ] **Create src/api/routes/websockets.py**
  ```python
  from fastapi import APIRouter, WebSocket, WebSocketDisconnect
  import json
  import logging
  from src.api.websockets.manager import connection_manager

  logger = logging.getLogger(__name__)
  router = APIRouter()

  @router.websocket("/signals")
  async def websocket_signals(websocket: WebSocket):
      """WebSocket endpoint for real-time signals"""
      await connection_manager.connect(websocket)
      
      try:
          while True:
              # Listen for client messages
              data = await websocket.receive_text()
              message = json.loads(data)
              
              if message.get("type") == "subscribe":
                  instrument = message.get("instrument")
                  if instrument:
                      await connection_manager.subscribe_to_instrument(websocket, instrument)
              
              elif message.get("type") == "ping":
                  await websocket.send_text(json.dumps({"type": "pong"}))
      
      except WebSocketDisconnect:
          logger.info("WebSocket client disconnected")
      except Exception as e:
          logger.error(f"WebSocket error: {e}")
      finally:
          connection_manager.disconnect(websocket)
  ```
  **Verification:** Test WebSocket connection and subscription

---

## 🧪 PHASE 3: TESTING INFRASTRUCTURE (Weeks 7-8)

### Unit Testing Setup
- [ ] **Install testing framework and dependencies**
  ```bash
  pip install pytest pytest-asyncio pytest-mock pytest-cov factory-boy
  ```

- [ ] **Create test configuration**
  ```python
  # tests/conftest.py
  @pytest.fixture
  async def db_session():
      # Test database setup
      
  @pytest.fixture
  def mock_oanda_api():
      # Mock OANDA API responses
  ```

- [ ] **Write comprehensive unit tests**
  - [ ] Test all repository implementations
  - [ ] Test service layer business logic
  - [ ] Test strategy calculations and validations
  - [ ] Test API endpoint functionality
  - [ ] Test error handling scenarios

### Integration Testing
- [ ] **Database integration tests**
  - [ ] Test MongoDB operations with real database
  - [ ] Test data migration scripts
  - [ ] Test connection pooling and failover
  - [ ] Test indexing and query performance

- [ ] **External API integration tests**
  - [ ] Test OANDA API integration
  - [ ] Test rate limiting behavior
  - [ ] Test API error handling and retries
  - [ ] Test data transformation accuracy

### End-to-End Testing
- [ ] **API endpoint testing**
  ```python
  # tests/e2e/test_signals_api.py
  async def test_get_signals_endpoint():
      # Test complete API flow
  ```

- [ ] **Signal generation workflow testing**
  - [ ] Test complete signal generation pipeline
  - [ ] Test WebSocket signal broadcasting
  - [ ] Test signal persistence and retrieval
  - [ ] Test error recovery scenarios

---

## 📊 PHASE 4: MONITORING & OBSERVABILITY (Weeks 9-10)

### Structured Logging Implementation
- [ ] **Setup structured logging**
  ```python
  # src/core/logging.py
  def setup_logging():
      logging.basicConfig(
          level=logging.INFO,
          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
          handlers=[
              logging.StreamHandler(),
              logging.FileHandler('app.log')
          ]
      )
  ```

- [ ] **Add contextual logging**
  - [ ] Log all API requests/responses
  - [ ] Log strategy execution details
  - [ ] Log database operations and performance
  - [ ] Log external API calls and responses

### Metrics and Monitoring
- [ ] **Implement application metrics**
  ```python
  # src/infrastructure/monitoring/metrics.py
  from prometheus_client import Counter, Histogram, Gauge

  SIGNAL_GENERATION_COUNTER = Counter('signals_generated_total', 'Total signals generated')
  API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
  ```

- [ ] **Add system health monitoring**
  - [ ] Database connection health checks
  - [ ] External API availability checks
  - [ ] Memory and CPU usage monitoring
  - [ ] Queue size and processing rate monitoring

- [ ] **Create monitoring dashboard**
  - [ ] Setup Prometheus metrics collection
  - [ ] Create Grafana dashboard for visualization
  - [ ] Add alerting for critical metrics
  - [ ] Setup email/Slack notifications

### Error Tracking and Alerting
- [ ] **Implement error tracking**
  - [ ] Setup Sentry for error tracking
  - [ ] Add custom error reporting
  - [ ] Create error categorization and prioritization
  - [ ] Add error recovery mechanisms

- [ ] **Create alerting system**
  - [ ] Alert on signal generation failures
  - [ ] Alert on API rate limit violations
  - [ ] Alert on database connection issues
  - [ ] Alert on high error rates

---

## 🔒 PHASE 5: SECURITY & PERFORMANCE (Weeks 11-12)

### Security Enhancements
- [ ] **API Security Implementation**
  ```python
  # src/api/security.py
  class RateLimiter:
      async def __call__(self, request: Request):
          # Rate limiting implementation
  
  class APIKeyValidator:
      async def validate_key(self, api_key: str) -> bool:
          # API key validation logic
  ```

- [ ] **Data Security**
  - [ ] Encrypt sensitive data at rest
  - [ ] Implement secure credential management
  - [ ] Add input sanitization and validation
  - [ ] Implement audit logging for sensitive operations

- [ ] **Infrastructure Security**
  - [ ] Setup HTTPS for all endpoints
  - [ ] Implement CORS policy
  - [ ] Add request size limiting
  - [ ] Create security headers middleware

### Performance Optimization
- [ ] **Caching Implementation**
  ```python
  # src/infrastructure/cache/redis_cache.py
  class RedisCache:
      async def get(self, key: str) -> Optional[str]:
          # Redis cache implementation
      
      async def set(self, key: str, value: str, ttl: int = 300):
          # Cache with TTL
  ```

- [ ] **Database Performance**
  - [ ] Optimize database queries and indexes
  - [ ] Implement query result caching
  - [ ] Add connection pooling optimization
  - [ ] Create database query monitoring

- [ ] **Async Processing**
  - [ ] Implement background task processing with Celery
  - [ ] Add message queue for signal processing
  - [ ] Create async signal generation pipeline
  - [ ] Add concurrent processing for multiple strategies

---

## 🚀 PHASE 6: DEPLOYMENT & CI/CD (Weeks 13-14)

### Containerization
- [ ] **Create Docker configuration**
  ```dockerfile
  # Dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Multi-service Docker Compose**
  ```yaml
  # docker-compose.yml
  version: '3.8'
  services:
    api:
      build: .
      ports:
        - "8000:8000"
    mongodb:
      image: mongo:latest
    redis:
      image: redis:alpine
  ```

### CI/CD Pipeline
- [ ] **GitHub Actions workflow**
  ```yaml
  # .github/workflows/ci.yml
  name: CI/CD Pipeline
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Run tests
          run: pytest
  ```

- [ ] **Automated deployment**
  - [ ] Create staging and production environments
  - [ ] Add automated testing in pipeline
  - [ ] Implement blue-green deployment
  - [ ] Add rollback mechanisms

### Production Deployment
- [ ] **Infrastructure as Code**
  - [ ] Create Terraform/CloudFormation templates
  - [ ] Setup load balancers and auto-scaling
  - [ ] Configure monitoring and logging
  - [ ] Setup backup and disaster recovery

- [ ] **Production Configuration**
  - [ ] Environment-specific configuration management
  - [ ] Secret management with HashiCorp Vault
  - [ ] SSL certificate management
  - [ ] Database replica configuration

---

## 📈 PHASE 7: ADVANCED FEATURES (Weeks 15-18)

### Strategy Engine Enhancement
- [ ] **Dynamic Strategy Loading**
  ```python
  # src/core/strategy_engine.py
  class StrategyEngine:
      async def load_strategy(self, strategy_config: dict) -> Strategy:
          # Dynamic strategy loading
      
      async def execute_strategies(self, market_data: MarketData) -> List[TradingSignal]:
          # Parallel strategy execution
  ```

- [ ] **Strategy Backtesting**
  - [ ] Create backtesting framework
  - [ ] Add performance metrics calculation
  - [ ] Implement walk-forward analysis
  - [ ] Create backtesting report generation

### Real-time Data Pipeline
- [ ] **Streaming Data Architecture**
  - [ ] Implement Apache Kafka for data streaming
  - [ ] Create real-time data processing pipeline
  - [ ] Add stream processing with Apache Flink
  - [ ] Implement event sourcing for signals

- [ ] **Data Quality Monitoring**
  - [ ] Add data validation checks
  - [ ] Monitor data freshness and completeness
  - [ ] Implement data quality alerts
  - [ ] Create data lineage tracking

### Advanced Analytics
- [ ] **Signal Performance Analytics**
  ```python
  # src/application/services/analytics_service.py
  class AnalyticsService:
      async def calculate_signal_performance(self) -> SignalPerformanceReport:
          # Performance calculation logic
  ```

- [ ] **Machine Learning Integration**
  - [ ] Add feature engineering pipeline
  - [ ] Implement ML model training infrastructure
  - [ ] Create model versioning and deployment
  - [ ] Add A/B testing for strategies

---

## 🎯 SUCCESS METRICS TO TRACK

### Technical Metrics
- [ ] **Code Quality: Test coverage >90%**
- [ ] **Performance: API response time <100ms**
- [ ] **Reliability: 99.9% uptime**
- [ ] **Security: Zero critical vulnerabilities**
- [ ] **Scalability: Handle 1000+ concurrent connections**

### Business Metrics
- [ ] **Signal Generation: <30 seconds from market data to signal**
- [ ] **Data Accuracy: 99.99% data integrity**
- [ ] **System Availability: 24/7 operation**
- [ ] **Strategy Performance: Consistent signal quality**
- [ ] **User Experience: <1 second signal delivery**

### Monitoring Metrics
- [ ] **Error Rate: <0.1% for critical operations**
- [ ] **Resource Usage: <80% CPU/Memory utilization**
- [ ] **Database Performance: <50ms query response time**
- [ ] **API Rate Limits: No violations under normal load**
- [ ] **Cache Hit Rate: >95% for frequent queries**

---

## 🔧 IMMEDIATE ACTIONS (Week 1) - STEP-BY-STEP CHECKLIST

### Day 1: Project Structure Setup
- [ ] **1.1.1 Create directory structure** (15 min)
  - Run commands in task 1.1.1
  - Verify with `tree src/`
- [ ] **1.1.2 Move existing files** (30 min)  
  - Move config/settings.py → src/core/config.py
  - Move api/oanda_api.py → src/infrastructure/external_apis/
  - Update import statements in moved files
- [ ] **1.1.3 Create __init__.py files** (10 min)
  - Run find command to create all __init__.py files

### Day 2: Core Entities
- [ ] **1.2.1 Create Signal entity** (45 min)
  - Implement TradingSignal dataclass
  - Test with `python -c "from src.core.entities.signal import TradingSignal"`
- [ ] **1.2.2 Create MarketData entity** (30 min)
  - Implement Candle dataclass with from_oanda_response method
- [ ] **1.2.3 Create Strategy entity** (20 min)
  - Implement StrategyConfig dataclass

### Day 3: Repository Interfaces  
- [ ] **1.3.1 Create base repository interfaces** (45 min)
  - Implement SignalRepository and MarketDataRepository ABCs
- [ ] **1.3.2 Create external API interfaces** (30 min)
  - Implement MarketDataProvider ABC

### Day 4: Configuration
- [ ] **1.4.1 Install dependencies** (10 min)
  - Run pip install commands
- [ ] **1.4.2 Create configuration class** (30 min)
  - Implement Settings with Pydantic validation
- [ ] **1.4.3 Setup environment variables** (15 min)
  - Create .env file with all required variables

### Day 5: Database Implementation
- [ ] **1.5.1 Create database connection manager** (45 min)
  - Implement DatabaseManager with async Motor client
- [ ] **1.5.2 Implement signal repository** (60 min)
  - Create MongoSignalRepository with all CRUD operations

### Day 6: Dependency Injection
- [ ] **1.6.1 Create dependency container** (30 min)
  - Implement Container class with repository getters

### Day 7: Basic API
- [ ] **1.7.1 Create FastAPI app** (45 min)
  - Setup main.py with health check endpoint
- [ ] **1.7.2 Create API routes** (45 min)
  - Implement health and signals routes

### Immediate Validation Steps:
1. **Test database connection:** `python -c "import asyncio; from src.infrastructure.database.connection import db_manager; asyncio.run(db_manager.connect())"`
2. **Test API startup:** `python src/api/main.py`
3. **Test health endpoint:** `curl http://localhost:8000/health`
4. **Test signals endpoint:** `curl -H "X-API-Key: dev-key-123" http://localhost:8000/api/v1/signals`

---

## 📋 LLM EXECUTION GUIDELINES

### For Each Task:
1. **Read the full task description** including verification steps
2. **Create the file exactly as specified** with the provided code
3. **Run the verification command** to ensure it works
4. **Fix any import/syntax errors** before proceeding
5. **Move to next task only after verification passes**

### Critical Dependencies:
- **Task 1.4.1 must complete** before any database operations
- **Task 1.5.1 must complete** before repository implementation  
- **Task 1.6.1 must complete** before API routes
- **Tasks 1.1-1.3 must complete** before any service implementation

### Error Handling:
- If imports fail, check directory structure and __init__.py files
- If database connection fails, verify MongoDB URI in .env
- If API fails to start, check all dependencies are installed
- Test each component in isolation before integration

---

## 🎯 SUCCESS METRICS TO TRACK

### Technical Metrics
- [ ] **Code Quality: Test coverage >90%**
- [ ] **Performance: API response time <100ms**
- [ ] **Reliability: 99.9% uptime**
- [ ] **Security: Zero critical vulnerabilities**
- [ ] **Scalability: Handle 1000+ concurrent connections**

### Business Metrics
- [ ] **Signal Generation: <30 seconds from market data to signal**
- [ ] **Data Accuracy: 99.99% data integrity**
- [ ] **System Availability: 24/7 operation**
- [ ] **Strategy Performance: Consistent signal quality**
- [ ] **User Experience: <1 second signal delivery**

### Monitoring Metrics
- [ ] **Error Rate: <0.1% for critical operations**
- [ ] **Resource Usage: <80% CPU/Memory utilization**
- [ ] **Database Performance: <50ms query response time**
- [ ] **API Rate Limits: No violations under normal load**
- [ ] **Cache Hit Rate: >95% for frequent queries**

---

## � IMPLEMENTATION PHASES SUMMARY

### **Phase 1-2 (Weeks 1-6): Foundation & API**
- Clean architecture implementation
- Database redesign and API layer
- Service layer and WebSocket support

### **Phase 3-4 (Weeks 7-10): Quality & Monitoring**
- Comprehensive testing infrastructure
- Monitoring, logging, and observability

### **Phase 5-6 (Weeks 11-14): Security & Deployment**
- Security enhancements and performance optimization
- CI/CD pipeline and production deployment

### **Phase 7 (Weeks 15-18): Advanced Features**
- Enhanced strategy engine and real-time pipeline
- Advanced analytics and ML integration

---

## 🎯 CRITICAL PATH DEPENDENCIES

### **Must Complete First:**
- **Clean Architecture Setup** → All other development
- **Database Redesign** → Data consistency and performance
- **API Layer** → Frontend integration and external access
- **Configuration Management** → Security and deployment
- **Testing Infrastructure** → Code reliability and maintenance

### **High Impact Items:**
- **Unified Strategy Engine** → Code maintainability
- **Monitoring & Logging** → Production readiness
- **Security Implementation** → Safe production deployment
- **Performance Optimization** → Scalability and user experience

---

*This LLM-optimized checklist provides step-by-step implementation with specific file paths, code examples, and verification steps. Each task is sized for 15-60 minute focused implementation sessions with clear success criteria.*
