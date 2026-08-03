"""Authentication and security middleware for Azure AD integration."""

from typing import Any, Dict, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request
from jose import JWTError, jwt
from msal import ConfidentialClientApplication
from ..config.settings import settings


security = HTTPBearer()


class AzureADAuth:
    """Azure AD authentication handler."""

    def __init__(self):
        self.app = ConfidentialClientApplication(
            settings.AZURE_AD_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/"
                      f"{settings.AZURE_AD_TENANT_ID}",
            client_credential=settings.AZURE_AD_CLIENT_SECRET,
        )


async def verify_azure_ad_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify Azure AD token and extract user information."""
    token = credentials.credentials

    try:
        # Decode JWT token without verification for development
        # In production, implement proper Azure AD JWT verification
        payload = jwt.get_unverified_claims(token)

        username: str = payload.get("preferred_username")
        user_id: str = payload.get("oid")
        roles: List[str] = payload.get("roles", [])

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "username": username,
            "user_id": user_id,
            "roles": roles,
            "token": token
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_data: Dict[str, Any] = Depends(verify_azure_ad_token)
):
    """Get current authenticated user."""
    return {
        "id": user_data["user_id"],
        "username": user_data["username"],
        "roles": user_data["roles"]
    }


async def require_role(required_role: str):
    """Dependency to require specific role."""
    def role_checker(
        user_data: Dict[str, Any] = Depends(verify_azure_ad_token)
    ):
        user_roles = user_data.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. "
                       f"Required role: {required_role}"
            )
        return user_data
    return role_checker


async def require_admin(
    user_data: Dict[str, Any] = Depends(require_role("Admin"))
):
    """Require admin role."""
    return user_data


class SecurityMiddleware:
    """Security middleware for request processing."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    headers[b"x-content-type-options"] = b"nosniff"
                    headers[b"x-frame-options"] = b"DENY"
                    headers[b"x-xss-protection"] = b"1; mode=block"
                    message["headers"] = list(headers.items())
                await send(message)
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


async def validate_api_key(request: Request):
    """Validate API key for internal service calls."""
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True
