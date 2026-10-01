"""
ExpenseFlow - FastAPI Application Entry Point
Production-grade RESTful API for personal financial management.
Author & Architect: Chirag Darji (dchirag516@gmail.com)
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.connection import engine, test_db_connection, sync_database_schema
from app.database.base import Base

# Ensure all models are loaded so Base.metadata knows about all tables
import app.models  # noqa: F401

from app.routers import (
    auth,
    categories,
    transactions,
    budgets,
    savings,
    dashboard,
    reports,
    reminders,
    recurring,
    notifications,
    push,
    preferences,
    scheduler
)

logger = logging.getLogger("expenseflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager: handles database startup checks and graceful shutdown."""
    print(f"[{settings.PROJECT_NAME}] Starting up in {settings.ENVIRONMENT} mode...")
    connected = test_db_connection()
    if connected:
        print("[Database] Database connected successfully! Ensuring tables exist...")
        try:
            sync_database_schema()
            print("[Database] Schema synchronized successfully.")
        except Exception as e:
            print(f"[Database Error] Table creation failed: {e}")
    else:
        print("[Database Warning] Could not connect to database. Please verify your credentials in .env.")
    yield
    print(f"[{settings.PROJECT_NAME}] Shutting down...")


app = FastAPI(
    title="ExpenseFlow API",
    description="Production-quality Personal Expense & Income Management SaaS REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handler for Request Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error["loc"] if loc != "body"])
        errors.append(f"{field}: {error['msg']}" if field else error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "detail": "Validation error",
            "errors": errors,
            "message": errors[0] if errors else "Invalid request data."
        }
    )


# Centralized Exception Handler for HTTP Exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "message": exc.detail
        },
        headers=exc.headers
    )


# Centralized Exception Handler for Unhandled Server Errors
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error processing request: {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "detail": "Internal server error occurred.",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Health check endpoint
@app.get("/api/health", tags=["Health"])
def health_check(response: Response):
    db_status = test_db_connection()
    if not db_status:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "healthy" if db_status else "degraded",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_status
    }


# Mount API routers under /api
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(budgets.router, prefix=settings.API_V1_PREFIX)
app.include_router(savings.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(reminders.router, prefix=settings.API_V1_PREFIX)
app.include_router(recurring.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(push.router, prefix=settings.API_V1_PREFIX)
app.include_router(preferences.router, prefix=settings.API_V1_PREFIX)
app.include_router(scheduler.router, prefix=settings.API_V1_PREFIX)

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
