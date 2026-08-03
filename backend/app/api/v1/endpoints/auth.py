"""
Authentication endpoints for Azure AD OAuth2 integration.
Provides login, logout, token refresh, and user info endpoints.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Depends, HTTPException, Request, status
    from fastapi.responses import JSONResponse, RedirectResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.error("FastAPI not available - auth endpoints cannot be created")

from backend.app.services.azure.auth_service import (
    AzureAuthService,
    AuthenticationError,
    TokenValidationError,
    auth_service,
)
from backend.app.core.security import (
    validate_token,
    extract_user_from_token,
    get_current_user,
)

if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/auth", tags=["authentication"])

    # -------------------------------------------------------
    # Request/Response Models
    # -------------------------------------------------------

    class LoginRequest(BaseModel):
        """Login request body."""
        username: str = Field(..., description="User's email or username")
        password: str = Field(..., description="User's password")

    class LoginResponse(BaseModel):
        """Login response with tokens."""
        access_token: str = Field(..., description="JWT access token")
        refresh_token: Optional[str] = Field(None, description="Refresh token")
        id_token: Optional[str] = Field(None, description="ID token")
        token_type: str = Field(default="Bearer", description="Token type")
        expires_in: int = Field(default=3600, description="Token expiry in seconds")
        user: Optional[Dict[str, Any]] = Field(None, description="User information")

    class RefreshRequest(BaseModel):
        """Token refresh request body."""
        refresh_token: str = Field(..., description="Refresh token to exchange")

    class LogoutRequest(BaseModel):
        """Logout request body."""
        username: Optional[str] = Field(None, description="Username to log out")

    class TokenValidationRequest(BaseModel):
        """Token validation request body."""
        token: str = Field(..., description="Token to validate")

    # -------------------------------------------------------
    # Endpoints
    # -------------------------------------------------------

    @router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
    async def login(request: LoginRequest) -> LoginResponse:
        """
        Authenticate user with username and password via Azure AD.

        Returns access token, refresh token, and user information.
        """
        logger.info(f"Login attempt for user: {request.username}")
        try:
            result = auth_service.login(
                username=request.username,
                password=request.password,
            )

            user_info = None
            if result.get("access_token"):
                try:
                    user_info = extract_user_from_token(result["access_token"])
                except Exception:
                    user_info = result.get("account", {})

            return LoginResponse(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                id_token=result.get("id_token"),
                token_type=result.get("token_type", "Bearer"),
                expires_in=result.get("expires_in", 3600),
                user=user_info,
            )
        except AuthenticationError as e:
            logger.warning(f"Login failed for {request.username}: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Unexpected login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error",
            )

    @router.post("/authenticate", response_model=LoginResponse, status_code=status.HTTP_200_OK)
    async def authenticate(request: LoginRequest) -> LoginResponse:
        """
        Authenticate user - alias for /login endpoint.
        """
        return await login(request)

    @router.post("/logout", status_code=status.HTTP_200_OK)
    async def logout(
        request: Optional[LogoutRequest] = None,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """
        Logout the current user and invalidate their session.
        """
        username = current_user.get("username", "")
        logger.info(f"Logout request for user: {username}")

        try:
            account = {"username": username} if username else None
            result = auth_service.logout(account=account)
            return {"message": "Successfully logged out", "status": "success"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {"message": "Logout completed", "status": "success"}

    @router.post("/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
    async def refresh(request: RefreshRequest) -> LoginResponse:
        """
        Refresh access token using a valid refresh token.
        """
        logger.info("Token refresh request received")
        try:
            result = auth_service.refresh_token(
                refresh_token_value=request.refresh_token
            )

            user_info = None
            if result.get("access_token"):
                try:
                    user_info = extract_user_from_token(result["access_token"])
                except Exception:
                    user_info = result.get("account", {})

            return LoginResponse(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                id_token=result.get("id_token"),
                token_type=result.get("token_type", "Bearer"),
                expires_in=result.get("expires_in", 3600),
                user=user_info,
            )
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=e.message,
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed",
            )

    @router.get("/me", status_code=status.HTTP_200_OK)
    async def get_me(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """
        Get current authenticated user's information.
        """
        return current_user

    @router.post("/validate", status_code=status.HTTP_200_OK)
    async def validate(request: TokenValidationRequest) -> Dict[str, Any]:
        """
        Validate a JWT token and return its claims.
        """
        try:
            claims = validate_token(request.token)
            return {"valid": True, "claims": claims}
        except TokenValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    @router.get("/health", status_code=status.HTTP_200_OK)
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint for the auth service."""
        return {"status": "healthy", "service": "azure-auth"}

else:
    router = None
    logger.error("FastAPI not available - auth router not created")

__all__ = ["router"]
