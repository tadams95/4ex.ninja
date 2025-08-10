"""
Metrics Collection Middleware

FastAPI middleware to automatically collect performance and business metrics
for all API requests.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

try:
    from infrastructure.monitoring.business_metrics import business_metrics_monitor
    from infrastructure.monitoring.performance import performance_monitor
    from infrastructure.monitoring.system_metrics import system_metrics_monitor
except ImportError:
    # Fallback for development/testing
    business_metrics_monitor = None
    performance_monitor = None
    system_metrics_monitor = None


class MetricsCollectionMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect metrics for all requests."""
    
    def __init__(self, app, collect_user_metrics: bool = True):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        self.collect_user_metrics = collect_user_metrics
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for each request."""
        start_time = time.perf_counter()
        request_timestamp = time.time()
        
        # Extract request info
        method = request.method
        url_path = request.url.path
        user_id = self._extract_user_id(request)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Record metrics
            await self._record_request_metrics(
                request, response, processing_time_ms, user_id
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{processing_time_ms:.2f}ms"
            response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Record error metrics
            await self._record_error_metrics(
                request, e, processing_time_ms, user_id
            )
            
            # Re-raise the exception
            raise
            
    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request (if available)."""
        # Try to get user from JWT token or session
        user = getattr(request.state, 'user', None)
        if user:
            return getattr(user, 'id', 'authenticated')
            
        # Check for API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"api_key_{api_key[-8:]}"  # Last 8 chars for identification
            
        return 'anonymous'
        
    async def _record_request_metrics(
        self,
        request: Request,
        response: Response,
        processing_time_ms: float,
        user_id: str
    ):
        """Record metrics for successful requests."""
        method = request.method
        url_path = request.url.path
        status_code = response.status_code
        
        # Record API call metrics
        if business_metrics_monitor:
            business_metrics_monitor.record_api_call(
                endpoint=url_path,
                method=method,
                response_time_ms=processing_time_ms,
                status_code=status_code,
                user_id=user_id
            )
        
        # Record performance metrics
        if performance_monitor:
            performance_monitor.record_timer(
                name="api_request_duration",
                duration_ms=processing_time_ms,
                tags={
                    "method": method,
                    "endpoint": url_path,
                    "status_code": str(status_code)
                }
            )
        
        # Record user activity (if enabled and not anonymous)
        if self.collect_user_metrics and user_id != 'anonymous' and business_metrics_monitor:
            activity_type = self._categorize_endpoint(url_path, method)
            business_metrics_monitor.record_user_activity(
                user_id=user_id,
                activity_type=activity_type,
                metadata={
                    "endpoint": url_path,
                    "method": method,
                    "response_time_ms": processing_time_ms
                }
            )
            
        # Performance monitoring for specific endpoints
        if url_path.startswith('/api/v1/signals') and performance_monitor:
            performance_monitor.record_histogram(
                name="signals_api_response_time",
                value=processing_time_ms,
                tags={"endpoint": url_path}
            )
            
        # Log slow requests
        if processing_time_ms > 1000:  # Slower than 1 second
            self.logger.warning(
                f"Slow request: {method} {url_path} took {processing_time_ms:.1f}ms "
                f"(status: {status_code}, user: {user_id})"
            )
            
    async def _record_error_metrics(
        self,
        request: Request,
        exception: Exception,
        processing_time_ms: float,
        user_id: str
    ):
        """Record metrics for failed requests."""
        method = request.method
        url_path = request.url.path
        error_type = type(exception).__name__
        
        # Record API error metrics
        if business_metrics_monitor:
            business_metrics_monitor.record_api_call(
                endpoint=url_path,
                method=method,
                response_time_ms=processing_time_ms,
                status_code=500,  # Default to 500 for unhandled exceptions
                user_id=user_id
            )
        
        # Record error performance metrics
        if performance_monitor:
            performance_monitor.record_timer(
                name="api_request_error",
                duration_ms=processing_time_ms,
                tags={
                    "method": method,
                    "endpoint": url_path,
                    "error_type": error_type
                }
            )
        
        # Log the error
        self.logger.error(
            f"Request error: {method} {url_path} failed after {processing_time_ms:.1f}ms "
            f"(error: {error_type}, user: {user_id})"
        )
        
    def _categorize_endpoint(self, url_path: str, method: str) -> str:
        """Categorize endpoint for user activity tracking."""
        if url_path.startswith('/api/v1/auth'):
            if 'login' in url_path:
                return 'login'
            elif 'register' in url_path:
                return 'registration'
            elif 'logout' in url_path:
                return 'logout'
            else:
                return 'authentication'
                
        elif url_path.startswith('/api/v1/signals'):
            if method == 'GET':
                return 'signal_view'
            else:
                return 'signal_interaction'
                
        elif url_path.startswith('/api/v1/market-data'):
            return 'market_data_access'
            
        elif url_path.startswith('/api/v1/performance'):
            return 'performance_monitoring'
            
        elif url_path.startswith('/health'):
            return 'health_check'
            
        else:
            return 'general_api_access'


def create_metrics_middleware(collect_user_metrics: bool = True):
    """Factory function to create metrics collection middleware."""
    def middleware_factory(app):
        return MetricsCollectionMiddleware(app, collect_user_metrics)
    return middleware_factory
