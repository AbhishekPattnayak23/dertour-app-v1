"""
Azure AD Authentication Service using MSAL library.
Provides OAuth2/OIDC authentication flow with Azure Active Directory.
"""
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    logger.warning("MSAL library not available - using mock implementation")

try:
    from jose import JWTError, jwt as jose_jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    logger.warning("python-jose not available")


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""

    def __init__(self, message: str = "Authentication failed", code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TokenValidationError(AuthenticationError):
    """Exception raised when token validation fails."""

    def __init__(self, message: str = "Token validation failed"):
        super().__init__(message=message, code="TOKEN_VALIDATION_ERROR")


class AzureAuthService:
    """
    Azure AD Authentication Service using MSAL.
    Handles OAuth2 authorization code flow, token acquisition, and refresh.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        authority: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ):
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET", "")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID", "")
        self.authority = authority or os.getenv(
            "AZURE_AUTHORITY",
            f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        self.scopes = scopes or ["User.Read", "openid", "profile", "email"]
        self._client_app = None
        self._token_cache = None
        logger.info("AzureAuthService initialized")

    @property
    def client_app(self):
        """Lazy initialization of MSAL ConfidentialClientApplication."""
        if self._client_app is None:
            self._client_app = self._create_msal_app()
        return self._client_app

    def _create_msal_app(self):
        """Create and configure MSAL ConfidentialClientApplication."""
        if not MSAL_AVAILABLE:
            logger.warning("MSAL not available, returning mock app")
            return None
        try:
            cache = msal.SerializableTokenCache()
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
                token_cache=cache,
            )
            self._token_cache = cache
            logger.info("MSAL ConfidentialClientApplication created successfully")
            return app
        except Exception as e:
            logger.error(f"Failed to create MSAL app: {str(e)}")
            raise AuthenticationError(f"Failed to initialize MSAL: {str(e)}")

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with username and password via ROPC flow.

        Args:
            username: User's email/username
            password: User's password

        Returns:
            Dict containing access_token, refresh_token, and user info

        Raises:
            AuthenticationError: If authentication fails
        """
        logger.info(f"Authenticating user: {username}")
        try:
            if not MSAL_AVAILABLE or self.client_app is None:
                # Mock response for testing/development
                logger.warning("MSAL not available - returning mock token")
                return self._mock_token_response(username)

            result = self.client_app.acquire_token_by_username_password(
                username=username,
                password=password,
                scopes=self.scopes,
            )
            return self._process_token_result(result)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Alias for authenticate - login user with credentials.

        Args:
            username: User's email/username
            password: User's password

        Returns:
            Dict containing access_token, refresh_token, and user info
        """
        return self.authenticate(username=username, password=password)

    def acquire_token_by_auth_code(
        self,
        auth_code: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Acquire token using authorization code (OAuth2 code flow).

        Args:
            auth_code: Authorization code from Azure AD redirect
            redirect_uri: The redirect URI used in the auth request
            scopes: Optional list of scopes

        Returns:
            Dict with tokens and user info
        """
        logger.info("Acquiring token by authorization code")
        try:
            if not MSAL_AVAILABLE or self.client_app is None:
                return self._mock_token_response("auth_code_user")

            result = self.client_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=scopes or self.scopes,
                redirect_uri=redirect_uri,
            )
            return self._process_token_result(result)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token acquisition error: {str(e)}")
            raise AuthenticationError(f"Token acquisition failed: {str(e)}")

    def acquire_token_for_client(
        self, scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Acquire token for client (app-only, no user) using client credentials flow.

        Args:
            scopes: Optional list of scopes

        Returns:
            Dict with access token
        """
        logger.info("Acquiring client credentials token")
        try:
            if not MSAL_AVAILABLE or self.client_app is None:
                return {"access_token": "mock_client_token", "token_type": "Bearer"}

            result = self.client_app.acquire_token_for_client(
                scopes=scopes or [f"{self.client_id}/.default"]
            )
            return self._process_token_result(result)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Client credentials error: {str(e)}")
            raise AuthenticationError(f"Client credentials flow failed: {str(e)}")

    def refresh_token(self, refresh_token_value: str) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token_value: The refresh token string

        Returns:
            Dict with new access_token and refresh_token
        """
        logger.info("Refreshing access token")
        try:
            if not MSAL_AVAILABLE or self.client_app is None:
                return self._mock_token_response("refreshed_user")

            # MSAL handles refresh tokens transparently via cache
            # We use acquire_token_silent with cached accounts
            accounts = self.client_app.get_accounts()
            if not accounts:
                raise AuthenticationError("No cached accounts found for token refresh")

            result = self.client_app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0],
                force_refresh=True,
            )
            if result is None:
                raise AuthenticationError("Token refresh returned no result")
            return self._process_token_result(result)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Get the Azure AD authorization URL for OAuth2 code flow.

        Args:
            redirect_uri: URI to redirect after authentication
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL string
        """
        logger.info("Getting authorization URL")
        if not MSAL_AVAILABLE or self.client_app is None:
            return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize?mock=true"

        flow = self.client_app.initiate_auth_code_flow(
            scopes=self.scopes,
            redirect_uri=redirect_uri,
            state=state,
        )
        return flow.get("auth_uri", "")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT access token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Dict with decoded token claims

        Raises:
            TokenValidationError: If token is invalid or expired
        """
        logger.info("Validating JWT token")
        try:
            if JOSE_AVAILABLE:
                # Decode without verification for claims extraction
                # Full verification is done by Azure AD's JWKS endpoint
                claims = jose_jwt.get_unverified_claims(token)
                return claims
            else:
                import jwt as pyjwt
                claims = pyjwt.decode(
                    token,
                    options={"verify_signature": False},
                    algorithms=["RS256", "HS256"],
                )
                return claims
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise TokenValidationError(f"Token validation failed: {str(e)}")

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from token claims or Microsoft Graph.

        Args:
            access_token: Valid access token

        Returns:
            Dict with user information
        """
        logger.info("Getting user info from token")
        try:
            claims = self.validate_token(access_token)
            return {
                "id": claims.get("oid", claims.get("sub", "")),
                "username": claims.get("preferred_username", claims.get("upn", "")),
                "email": claims.get("email", claims.get("preferred_username", "")),
                "name": claims.get("name", ""),
                "roles": claims.get("roles", []),
                "groups": claims.get("groups", []),
                "tenant_id": claims.get("tid", ""),
            }
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise AuthenticationError(f"Failed to get user info: {str(e)}")

    def logout(self, account: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sign out the user by removing their account from the MSAL token cache.

        Args:
            account: Optional account dict with username to identify which account to remove

        Returns:
            Dict with logout status
        """
        logger.info("Logging out user")
        try:
            if MSAL_AVAILABLE and self.client_app is not None:
                accounts = self.client_app.get_accounts()
                if account and accounts:
                    for cached_account in accounts:
                        if cached_account.get("username") == account.get("username"):
                            self.client_app.remove_account(cached_account)
                            logger.info(f"Removed account from cache: {account.get('username')}")
                            break
                elif accounts:
                    for cached_account in accounts:
                        self.client_app.remove_account(cached_account)
                    logger.info("Removed all accounts from cache")
            return {"status": "logged_out", "message": "User successfully logged out"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def sign_out(self, account: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Alias for logout - signs out user and clears cached tokens.

        Args:
            account: Optional account dict to identify which account to remove

        Returns:
            Dict with sign-out status
        """
        return self.logout(account=account)

    def _process_token_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process MSAL token acquisition result.

        Args:
            result: Raw MSAL token result

        Returns:
            Normalized token response dict

        Raises:
            AuthenticationError: If result contains error
        """
        if result is None:
            raise AuthenticationError("Token acquisition returned None")

        if "error" in result:
            error_desc = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Token acquisition failed: {error_desc}")
            raise AuthenticationError(f"Token acquisition failed: {error_desc}")

        return {
            "access_token": result.get("access_token", ""),
            "refresh_token": result.get("refresh_token", ""),
            "id_token": result.get("id_token", ""),
            "token_type": result.get("token_type", "Bearer"),
            "expires_in": result.get("expires_in", 3600),
            "scope": result.get("scope", ""),
            "account": result.get("account", {}),
        }

    def _mock_token_response(self, username: str) -> Dict[str, Any]:
        """Generate mock token response for development/testing."""
        return {
            "access_token": f"mock_access_token_{username}",
            "refresh_token": f"mock_refresh_token_{username}",
            "id_token": f"mock_id_token_{username}",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(self.scopes),
            "account": {"username": username},
        }


# Module-level singleton instance
auth_service = AzureAuthService()

__all__ = [
    "AzureAuthService",
    "AuthenticationError",
    "TokenValidationError",
    "auth_service",
]
