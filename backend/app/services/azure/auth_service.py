"""
Azure AD authentication service with proper error handling
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    from jose import jwt, JWTError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("python-jose not available, using mock tokens")

try:
    from itsdangerous import URLSafeTimedSerializer
    ITSDANGEROUS_AVAILABLE = True
except ImportError:
    ITSDANGEROUS_AVAILABLE = False
    logging.warning("itsdangerous not available, using simple tokens")

logger = logging.getLogger(__name__)

class AzureAuthService:
    def __init__(self):
        self.secret_key = "dev-secret-key-change-in-production"
        if ITSDANGEROUS_AVAILABLE:
            self.serializer = URLSafeTimedSerializer(self.secret_key)
        else:
            self.serializer = None

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        if JWT_AVAILABLE:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(hours=24)
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        else:
            # Fallback to simple token for development
            import json
            import base64
            token_data = {**data, "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()}
            return base64.b64encode(json.dumps(token_data).encode()).decode()

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            if JWT_AVAILABLE:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                return payload
            else:
                # Fallback verification
                import json
                import base64
                decoded = json.loads(base64.b64decode(token).decode())
                exp_str = decoded.get("exp")
                if exp_str:
                    exp_time = datetime.fromisoformat(exp_str)
                    if datetime.utcnow() > exp_time:
                        return None
                return decoded
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    def get_mock_user_profile(self, email: str = "sarah.chen@dertour.com") -> Dict[str, Any]:
        """Get mock user profile for development"""
        return {
            "email": email,
            "name": "Sarah Chen",
            "role": "Travel Advisor",
            "department": "European Destinations",
            "authenticated": True
        }
