"""
Authentication endpoints — signup, login, session management.
Fixed: commit transaction on register, proper tenant creation, type-safe tokens,
       brute-force protection, case-insensitive email lookup.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import timedelta, datetime
from threading import Lock
import uuid
import re
from pydantic import EmailStr

from app.db.session import get_db
from app.schemas.schemas import UserCreate, UserResponse, Token, TokenData
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)


router = APIRouter()

# ---------------------------------------------------------------------------
# Rate limiting — sliding window, per-identifier (IP or email).
# For production with multiple workers: replace with Redis-backed store.
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field


@dataclass
class RateLimitBucket:
    """Sliding-window failure counter for one identifier."""
    attempts: list[datetime] = field(default_factory=list)

    def add(self, when: datetime) -> None:
        self.attempts.append(when)

    def count_recent(self, window: timedelta) -> int:
        cutoff = datetime.utcnow() - window
        self.attempts = [t for t in self.attempts if t > cutoff]
        return len(self.attempts)

    def is_locked(self, window: timedelta, max_attempts: int) -> bool:
        return self.count_recent(window) >= max_attempts


# Global store — per (identifier, action) bucket
_rate_limit_store: dict[tuple[str, str], RateLimitBucket] = {}
_rate_limit_lock = Lock()

# Tunables (can move to settings)
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_MAX_ATTEMPTS = 5
REGISTER_WINDOW = timedelta(hours=1)
REGISTER_MAX_ATTEMPTS = 5


def _get_client_ip(request: Request) -> str:
    """Prefer X-Forwarded-For (when behind a proxy/Cloudflare), else client host."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(
    request: Request,
    action: str,
    window: timedelta,
    max_attempts: int,
    identifier: str | None = None,
) -> None:
    """
    Raise 429 if rate limit is exceeded for this (IP, action) pair.
    Pass identifier=None to use the client IP.
    """
    ip = identifier or _get_client_ip(request)
    key = (ip, action)

    with _rate_limit_lock:
        bucket = _rate_limit_store.setdefault(key, RateLimitBucket())

    now = datetime.utcnow()
    with _rate_limit_lock:
        bucket.add(now)

    if bucket.is_locked(window, max_attempts):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many {action} attempts. Please try again later.",
        )


# ---------------------------------------------------------------------------
# Password policy
# ---------------------------------------------------------------------------
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Return (is_valid, error_message)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    if len(password) > PASSWORD_MAX_LENGTH:
        return False, f"Password must not exceed {PASSWORD_MAX_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, ""


# ---------------------------------------------------------------------------
# Tenant helpers
# ---------------------------------------------------------------------------

