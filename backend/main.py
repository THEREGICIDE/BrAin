"""
Production-Ready FastAPI Application with Comprehensive Logging and Monitoring
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
import uuid
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest
from google.cloud import logging as cloud_logging
import traceback

from app.config import settings
from app.api.routes import router
from app.services.bigquery_service import bigquery_service

# Configure structured logging
logger = structlog.get_logger(__name__)

# Prometheus metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
error_count = Counter('http_errors_total', 'Total HTTP errors', ['method', 'endpoint', 'status'])

# Initialize Google Cloud Logging if enabled
if settings.enable_cloud_logging and settings.google_cloud_project:
    try:
        cloud_logging_client = cloud_logging.Client(project=settings.google_cloud_project)
        cloud_logging_client.setup_logging()
        logger.info("Google Cloud Logging initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Cloud Logging: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting application",
               app_name=settings.app_name,
               version=settings.app_version,
               environment=settings.environment)
    
    # Log startup configuration
    await bigquery_service.log_application_log({
        "level": "INFO",
        "logger": "Application",
        "message": "Application started",
        "context": {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
            "workers": settings.workers
        }
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await bigquery_service.log_application_log({
        "level": "INFO",
        "logger": "Application",
        "message": "Application shutdown",
        "context": {"app_name": settings.app_name}
    })

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered personalized trip planner with EMT booking integration",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Trusted Host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.googleapis.com", "localhost", "127.0.0.1"]
    )

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Comprehensive logging middleware"""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request details
    start_time = time.time()
    
    logger.info("Request received",
               request_id=request_id,
               method=request.method,
               path=request.url.path,
               client_ip=request.client.host if request.client else "unknown",
               user_agent=request.headers.get("user-agent", "unknown"))
    
    # Log to BigQuery
    await bigquery_service.log_analytics_event(
        "api_request",
        {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info("Request completed",
                   request_id=request_id,
                   method=request.method,
                   path=request.url.path,
                   status_code=response.status_code,
                   duration_seconds=round(duration, 3))
        
        # Update Prometheus metrics
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log to BigQuery
        await bigquery_service.log_analytics_event(
            "api_response",
            {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_seconds": duration
            }
        )
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(duration, 3))
        
        return response
        
    except Exception as e:
        # Log error
        duration = time.time() - start_time
        error_trace = traceback.format_exc()
        
        logger.error("Request failed",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                    duration_seconds=round(duration, 3))
        
        # Update error metrics
        error_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        
        # Log to BigQuery
        await bigquery_service.log_application_log({
            "level": "ERROR",
            "logger": "Middleware",
            "message": f"Request failed: {str(e)}",
            "error_trace": error_trace,
            "request_id": request_id,
            "context": {
                "method": request.method,
                "path": request.url.path,
                "duration": duration
            }
        })
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "message": str(e) if settings.debug else "An error occurred"
            },
            headers={"X-Request-ID": request_id}
        )

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    if not settings.rate_limit_enabled:
        return await call_next(request)
    
    # Simple rate limiting based on IP
    client_ip = request.client.host if request.client else "unknown"
    
    # TODO: Implement actual rate limiting with Redis
    # For now, just log
    logger.debug("Rate limit check", client_ip=client_ip)
    
    return await call_next(request)

# Include API routes
app.include_router(router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with application info"""
    logger.info("Root endpoint accessed")
    
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": "/docs" if settings.debug else "Disabled in production",
        "health": "/api/v1/health",
        "metrics": "/metrics" if settings.enable_metrics else "Disabled"
    }

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check BigQuery connection
    try:
        await bigquery_service.log_analytics_event("health_check", {"timestamp": time.time()})
        health_status["checks"]["bigquery"] = "healthy"
    except Exception as e:
        health_status["checks"]["bigquery"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis if enabled
    if settings.use_redis_cache:
        try:
            # TODO: Add Redis health check
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    # Check Gemini API
    if settings.gemini_api_key:
        health_status["checks"]["gemini_api"] = "configured"
    else:
        health_status["checks"]["gemini_api"] = "not configured"
        health_status["status"] = "degraded"
    
    # Check Maps API
    if settings.google_maps_api_key:
        health_status["checks"]["maps_api"] = "configured"
    else:
        health_status["checks"]["maps_api"] = "not configured"
    
    logger.info("Health check performed", status=health_status["status"])
    
    return health_status

# Metrics endpoint for Prometheus
if settings.enable_metrics:
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        logger.debug("Metrics endpoint accessed")
        return Response(content=generate_latest(), media_type="text/plain")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    logger.warning("404 Not Found",
                  path=request.url.path,
                  method=request.method)
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": f"The requested resource {request.url.path} was not found",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    error_trace = traceback.format_exc()
    
    logger.error("Unhandled exception",
                request_id=request_id,
                error=str(exc),
                error_type=type(exc).__name__,
                path=request.url.path)
    
    # Log to BigQuery
    await bigquery_service.log_application_log({
        "level": "ERROR",
        "logger": "ExceptionHandler",
        "message": f"Unhandled exception: {str(exc)}",
        "error_trace": error_trace,
        "request_id": request_id,
        "context": {
            "path": request.url.path,
            "method": request.method
        }
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "request_id": request_id
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting application via uvicorn",
               host=settings.host,
               port=settings.port,
               workers=settings.workers)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_config=settings.get_log_config()
    )