from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class EntitlementType(str, Enum):
    FEATURE = "feature"
    RESOURCE = "resource"
    PERMISSION = "permission"


class UserEntitlementResponse(BaseModel):
    id: int
    name: str
    type: EntitlementType
    description: Optional[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty')
        return v.strip()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None

    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 50:
                raise ValueError('Username must be less than 50 characters')
        return v

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty')
        return v.strip() if v else v


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    entitlements: List[UserEntitlementResponse] = []

    class Config:
        orm_mode = True