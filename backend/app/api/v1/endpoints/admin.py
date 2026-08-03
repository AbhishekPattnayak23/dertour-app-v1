from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.config.database import get_db as get_db_alt
from app.core.auth import get_current_admin_user
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.schemas.user import UserResponse, UserUpdate, UserCreate, UserListResponse
from app.schemas.admin import (
    AdminDashboardStats,
    UserAnalytics,
    ProjectAnalytics,
    SystemHealth,
    AuditLogEntry
)
from app.crud.user import user_crud
from app.db.repositories.user_repository import UserRepository
from app.services.user_management import UserManagementService
from app.core.dependencies import get_current_active_superuser

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
    limit: int = Query(100, ge=1, le=1000),
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


@router.get("/users-alt", response_model=dict)
async def get_all_users_alt(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Get all users with pagination and filtering."""
    repo = UserRepository(db)
    skip = (page - 1) * size

    users, total = repo.get_users_filtered(
        skip=skip,
        limit=size,
        role=role,
        is_active=is_active,
        search=search,
    )

    return {
        "items": [u.to_dict() for u in users],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if size > 0 else 0,
    }


@router.post("/users", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_superuser),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user - admin only"""
    try:
        # Check if user already exists
        existing_user = user_crud.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        user = user_crud.create(db, obj_in=user_in)
        return UserResponse.from_orm(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/users-alt", response_model=dict, status_code=201)
async def create_user_alt(
    user_data: dict,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Create a new user."""
    service = UserManagementService(db)

    existing = UserRepository(db).get_by_email(user_data.get("email", ""))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = service.create_user(user_data)
    return user.to_dict()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
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
    return UserResponse.from_orm(user)


@router.get("/users-alt/{user_id}", response_model=dict)
async def get_user_by_id_alt(
    user_id: int,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Get a specific user by ID."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        user = user_crud.update(db, db_obj=user, obj_in=user_in)
        return UserResponse.from_orm(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@router.put("/users-alt/{user_id}", response_model=dict)
async def update_user_alt(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Update an existing user."""
    service = UserManagementService(db)
    user = service.update_user(user_id, user_data)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
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


@router.delete("/users-alt/{user_id}", status_code=204)
async def delete_user_alt(
    user_id: int,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Delete a user."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    repo.delete(user_id)


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
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


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    role: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Update user role - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    valid_roles = ["admin", "manager", "user", "guest"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )

    user.role = role
    db.commit()
    db.refresh(user)
    return {"message": f"User role updated to {role}"}


@router.patch("/users-alt/{user_id}/role", response_model=dict)
async def update_user_role_alt(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Update a user's role."""
    service = UserManagementService(db)
    new_role = role_data.get("role")

    if not new_role:
        raise HTTPException(status_code=400, detail="Role is required")

    user = service.assign_role(user_id, new_role)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    status_value: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Update user status - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    valid_statuses = ["active", "inactive", "suspended", "pending"]
    if status_value not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    user.status = status_value
    db.commit()
    db.refresh(user)
    return {"message": f"User status updated to {status_value}"}


@router.patch("/users-alt/{user_id}/status", response_model=dict)
async def toggle_user_status(
    user_id: int,
    status_data: dict,
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Activate or deactivate a user account."""
    service = UserManagementService(db)
    is_active = status_data.get("is_active")

    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active field is required")

    user = service.set_user_active(user_id, is_active)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.get("/users/{user_id}/entitlements")
async def get_user_entitlements(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get user entitlements - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "user_id": user_id,
        "entitlements": getattr(user, 'entitlements', []),
        "role": getattr(user, 'role', 'user')
    }


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
    project_statuses = db.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()

    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()

    return ProjectAnalytics(
        total_projects=total_projects,
        active_projects=active_projects,
        creation_trend=[
            {"date": str(proj.date), "count": proj.count} for proj in projects_created
        ],
        status_distribution=[
            {"status": status.status, "count": status.count} for status in project_statuses
        ],
        period_days=days
    )


@router.get("/stats", response_model=dict)
async def get_admin_stats(
    db: Session = Depends(get_db_alt),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Get administrative statistics."""
    repo = UserRepository(db)
    stats = repo.get_user_stats()
    return stats
