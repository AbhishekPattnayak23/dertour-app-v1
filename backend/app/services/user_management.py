from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile_data: Optional[Dict[str, Any]] = None


class UserManagementService:
    """Service for managing user profiles, roles, and entitlements"""

    def __init__(self, db: Session, user_repository=None):
        self.db = db
        self.user_repository = user_repository or UserRepository(db)
        self.repo = UserRepository(db)
        self.logger = logger

    def assign_entitlement(self, user_id: str, entitlement: str) -> bool:
        """Assign an entitlement to a user"""
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return False
            
            # Get current entitlements or initialize empty list
            entitlements = getattr(user, "entitlements", []) or []
            if entitlement not in entitlements:
                entitlements.append(entitlement)
                return self.user_repository.update(user_id, {"entitlements": entitlements})
            return True
        except Exception:
            return False

    def revoke_entitlement(self, user_id: str, entitlement: str) -> bool:
        """Revoke an entitlement from a user"""
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return False
            
            entitlements = getattr(user, "entitlements", []) or []
            if entitlement in entitlements:
                entitlements.remove(entitlement)
                return self.user_repository.update(user_id, {"entitlements": entitlements})
            return True
        except Exception:
            return False

    def get_user_entitlements(self, user_id: str) -> list:
        """Get all entitlements for a user"""
        try:
            user = self.user_repository.get_by_id(user_id)
            if user:
                return getattr(user, "entitlements", []) or []
            return []
        except Exception:
            return []

    def check_user_entitlement(self, user_id: str, entitlement: str) -> bool:
        """Check if user has specific entitlement"""
        try:
            entitlements = self.get_user_entitlements(user_id)
            return entitlement in entitlements
        except Exception:
            return False

    def manage_access_level(self, user_id: str, access_level: str) -> bool:
        """Set user access level"""
        try:
            valid_levels = ["basic", "standard", "premium", "admin"]
            if access_level not in valid_levels:
                return False
            return self.user_repository.update(user_id, {"access_level": access_level})
        except Exception:
            return False

    def create_user(self, user_data: dict):
        """Create a new user with validation."""
        email = user_data.get("email", "").strip().lower()
        if not email:
            raise ValueError("Email is required")

        if self.repo.email_exists(email):
            raise ValueError(f"Email '{email}' is already registered")

        username = user_data.get("username", "").strip()
        if username and self.repo.username_exists(username):
            raise ValueError(f"Username '{username}' is already taken")

        normalized_data = dict(user_data)
        normalized_data["email"] = email

        if "role" not in normalized_data:
            normalized_data["role"] = "user"

        if "is_active" not in normalized_data:
            normalized_data["is_active"] = True

        return self.repo.create(normalized_data)

    def update_user(self, user_id: int, update_data: dict):
        """Update user profile information."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None

        safe_fields = {
            "full_name",
            "username",
            "email",
            "department",
            "job_title",
            "phone",
            "avatar_url",
        }

        filtered = {k: v for k, v in update_data.items() if k in safe_fields}

        if "email" in filtered:
            filtered["email"] = filtered["email"].strip().lower()
            existing = self.repo.get_by_email(filtered["email"])
            if existing and existing.id != user_id:
                raise ValueError("Email already in use by another account")

        if "username" in filtered:
            filtered["username"] = filtered["username"].strip()
            existing = self.repo.get_by_username(filtered["username"])
            if existing and existing.id != user_id:
                raise ValueError("Username already taken")

        return self.repo.update(user_id, filtered)

    def assign_role(self, user_id: int, role: str):
        """Assign a role to a user."""
        valid_roles = {"admin", "user", "viewer", "editor", "moderator"}
        role = role.strip().lower()

        if role not in valid_roles:
            valid_roles_str = ", ".join(sorted(valid_roles))
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {valid_roles_str}"
            )

        return self.repo.update(user_id, {"role": role})

    def set_user_active(self, user_id: int, is_active: bool):
        """Activate or deactivate a user account."""
        return self.repo.update(user_id, {"is_active": is_active})

    def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Get a user's full profile."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        return user.to_dict() if hasattr(user, "to_dict") else {}

    def list_users(
        self,
        page: int = 1,
        size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> dict:
        """List users with pagination and filtering."""
        skip = (page - 1) * size
        users, total = self.repo.get_users_filtered(
            skip=skip,
            limit=size,
            role=role,
            is_active=is_active,
            search=search,
        )

        pages = (total + size - 1) // size if size > 0 else 0

        return {
            "items": [
                u.to_dict() if hasattr(u, "to_dict") else {} for u in users
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def create_user_profile(self, user_data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile."""
        # Validate user data
        if not user_data.get("username") or not user_data.get("email"):
            raise ValueError("Username and email are required")

        # Create user through repository
        new_user = self.user_repository.create_user(user_data)
        return new_user

    def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user profile information."""
        # Update user profile
        updated_user = self.user_repository.update_user(user_id, updates)
        if not updated_user:
            raise ValueError(f"User with ID {user_id} not found")
        return True

    def assign_user_role(self, user_id: int, role: UserRole) -> bool:
        """Assign role to user."""
        # Validate role
        valid_roles = ["admin", "user", "moderator"]
        role_value = role.value if isinstance(role, UserRole) else role
        if role_value not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")

        # Update user role
        success = self.user_repository.update_user_role(user_id, role_value)
        if not success:
            raise ValueError(f"User with ID {user_id} not found")
        return success

    def delete_user_profile(self, user_id: int) -> bool:
        """Delete a user profile."""
        success = self.user_repository.delete_user(user_id)
        if not success:
            raise ValueError(f"User with ID {user_id} not found")
        return success

    def list_user_profiles(self, limit: int = 100, offset: int = 0) -> list:
        """List user profiles with pagination."""
        return self.user_repository.list_users(limit=limit, offset=offset)

    def update_user_status(self, user_id: int, status: UserStatus) -> bool:
        """Update user status"""
        status_value = status.value if isinstance(status, UserStatus) else status
        return self.user_repository.update(user_id, {"status": status_value})

    def get_users_by_role(self, role: UserRole) -> List[UserProfile]:
        """Get users by role"""
        role_value = role.value if isinstance(role, UserRole) else role
        return self.user_repository.get_users_by_role(role_value)

    def get_users_by_status(self, status: UserStatus) -> List[UserProfile]:
        """Get users by status"""
        status_value = status.value if isinstance(status, UserStatus) else status
        return self.user_repository.get_users_by_status(status_value)

    def validate_user_permissions(self, user_id: int, required_role: UserRole) -> bool:
        """Validate user permissions"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        user_role = getattr(user, 'role', None)
        required_role_value = required_role.value if isinstance(required_role, UserRole) else required_role
        return user_role == required_role_value


class EntitlementManager:
    """Manages user entitlements and access permissions"""

    def __init__(self):
        self.entitlements_cache = {}
