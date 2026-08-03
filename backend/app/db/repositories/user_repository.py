from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from app.db.models.user import User
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()


    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users - alias for get_users method"""
        return self.get_users(skip=skip, limit=limit)

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users - another alias for get_users method"""
        return self.get_users(skip=skip, limit=limit)
    def get_users_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by role"""
        return self.db.query(User).filter(
            and_(User.role == role, User.is_active == True)
        ).offset(skip).limit(limit).all()

    def create(self, user_data: UserCreate) -> User:
        """Create a new user"""
        existing = self.get_by_email(user_data.email)
        if existing:
            raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")

        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=getattr(user_data, 'full_name', None),
            role=getattr(user_data, 'role', 'user'),
            is_active=True,
        )
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError(f"User with email {user_data.email} already exists")

    def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Update an existing user"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        update_data = user_data.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)

        try:
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError("Email already in use")

    def delete(self, user_id: int) -> bool:
        """Delete a user by ID"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        self.db.delete(db_user)
        self.db.commit()
        return True

    def soft_delete(self, user_id: int) -> User:
        """Soft delete a user by setting is_active to False"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def assign_role(self, user_id: int, role: str) -> User:
        """Assign a role to a user"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        db_user.role = role
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_entitlements(self, user_id: int, entitlements: List[str]) -> User:
        """Update user entitlements/permissions"""
        db_user = self.get_by_id(user_id)
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        if hasattr(db_user, 'entitlements'):
            db_user.entitlements = entitlements
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by email or username"""
        return self.db.query(User).filter(
            or_(
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit).all()

    def count_users(self) -> int:
        """Count total number of users"""
        return self.db.query(User).count()

    def count_active_users(self) -> int:
        """Count active users"""
        return self.db.query(User).filter(User.is_active == True).count()

    # --- Profile Data Storage Methods ---

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Retrieve user profile data by user ID."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        profile = {
            "user_id": str(user.id),
            "username": getattr(user, "username", None),
            "email": getattr(user, "email", None),
            "full_name": getattr(user, "full_name", None),
            "profile_picture": getattr(user, "profile_picture", None),
            "bio": getattr(user, "bio", None),
            "preferences": getattr(user, "preferences", {}),
            "created_at": getattr(user, "created_at", None),
            "updated_at": getattr(user, "updated_at", None),
        }
        return profile

    async def update_user_profile(self, user_id: str, profile_data: dict) -> Optional[dict]:
        """Update user profile data."""
        profile_fields = {
            "full_name", "profile_picture", "bio", "preferences", "phone_number", "address"
        }
        update_data = {k: v for k, v in profile_data.items() if k in profile_fields}
        updated_user = await self.update(user_id, update_data)
        if updated_user is None:
            return None
        return await self.get_user_profile(user_id)

    async def store_user_profile(self, user_id: str, profile_data: dict) -> Optional[dict]:
        """Store/upsert user profile information."""
        existing = await self.get_by_id(user_id)
        if existing is None:
            return None
        return await self.update_user_profile(user_id, profile_data)

    async def get_profile_by_username(self, username: str) -> Optional[dict]:
        """Retrieve user profile by username."""
        try:
            user = await self.db.execute(
                self.model.__table__.select().where(
                    self.model.username == username
                )
            )
            result = user.fetchone()
            if result is None:
                return None
            return await self.get_user_profile(str(result.id))
        except Exception:
            return None

    # UserProfile convenience alias
    async def get_UserProfile(self, user_id: str) -> Optional[dict]:
        """Alias for get_user_profile for compatibility."""
        return await self.get_user_profile(user_id)

    async def save_user_profile_data(self, user_id: str, profile: dict) -> bool:
        """Persist user_profile data to storage."""
        result = await self.store_user_profile(user_id, profile)
        return result is not None
