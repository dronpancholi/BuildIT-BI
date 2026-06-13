"""
Security primitives: hashing, JWT encoding/decoding, current-user resolution.
Fixed: removed ORM model dependency (schema mismatch with raw-SQL auth queries),
       type-safe UUID handling, no more undefined-variable bug.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass
class CurrentUser:
    """
    Lightweight identity object returned by get_current_user().
    NOT an ORM model — avoids schema-coupling with the auth layer.
    """
    id: str            # UUID as string
    email: str
    role: str
    tenant_id: str     # UUID as string
    full_name: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_row(cls, row: dict) -> "CurrentUser":
        return cls(
            id=str(row["id"]),
            email=row["email"],
            role=row["role"],
            tenant_id=str(row["tenant_id"]),
            full_name=row.get("full_name") or "",
            is_active=row["is_active"],
            created_at=row["created_at"],
        )


# ---------------------------------------------------------------------------
# Password hashing (bcrypt, always)
# ---------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time bcrypt comparison — safe against timing attacks."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Generate a new bcrypt hash with a random salt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Encode a JWT with HS256.  Payload always gets an 'exp' claim.
    data should contain: sub (email), user_id (str UUID), role, tenant_id (str UUID).
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Current user resolution
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Decode the Bearer token, fetch the user from the database,
    return a CurrentUser dataclass.

    Raises HTTPException 401 on any validation failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Look up by email — always case-insensitive
    result = await db.execute(
        text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
        {"email": email},
    )
    row = result.mappings().fetchone()

    if not row:
        raise credentials_exception

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return CurrentUser.from_row(row)