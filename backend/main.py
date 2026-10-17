from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import check_database_connection
from routes.jobs import router as jobs_router
from routes.github import router as github_router
from routes.assessments import router as assessments_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-based AI Career Coach API — Integrating Job Requirement Analysis & GitHub Portfolio Evidence",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(jobs_router)
app.include_router(github_router)
app.include_router(assessments_router)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """
    Primary health verification endpoint for frontend and monitoring.
    """
    return {
        "status": "healthy",
        "message": "AI Career Coach API is running",
    }


@app.get("/api/v1/status", status_code=status.HTTP_200_OK, tags=["System"])
def get_system_status():
    """
    System status endpoint detailing application version and verified Supabase database status.
    """
    db_status = check_database_connection()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_status,
    }
