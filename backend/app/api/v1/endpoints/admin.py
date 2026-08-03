from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.security import get_current_user, require_admin
from app.db.repositories.user_repository import UserRepository
from app.services.user_management import UserManagementService

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


@router.get("/users", response_model=dict)
async def get_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
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


@router.get("/users/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Get a specific user by ID."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.post("/users", response_model=dict, status_code=201)
async def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
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


@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Update an existing user."""
    service = UserManagementService(db)
    user = service.update_user(user_id, user_data)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Delete a user."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    repo.delete(user_id)


@router.patch("/users/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
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


@router.patch("/users/{user_id}/status", response_model=dict)
async def toggle_user_status(
    user_id: int,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Activate or deactivate a user account."""
    service = UserManagementService(db)
    is_active = status_data.get("is_active")

    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active field is  \
            required")

    user = service.set_user_active(user_id, is_active)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.to_dict()


@router.get("/stats", response_model=dict)
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_admin),
):
    """Get administrative statistics."""
    repo = UserRepository(db)
    stats = repo.get_user_stats()
    return stats
