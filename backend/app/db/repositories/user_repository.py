from typing import Optional, List
import uuid
from datetime import datetime, timezone

import asyncpg


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

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
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id,
            )
        return dict(row) if row else None

    async def get_by_email(self, email: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email.lower().strip(),
            )
        return dict(row) if row else None

    async def get_by_username(self, username: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1",
                username.strip(),
            )
        return dict(row) if row else None

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> List[dict]:
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
                SET roles = array_append(
                    CASE WHEN $2 = ANY(roles) THEN roles
                         ELSE roles END,
                    CASE WHEN $2 = ANY(roles) THEN NULL
                         ELSE $2 END
                ),
                updated_at = $3
                WHERE id = $1
                RETURNING *
                """,
                user_id,
                role,
                now,
            )
            if not row:
                return None
            # Simpler approach: use array union
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

    async def has_feature(self, user_id: str, feature: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT features, expires_at
                FROM user_entitlements
                WHERE user_id = $1
                """,
                user_id,
            )
        if not row:
            return False
        expires_at = row["expires_at"]
        if expires_at and expires_at < datetime.now(timezone.utc):
            return False
        return feature in (row["features"] or [])

    async def count_users(self, is_active: Optional[bool] = None) -> int:
        query = "SELECT COUNT(*) FROM users"
        params: list = []

        if is_active is not None:
            params.append(is_active)
            query += f" WHERE is_active = ${len(params)}"

        async with self._pool.acquire() as conn:
            result = await conn.fetchval(query, *params)
        return result or 0

    async def email_exists(self, email: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1)",
                email.lower().strip(),
            )
        return bool(result)

    async def username_exists(self, username: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username = $1)",
                username.strip(),
            )
        return bool(result)

    async def search_users(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[dict]:
        search_term = f"%{query.strip()}%"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM users
                WHERE
                    email ILIKE $1 OR
                    username ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                search_term,
                limit,
                offset,
            )
        return [dict(row) for row in rows]

    async def get_users_by_role(
        self,
        role: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM users
                WHERE $1 = ANY(roles) AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                role,
                limit,
                offset,
            )
        return [dict(row) for row in rows]

    async def bulk_deactivate(self, user_ids: List[str]) -> int:
        if not user_ids:
            return 0
        now = datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users
                SET is_active = FALSE, updated_at = $1
                WHERE id = ANY($2::uuid[])
                """,
                now,
                user_ids,
            )
        try:
            return int(result.split()[-1])
        except (IndexError, ValueError):
            return 0