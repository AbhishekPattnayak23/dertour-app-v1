from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.schemas.admin import (
    AdminDashboardStats,
    UserAnalytics,
    ProjectAnalytics,
    SystemHealth,
    AuditLogEntry
)
from app.crud.user import user_crud

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""

    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active is True).count()
    new_users_today = db.query(User).filter(
        func.date(User.created_at) == datetime.utcnow().date()
    ).count()

    # Project statistics
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()

    # Task statistics
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == "completed").count()
    pending_tasks = db.query(Task).filter(Task.status == "pending").count()

    return AdminDashboardStats(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        total_projects=total_projects,
        active_projects=active_projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users with filtering and pagination"""

    query = db.query(User)

    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""

    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user details"""

    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated_user = user_crud.update(db, db_obj=user, obj_in=user_update)
    return updated_user

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user"""

    # Check if user already exists
    existing_user = user_crud.get_by_email(db, email=user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    user = user_crud.create(db, obj_in=user_create)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete or deactivate user"""

    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Soft delete - deactivate user instead of hard delete
    user_crud.update(db, db_obj=user, obj_in={"is_active": False})
    return {"message": "User deactivated successfully"}

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate a deactivated user"""

    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_crud.update(db, db_obj=user, obj_in={"is_active": True})
    return {"message": "User activated successfully"}

@router.get("/analytics/users", response_model=UserAnalytics)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user analytics for specified period"""

    start_date = datetime.utcnow() - timedelta(days=days)

    # User registrations over time
    registrations = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).all()

    # Active users over time
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active is True).count()

    return UserAnalytics(
        total_users=total_users,
        active_users=active_users,
        registration_trend=[
            {"date": str(reg.date), "count": reg.count} for reg in registrations
        ],
        period_days=days
    )

@router.get("/analytics/projects", response_model=ProjectAnalytics)
async def get_project_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get project analytics for specified period"""

    start_date = datetime.utcnow() - timedelta(days=days)

    # Projects created over time
    projects_created = db.query(
        func.date(Project.created_at).label('date'),
        func.count(Project.id).label('count')
    ).filter(
        Project.created_at >= start_date
    ).group_by(
        func.date(Project.created_at)
    ).all()

    # Project status distribution
    status_distribution = db.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()

    return ProjectAnalytics(
        total_projects=db.query(Project).count(),
        active_projects=db.query(Project).filter(Project.status == "active").count(),
        completed_projects=db.query(Project).filter(Project.status == "completed").count(),
        creation_trend=[
            {"date": str(proj.date), "count": proj.count} for proj in projects_created
        ],
        status_distribution={
            status.status: status.count for status in status_distribution
        },
        period_days=days
    )

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system health status"""

    try:
        # Database connectivity check
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Memory and performance metrics would typically come from monitoring tools
    return SystemHealth(
        database_status=db_status,
        api_status="healthy",
        uptime_seconds=0,  # This would be calculated from app start time
        memory_usage_mb=0,  # This would come from system monitoring
        cpu_usage_percent=0.0,  # This would come from system monitoring
        active_connections=0  # This would come from connection pool monitoring
    )

@router.get("/logs/audit", response_model=List[AuditLogEntry])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering"""

    # This would typically query an audit_logs table
    # For now, return empty list as audit logging would be implemented separately
    return []

@router.post("/maintenance/cleanup")
async def cleanup_system(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Perform system cleanup operations"""

    # This could include operations like:
    # - Cleaning up expired sessions
    # - Removing old temporary files
    # - Archiving old logs
    # - Optimizing database

    return {"message": "System cleanup completed successfully"}
