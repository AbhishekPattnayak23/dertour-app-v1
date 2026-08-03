"""
Authentication endpoints for Azure AD OAuth2 integration.
Provides login, logout, token refresh, and user info endpoints.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Depends, HTTPException, Request, status
    from fastapi.responses import JSONResponse, RedirectResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.error("FastAPI not available - auth endpoints cannot be created")

try:
    from backend.app.services.azure.auth_service import (
        AzureAuthService,
        AuthenticationError,
        TokenValidationError,
        auth_service,
    )
    AZURE_AUTH_AVAILABLE = True
except ImportError:
    try:
        from app.services.azure.auth_service import AzureAuthService
        AZURE_AUTH_AVAILABLE = False
    except ImportError:
        AZURE_AUTH_AVAILABLE = False

try:
    from backend.app.core.security import (
        validate_token,
        extract_user_from_token,
        get_current_user as azure_get_current_user,
    )
    SECURITY_MODULE_AVAILABLE = True
except ImportError:
    SECURITY_MODULE_AVAILABLE = False

try:
    from app.core.database import get_db
    from app.models.user import User
    from app.schemas.auth import Token, UserProfile, LoginRequest as LegacyLoginRequest
    LEGACY_DB_AVAILABLE = True
except ImportError:
    LEGACY_DB_AVAILABLE = False

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)
security_bearer = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any],
                        expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


if LEGACY_DB_AVAILABLE:
    def get_user_by_email(db: Session, email: str) -> Optional[Any]:
        return db.query(User).filter(User.email == email).first()

    def authenticate_user(db: Session, email: str,
                          password: str) -> Optional[Any]:
        user = get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_current_user_legacy(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> Any:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not credentials:
            raise credentials_exception

        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY,
                                 algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = get_user_by_email(db, email=email)
        if user is None:
            raise credentials_exception
        return user


if FASTAPI_AVAILABLE:
    router = APIRouter()

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

    if AZURE_AUTH_AVAILABLE and SECURITY_MODULE_AVAILABLE:

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
            current_user: Dict[str, Any] = Depends(azure_get_current_user),
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
                )
            except Exception as e:
                logger.error(f"Token refresh error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Token refresh failed",
                )

        @router.get("/profile")
        async def get_profile(
            current_user: Dict[str, Any] = Depends(azure_get_current_user)
        ) -> Dict[str, Any]:
            """Get user profile."""
            return current_user

    else:
        # Fallback endpoints if Azure auth is not available
        @router.post("/login")
        async def login():
            """User login endpoint."""
            return {"message": "Login endpoint"}

        @router.post("/logout")
        async def logout():
            """User logout endpoint."""
            return {"message": "Logout endpoint"}

        @router.get("/profile")
        async def get_profile():
            """Get user profile."""
            return {"message": "Profile endpoint"}

    # Legacy endpoints for backward compatibility
    if LEGACY_DB_AVAILABLE:
        @router.post("/login/legacy", response_model=Token)
        async def login_legacy(login_data: LegacyLoginRequest, db: Session = Depends(get_db)):
            user = authenticate_user(db, login_data.email, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}

        @router.get("/me", response_model=UserProfile)
        async def get_current_user_profile(
            current_user: User = Depends(get_current_user_legacy)
        ):
            return UserProfile(
                id=current_user.id,
                email=current_user.email,
                name=current_user.name,
                role=current_user.role,
                department=current_user.department
            )

        @router.post("/refresh/legacy", response_model=Token)
        async def refresh_token_legacy(current_user: User = Depends(get_current_user_legacy)):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": current_user.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
else:
    # Fallback if FastAPI is not available
    router = None
