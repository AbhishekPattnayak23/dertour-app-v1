from typing import Optional, List, Tuple
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

    def _get_model(self):
        """Lazily import User model to avoid circular imports."""
        try:
            from app.models.user import User as UserModel
            return UserModel
        except ImportError:
            try:
                from app.db.models.user import User as UserModel
                return UserModel
            except ImportError:
                return None

    # -------------------------------------------------------------------------
    # asyncpg-based methods
    # -------------------------------------------------------------------------

    async def create_user(
        self,
        email: str = None,
        username: str = None,
        hashed_password: str = None,
        is_active: bool = True,
        is_superuser: bool = False,
        roles: Optional[List[str]] = None,
        user_data: dict = None,
    ) -> dict:
        # Support dict-based creation (from THEIRS) when pool is not available
        if self._pool is None:
            if user_data is not None:
                return self._create_user_orm(user_data)
            data = {
                "email": email,
                "username": username,
                "hashed_password": hashed_password,
                "is_active": is_active,
                "is_superuser": is_superuser,
                "roles": roles or [],
            }
            return self._create_user_orm(data)

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

    def _create_user_orm(self, user_data: dict):
        """Internal helper: create user via SQLAlchemy ORM."""
        UserModel = self._get_model()
        if UserModel is None:
            user_id = len(getattr(self, '_users', [])) + 1
            if not hasattr(self, '_users'):
                self._users = []
            new_user = {
                "id": user_id,
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "role": user_data.get("role", "user"),
                "profile": user_data.get("profile", {}),
            }
            self._users.append(new_user)
            return new_user

        user = UserModel(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create(self, user_data: dict):
        """Create a new user record (ORM-based)."""
        return self._create_user_orm(user_data)

    async def get_by_id(self, user_id) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    str(user_id),
                )
            return dict(row) if row else None
        # SQLAlchemy fallback (sync)
        UserModel = self._get_model()
        if UserModel is None:
            return None
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    async def get_by_email(self, email: str) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1",
                    email.lower().strip(),
                )
            return dict(row) if row else None
        UserModel = self._get_model()
        if UserModel is None:
            return None
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    async def get_by_username(self, username: str) -> Optional[dict]:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1",
                    username.strip(),
                )
            return dict(row) if row else None
        UserModel = self._get_model()
        if UserModel is None:
            return None
        return self.db.query(UserModel).filter(UserModel.username == username).first()

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

        # In-memory / ORM fallback
        if not hasattr(self, '_users'):
            self._users = []
        return self._users[offset:offset + limit]

    async def update_user(self, user_id, **fields) -> Optional[dict]:
        if self._pool is not None:
            if not fields:
                return await self.get_by_id(user_id)

            now = datetime.now(timezone.utc)
            fields["updated_at"] = now

            set_clauses = []
            values = []
            for idx, (key, value) in enumerate(fields.items(), start=1):
                set_clauses.append(f"{key} = ${idx}")
                values.append(value)

            values.append(str(user_id))
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

        # In-memory fallback
        if not hasattr(self, '_users'):
            self._users = []
        for user in self._users:
            if user["id"] == user_id:
                user.update(fields)
                return user
        return None

    def update(self, user_id, update_data: dict):
        """Update an existing user record (ORM-based)."""
        UserModel = self._get_model()
        if UserModel is None:
            if not hasattr(self, '_users'):
                self._users = []
            for user in self._users:
                if user["id"] == user_id:
                    user.update(update_data)
                    return user
            return None

        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

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

    async def delete_user(self, user_id) -> bool:
        if self._pool is not None:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM users WHERE id = $1",
                    str(user_id),
                )
            return result == "DELETE 1"

        # In-memory fallback
        if not hasattr(self, '_users'):
            self._users = []
        for i, user in enumerate(self._users):
            if user["id"] == user_id:
                del self._users[i]
                return True
        return False

    def delete(self, user_id) -> bool:
        """Delete a user record (ORM-based)."""
        UserModel = self._get_model()
        if UserModel is None:
            return self._delete_inmemory(user_id)

        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def _delete_inmemory(self, user_id) -> bool:
        if not hasattr(self, '_users'):
            self._users = []
        for i, user in enumerate(self._users):
            if user["id"] == user_id:
                del self._users[i]
                return True
        return False

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
                    user_id, plan, features, expires_at, metadata,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $6)
                ON CONFLICT (user_id) DO UPDATE
                SET plan = EXCLUDED.plan,
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
    # ORM / sync convenience methods (from THEIRS)
    # -------------------------------------------------------------------------

    def get_users_filtered(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List, int]:
        """Get users with optional filters, returning (users, total_count)."""
        UserModel = self._get_model()
        if UserModel is None:
            return [], 0

        query = self.db.query(UserModel)

        if role is not None:
            query = query.filter(UserModel.role == role)

        if is_active is not None:
            query = query.filter(UserModel.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                UserModel.email.ilike(search_term) |
                UserModel.username.ilike(search_term) |
                UserModel.full_name.ilike(search_term)
            )

        total = query.count()
        users = query.offset(skip).limit(limit).all()

        return users, total

    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        UserModel = self._get_model()
        if UserModel is None:
            return False
        return self.db.query(UserModel).filter(UserModel.email == email).first() is not None

    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        UserModel = self._get_model()
        if UserModel is None:
            return False
        return self.db.query(UserModel).filter(UserModel.username == username).first() is not None

    def get_user_stats(self) -> dict:
        """Get aggregate statistics about users."""
        UserModel = self._get_model()
        if UserModel is None:
            return {"total": 0, "active": 0, "inactive": 0}

        total = self.db.query(UserModel).count()
        active = self.db.query(UserModel).filter(
            UserModel.is_active == True).count()
        inactive = total - active

        role_counts = {}
        try:
            rows = (
                self.db.query(UserModel.role, UserModel.id)
                .group_by(UserModel.role)
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

    def update_user_role(self, user_id, role: str) -> bool:
        """Update user role (in-memory or ORM)."""
        if not hasattr(self, '_users'):
            self._users = []

        for user in self._users:
            if user["id"] == user_id:
                user["role"] = role
                return True

        # Try ORM
        UserModel = self._get_model()
        if UserModel is not None and self.db is not None:
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                user.role = role
                self.db.commit()
                return True

        return False
