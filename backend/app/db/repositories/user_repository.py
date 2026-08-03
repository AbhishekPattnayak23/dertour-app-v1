from typing import List, Optional, Tuple

from sqlalchemy.orm import Session


class UserRepository:
    """Data access layer for user operations."""

    def __init__(self, db: Session):
        self.db = db

    def _get_model(self):
        """Lazily import User model to avoid circular imports."""
        try:
            from app.models.user import User
            return User
        except ImportError:
            return None

    def get_by_id(self, user_id: int):
        """Get a user by their ID."""
        User = self._get_model()
        if User is None:
            return None
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str):
        """Get a user by their email address."""
        User = self._get_model()
        if User is None:
            return None
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str):
        """Get a user by their username."""
        User = self._get_model()
        if User is None:
            return None
        return self.db.query(User).filter(User.username == username).first()

    def get_users_filtered(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List, int]:
        """Get users with optional filters, returning (users, total_count)."""
        User = self._get_model()
        if User is None:
            return [], 0

        query = self.db.query(User)

        if role is not None:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                User.email.ilike(search_term) |
                User.username.ilike(search_term) |
                User.full_name.ilike(search_term)
            )

        total = query.count()
        users = query.offset(skip).limit(limit).all()

        return users, total

    def create(self, user_data: dict):
        """Create a new user record."""
        User = self._get_model()
        if User is None:
            return None

        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, update_data: dict):
        """Update an existing user record."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        """Delete a user record."""
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.get_by_email(email) is not None

    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return self.get_by_username(username) is not None

    def get_user_stats(self) -> dict:
        """Get aggregate statistics about users."""
        User = self._get_model()
        if User is None:
            return {"total": 0, "active": 0, "inactive": 0}

        total = self.db.query(User).count()
        active = self.db.query(User).filter(
            User.is_active is True).count()  #
        inactive = total - active

        role_counts = {}
        try:
            rows = (
                self.db.query(User.role, User.id)
                .group_by(User.role)
                .all()
            )
            for role, _ in rows:
                if role not in role_counts:
                    role_counts[str(role)] = 0
                role_counts[str(role)] += 1
        except Exception:
            pass

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_role": role_counts,
        }

    def create_user(self, user_data: dict) -> dict:
        """Create a new user in the database."""
        # Implementation would insert user data into database
        user_id = len(getattr(self, '_users', [])) + 1
        if not hasattr(self, '_users'):
            self._users = []

        new_user = {
            "id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "role": user_data.get("role", "user"),
            "profile": user_data.get("profile", {})
        }
        self._users.append(new_user)
        return new_user

    def update_user(self, user_id: int, user_data: dict) -> dict:
        """Update an existing user."""
        if not hasattr(self, '_users'):
            self._users = []

        for user in self._users:
            if user["id"] == user_id:
                user.update(user_data)
                return user
        return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        if not hasattr(self, '_users'):
            self._users = []

        for i, user in enumerate(self._users):
            if user["id"] == user_id:
                del self._users[i]
                return True
        return False

    def list_users(self, limit: int = 100, offset: int = 0) -> list:
        """List users with pagination."""
        if not hasattr(self, '_users'):
            self._users = []

        return self._users[offset:offset + limit]

    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role."""
        if not hasattr(self, '_users'):
            self._users = []

        for user in self._users:
            if user["id"] == user_id:
                user["role"] = role
                return True
        return False
