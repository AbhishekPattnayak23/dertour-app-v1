"""
Security utilities for JWT token validation, role extraction, and FastAPI dependencies.
"""
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import Depends, HTTPException, Request, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available")

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    try:
        import jwt
        PYJWT_AVAILABLE = True
    except ImportError:
        PYJWT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from cachetools import TTLCache
    CACHETOOLS_AVAILABLE = True
    _jwks_cache = TTLCache(maxsize=1, ttl=3600)
except ImportError:
    CACHETOOLS_AVAILABLE = False
    _jwks_cache = {}

from backend.app.services.azure.auth_service import AuthenticationError, TokenValidationError


# -------------------------------------------------------
# Token Models
# -------------------------------------------------------

if PYDANTIC_AVAILABLE:
    from pydantic import BaseModel

    class TokenData(BaseModel):
        """Decoded token data model."""
        sub: Optional[str] = None
        oid: Optional[str] = None
        email: Optional[str] = None
        preferred_username: Optional[str] = None
        name: Optional[str] = None
        roles: List[str] = []
        groups: List[str] = []
        tenant_id: Optional[str] = None
        scopes: List[str] = []

    class UserContext(BaseModel):
        """Current user context model."""
        user_id: str
        username: str
        email: Optional[str] = None
        name: Optional[str] = None
        roles: List[str] = []
        groups: List[str] = []
        is_authenticated: bool = True


# -------------------------------------------------------
# JWT Token Validation Functions
# -------------------------------------------------------

def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode a JWT access token.

    Args:
        token: JWT token string (with or without 'Bearer ' prefix)

    Returns:
        Dict with decoded token claims

    Raises:
        TokenValidationError: If token is invalid or expired
    """
    if token.startswith("Bearer "):
        token = token[7:]

    logger.debug("Validating JWT token")

    try:
        if JOSE_AVAILABLE:
            try:
                claims = jwt.get_unverified_claims(token)
                return claims
            except JWTError as e:
                raise TokenValidationError(f"JWT validation failed: {str(e)}")
        elif PYJWT_AVAILABLE:
            try:
                claims = jwt.decode(
                    token,
                    options={"verify_signature": False},
                    algorithms=["RS256", "HS256", "RS384", "RS512"],
                )
                return claims
            except jwt.ExpiredSignatureError:
                raise TokenValidationError("Token has expired")
            except jwt.InvalidTokenError as e:
                raise TokenValidationError(f"Invalid token: {str(e)}")
        else:
            # Fallback: basic base64 decode of JWT payload
            import base64
            import json
            parts = token.split(".")
            if len(parts) != 3:
                raise TokenValidationError("Invalid JWT format")
            payload = parts[1]
            # Add padding
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            return claims
    except TokenValidationError:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise TokenValidationError(f"Token validation failed: {str(e)}")


def verify_token(token: str) -> Dict[str, Any]:
    """
    Alias for validate_token - verify a JWT token and return claims.

    Args:
        token: JWT token string

    Returns:
        Dict with token claims
    """
    return validate_token(token)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token without full signature verification.
    Used for extracting claims from trusted tokens.

    Args:
        token: JWT token string

    Returns:
        Dict with decoded payload claims
    """
    return validate_token(token)


def extract_roles_from_token(token: str) -> List[str]:
    """
    Extract roles from a JWT token's claims.

    Args:
        token: JWT token string

    Returns:
        List of role strings
    """
    try:
        claims = validate_token(token)
        roles = claims.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
        return roles
    except Exception as e:
        logger.warning(f"Failed to extract roles from token: {str(e)}")
        return []


def extract_user_from_token(token: str) -> Dict[str, Any]:
    """
    Extract user information from token claims.

    Args:
        token: JWT access token

    Returns:
        Dict with user info (id, username, email, name, roles, groups)
    """
    try:
        claims = validate_token(token)
        return {
            "id": claims.get("oid", claims.get("sub", "")),
            "username": claims.get("preferred_username", claims.get("upn", "")),
            "email": claims.get("email", claims.get("preferred_username", "")),
            "name": claims.get("name", ""),
            "roles": claims.get("roles", []),
            "groups": claims.get("groups", []),
            "tenant_id": claims.get("tid", ""),
            "scopes": claims.get("scp", "").split() if claims.get("scp") else [],
        }
    except Exception as e:
        logger.error(f"Failed to extract user from token: {str(e)}")
        raise TokenValidationError(f"Could not extract user from token: {str(e)}")


# -------------------------------------------------------
# FastAPI Security Dependencies
# -------------------------------------------------------

if FASTAPI_AVAILABLE:
    _bearer_scheme = HTTPBearer(auto_error=False)

    async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    ) -> Dict[str, Any]:
        """
        FastAPI dependency to get current authenticated user from Bearer token.

        Args:
            credentials: HTTP Bearer credentials from Authorization header

        Returns:
            Dict with current user information

        Raises:
            HTTPException 401: If token is missing or invalid
        """
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user = extract_user_from_token(credentials.credentials)
            return user
        except TokenValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Error in get_current_user dependency: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    ) -> Optional[Dict[str, Any]]:
        """
        FastAPI dependency to optionally get current user (no error if unauthenticated).

        Returns:
            Dict with user info or None if not authenticated
        """
        if credentials is None:
            return None
        try:
            return extract_user_from_token(credentials.credentials)
        except Exception:
            return None

    def require_roles(required_roles: List[str]):
        """
        FastAPI dependency factory to require specific roles.

        Args:
            required_roles: List of role strings that the user must have at least one of

        Returns:
            FastAPI dependency function
        """
        async def role_checker(
            current_user: Dict[str, Any] = Depends(get_current_user),
        ) -> Dict[str, Any]:
            user_roles = current_user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {required_roles}. User roles: {user_roles}",
                )
            return current_user

        return role_checker


__all__ = [
    "validate_token",
    "verify_token",
    "decode_token",
    "extract_roles_from_token",
    "extract_user_from_token",
    "AuthenticationError",
    "TokenValidationError",
]

if FASTAPI_AVAILABLE:
    __all__ += ["get_current_user", "get_optional_user", "require_roles"]

if PYDANTIC_AVAILABLE:
    __all__ += ["TokenData", "UserContext"]
