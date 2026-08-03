from typing import Optional, List
import uuid
from datetime import datetime, timezone

import asyncpg

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

try:
    from app.db.models.user import User
    from app.core.security import get_password_hash, verify_password
    from app.schemas.user import UserCreate, UserUpdate
    from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
    _sqlalchemy_available = True
except ImportError:
    _sqlalchemy_available = False


class UserRepository:
    """
    Unified UserRepository supporting both asyncpg (raw SQL) and SQLAlchemy ORM patterns.
    """

    def __init__(self, db=None, pool: asyncpg.Pool = None):
        self.db = db
        self._pool = pool

    # -------------------------------------------------------------------------
    # asyncpg-based methods
    # -------------------------------------------------------------------------

    async def create_user(
        self,
        email: str,
        username: str,
        hashed_password: str,
        is_active: bool = True,
        is_superuser: bool = False,
        roles: Optional[List[str]] = None,
    ) -> dict:
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        roles = roles or []

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (
                    id, email, username, hashed_password,
                    is_active, is_superuser, roles,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                user_id,
                email.lower().strip(),
                username.strip(),
                hashed_password,
                is_active,
                is_superuser,
                roles,
                now,
                now,
            )
        return dict(row)

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    user_id,
                )
            return dict(row) if row else None
        # SQLAlchemy fallback (sync)
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_by_email(self, email: str) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1",
                    email.lower().strip(),
                )
            return dict(row) if row else None
        return self.db.query(User).filter(User.email == email).first()

    async def get_by_username(self, username: str) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1",
                    username.strip(),
                )
            return dict(row) if row else None
        return self.db.query(User).filter(User.username == username).first()

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> List[dict]:
        if self._pool is not None:
            query = "SELECT * FROM users"
            params: list = []
            conditions: List[str] = []

            if is_active is not None:
                params.append(is_active)
                conditions.append(f"is_active = ${len(params)}")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            params.append(limit)
            query += f" ORDER BY created_at DESC LIMIT ${len(params)}"
            params.append(offset)
            query += f" OFFSET ${len(params)}"

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
        # SQLAlchemy fallback
        return self.get_users(skip=offset, limit=limit)

    async def update_user(self, user_id: str, **fields) -> Optional[dict]:
        if not fields:
            return await self.get_by_id(user_id)

        now = datetime.now(timezone.utc)
        fields["updated_at"] = now

        set_clauses = []
        values = []
        for idx, (key, value) in enumerate(fields.items(), start=1):
            set_clauses.append(f"{key} = ${idx}")
            values.append(value)

        values.append(user_id)
        where_param = f"${len(values)}"

        query = f"""
            UPDATE users
            SET {', '.join(set_clauses)}
            WHERE id = {where_param}
            RETURNING *
        """

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
        return dict(row) if row else None

    async def update_password(self, user_id: str, hashed_password: str) -> bool:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                SET hashed_password = $1, updated_at = $2
                WHERE id = $3
                """,
                hashed_password,
                now,
                user_id,
            )
        return result == "UPDATE 1"

    async def update_last_login(self, user_id: str) -> bool:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                SET last_login_at = $1, updated_at = $1
                WHERE id = $2
                """,
                now,
                user_id,
            )
        return result == "UPDATE 1"

    async def deactivate_user(self, user_id: str) -> bool:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                SET is_active = FALSE, updated_at = $1
                WHERE id = $2
                """,
                now,
                user_id,
            )
        return result == "UPDATE 1"

    async def activate_user(self, user_id: str) -> bool:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                SET is_active = TRUE, updated_at = $1
                WHERE id = $2
                """,
                now,
                user_id,
            )
        return result == "UPDATE 1"

    async def delete_user(self, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM users WHERE id = $1",
                user_id,
            )
        return result == "DELETE 1"

    async def add_role(self, user_id: str, role: str) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users
                SET roles = (
                    SELECT array_agg(DISTINCT r)
                    FROM unnest(array_append(roles, $2)) AS r
                ),
                updated_at = $3
                WHERE id = $1
                RETURNING *
                """,
                user_id,
                role,
                now,
            )
        return dict(row) if row else None

    async def remove_role(self, user_id: str, role: str) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users
                SET roles = array_remove(roles, $2),
                    updated_at = $3
                WHERE id = $1
                RETURNING *
                """,
                user_id,
                role,
                now,
            )
        return dict(row) if row else None

    async def set_roles(self, user_id: str, roles: List[str]) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users
                SET roles = $2, updated_at = $3
                WHERE id = $1
                RETURNING *
                """,
                user_id,
                roles,
                now,
            )
        return dict(row) if row else None

    async def has_role(self, user_id: str, role: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT roles FROM users WHERE id = $1",
                user_id,
            )
        if not row:
            return False
        return role in (row["roles"] or [])

    async def get_entitlements(self, user_id: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT ue.*
                FROM user_entitlements ue
                WHERE ue.user_id = $1
                """,
                user_id,
            )
        return dict(row) if row else None

    async def upsert_entitlements(
        self,
        user_id: str,
        plan: str,
        features: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        features = features or []
        metadata = metadata or {}

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_entitlements (
                    user_id, plan, features, expires_at,
                    metadata, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $6)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    plan = EXCLUDED.plan,
                    features = EXCLUDED.features,
                    expires_at = EXCLUDED.expires_at,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                user_id,
                plan,
                features,
                expires_at,
                metadata,
                now,
            )
        return dict(row)

    # -------------------------------------------------------------------------
    # SQLAlchemy ORM-based methods (sync)
    # -------------------------------------------------------------------------

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """Get all users with pagination (SQLAlchemy)"""
        return self.db.query(User).offset(skip).limit(limit).all()

    def get_all(self, skip: int = 0, limit: int = 100) -> List:
        """Get all users - alias for get_users method"""
        return self.get_users(skip=skip, limit=limit)

    def get_users_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """Get users by role (SQLAlchemy)"""
        return self.db.query(User).filter(
            and_(User.role == role, User.is_active == True)
        ).offset(skip).limit(limit).all()

    def create(self, user_data) -> "User":
        """Create a new user (SQLAlchemy)"""
        existing = self.db.query(User).filter(User.email == user_data.email).first()
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

    def update(self, user_id: int, user_data) -> "User":
        """Update an existing user (SQLAlchemy)"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        update_data = user_data.dict(exclude_unset=True) if hasattr(user_data, 'dict') else user_data
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
        """Delete a user by ID (SQLAlchemy)"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        self.db.delete(db_user)
        self.db.commit()
        return True

    def soft_delete(self, user_id: int) -> "User":
        """Soft delete a user by setting is_active to False (SQLAlchemy)"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        db_user.is_active = False
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def assign_role(self, user_id: int, role: str) -> "User":
        """Assign a role to a user (SQLAlchemy)"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        db_user.role = role
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_entitlements(self, user_id: int, entitlements: List[str]) -> "User":
        """Update user entitlements/permissions (SQLAlchemy)"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
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
    ) -> List:
        """Search users by email or username (SQLAlchemy)"""
        return self.db.query(User).filter(
            or_(
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit).all()

    def count_users(self) -> int:
        """Count total number of users (SQLAlchemy)"""
        return self.db.query(User).count()

    def count_active_users(self) -> int:
        """Count active users (SQLAlchemy)"""
        return self.db.query(User).filter(User.is_active == True).count()

    # -------------------------------------------------------------------------
    # Profile Data Storage Methods
    # -------------------------------------------------------------------------

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Retrieve user profile data by user ID."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        if isinstance(user, dict):
            profile = {
                "user_id": str(user.get("id", user_id)),
                "username": user.get("username"),
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "profile_picture": user.get("profile_picture"),
                "bio": user.get("bio"),
                "preferences": user.get("preferences", {}),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at"),
            }
        else:
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
        if self._pool is not None:
            updated_user = await self.update_user(user_id, **update_data)
        else:
            updated_user = self.update(user_id, type('obj', (object,), {'dict': lambda self, **kw: update_data, **update_data})())
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
            user = await self.get_by_username(username)
            if user is None:
                return None
            user_id = user.get("id") if isinstance(user, dict) else str(user.id)
            return await self.get_user_profile(str(user_id))
        except Exception:
            return None

    async def get_UserProfile(self, user_id: str) -> Optional[dict]:
        """Alias for get_user_profile for compatibility."""
        return await self.get_user_profile(user_id)

    async def save_user_profile_data(self, user_id: str, profile: dict) -> bool:
        """Persist user_profile data to storage."""
        result = await self.store_user_profile(user_id, profile)
        return result is not None
