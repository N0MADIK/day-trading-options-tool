from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.db import init_db, close_db
from app.api.v1.router import api_router
from app.domain.errors import BaseDomainError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    print(f"🚀 {settings.app_name} v{settings.app_version} started successfully")
    
    yield
    
    # Shutdown
    await close_db()
    print("👋 Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI backend for Options Trading Dashboard with clean architecture",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Global exception handlers
@app.exception_handler(BaseDomainError)
async def domain_error_handler(request, exc: BaseDomainError):
    """Handle domain errors and return consistent HTTP responses"""
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
    
    status_code = {
        "NotFoundError": 404,
        "ConflictError": 409,
        "ValidationError": 400,
        "UnauthorizedError": 401,
        "ForbiddenError": 403,
        "ExternalServiceError": 502,
        "DatabaseError": 500,
    }.get(exc.__class__.__name__, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