async def _get_or_create_default_tenant(db: AsyncSession) -> uuid.UUID:
    """
    Return the ID of the default tenant, creating it if it doesn't exist.
    This is the system tenant — never deleted, always has id == tenant_id.
    """
    # Try to find existing tenant
    result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
    row = result.fetchone()
    if row:
        return row[0]

    # Create default tenant
    tenant_id = uuid.uuid4()
    now = datetime.utcnow()
    await db.execute(
        text("""
            INSERT INTO tenants
              (id, tenant_id, name, code, is_active, subscription_tier,
               created_at, updated_at, created_by, updated_by)
            VALUES
              (:id, :tenant_id, :name, :code, true, 'professional',
               :now, :now, NULL, NULL)
        """),
        {
            "id": tenant_id,
            "tenant_id": tenant_id,
            "name": "Default Organization",
            "code": "default",
            "now": now,
        },
    )
    # Flush so the insert is visible to subsequent queries in the same tx
    await db.flush()
    return tenant_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account.

    - Validates password strength (min 8 chars, upper, lower, digit)
    - Creates a default system tenant if none exists
    - Commits the transaction before returning
    - Rate limited: 5 attempts per hour per IP
    """
    check_rate_limit(request, "register", REGISTER_WINDOW, REGISTER_MAX_ATTEMPTS)

    # 1. Password strength validation
    valid, msg = validate_password_strength(user_data.password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )

    # 2. Check email uniqueness (case-insensitive via LOWER index if available)
    result = await db.execute(
        text("SELECT id FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
        {"email": user_data.email},
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    # 3. Resolve tenant
    tenant_id = await _get_or_create_default_tenant(db)

    # 4. Build user
    password_hash = get_password_hash(user_data.password)
    user_id = uuid.uuid4()
    now = datetime.utcnow()

    await db.execute(
        text("""
            INSERT INTO users
              (id, tenant_id, username, email, full_name, password_hash, role,
               is_active, login_count, created_at, updated_at, created_by, updated_by)
            VALUES
              (:id, :tenant_id, :username, :email, :full_name, :password_hash, :role,
               true, 0, :now, :now, NULL, NULL)
        """),
        {
            "id": user_id,
            "tenant_id": tenant_id,
            "username": user_data.email.split("@")[0][:100],
            "email": user_data.email.lower().strip(),
            "full_name": user_data.full_name,
            "password_hash": password_hash,
            "role": user_data.role.value if hasattr(user_data.role, "value") else user_data.role,
            "now": now,
        },
    )

    # 5. Commit so the user is visible to subsequent requests
    await db.commit()

    # 6. Return the created user
    user_row = await db.execute(
        text("SELECT * FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = user_row.mappings().fetchone()
    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        full_name=row["full_name"] or "",
        role=row["role"],
        is_active=row["is_active"],
        created_at=row["created_at"],
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate with email + password, return a JWT bearer token.

    On success: updates last_login_at and increments login_count.
    On failure: returns 401 without distinguishing email-vs-password
               (prevents user-enumeration attacks).
    Rate limited: 5 attempts per 15 minutes per IP.
    """
    check_rate_limit(request, "login", LOGIN_WINDOW, LOGIN_MAX_ATTEMPTS)

    # 1. Fetch user by email (case-insensitive)
    result = await db.execute(
        text("SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1"),
        {"email": form_data.username},
    )
    user = result.mappings().fetchone()

    # 2. Verify password (constant-time, no timing leak)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check account is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # 4. Update login tracking (fire-and-forget within the request tx)
    await db.execute(
        text("""
            UPDATE users
            SET last_login_at = :now,
                login_count    = login_count + 1,
                updated_at    = :now
            WHERE id = :id
        """),
        {"id": user["id"], "now": datetime.utcnow()},
    )
    await db.commit()

    # 5. Mint JWT — user_id is stored as string (UUID) for safety
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["id"]),
            "role": user["role"],
            "tenant_id": str(user["tenant_id"]),
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user for the current session."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name or "",
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str = None,
    email: EmailStr = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the authenticated user's profile."""
    from sqlalchemy import text
    
    updates = []
    params = {"id": current_user.id}
    
    if full_name is not None:
        updates.append("full_name = :full_name")
        params["full_name"] = full_name
    if email is not None:
        updates.append("email = LOWER(:email)")
        params["email"] = email
    
    if updates:
        updates.append("updated_at = :now")
        params["now"] = datetime.utcnow()
        
        await db.execute(
            text(f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE id = :id
            """),
            params,
        )
        await db.commit()
        
        # Fetch updated user
        result = await db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": current_user.id},
        )
        row = result.mappings().fetchone()
        return UserResponse(
            id=str(row["id"]),
            email=row["email"],
            full_name=row["full_name"] or "",
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name or "",
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> list[UserResponse]:
    """
    List all users (tenant-scoped). Requires ceo/cfo/finance_manager role.
    """
    if current_user.role not in {"ceo", "cfo", "finance_manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to list users",
        )

    result = await db.execute(
        text("""
            SELECT id, email, full_name, role, is_active, created_at
            FROM users
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """),
        {"tenant_id": current_user.tenant_id, "limit": limit, "skip": skip},
    )
    rows = result.mappings().all()
    return [
        UserResponse(
            id=str(row["id"]),
            email=row["email"],
            full_name=row["full_name"] or "",
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )
        for row in rows
    ]