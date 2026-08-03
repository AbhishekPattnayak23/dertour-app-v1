from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from ....core.database import get_db
from ....models.user import User
from ....schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse
)
from ....crud.user import user_crud
# Add missing dependency - creating a stub for now
from ....core.dependencies import get_current_active_superuser

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get all users - admin only"""
    try:
        users = user_crud.get_multi(db, skip=skip, limit=limit)
        total = user_crud.count(db)
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.post("/users", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_superuser),
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


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get user by ID - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
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


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Delete user - admin only"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_crud.remove(db, id=user_id)
    return {"message": "User deleted successfully"}


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
