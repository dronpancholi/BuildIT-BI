from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4


# === Enums ===

class AuthMethod(Enum):
    PASSWORD = "password"
    SSO_OIDC = "sso_oidc"
    SSO_SAML = "sso_saml"
    API_KEY = "api_key"


class MFAMethod(Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    WEB_AUTHN = "web_authn"


class ResourceType(Enum):
    DASHBOARD = "dashboard"
    REPORT = "report"
    METRIC = "metric"
    FORMULA = "formula"
    USER = "user"
    SYSTEM = "system"
    QUERY = "query"
    EXPORT = "export"
    DECISION = "decision"
    INTELLIGENCE = "intelligence"


class Action(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    EXPORT = "export"
    APPROVE = "approve"
    REJECT = "reject"
    CERTIFY = "certify"
    EXECUTE = "execute"


class PermissionScope(Enum):
    OWN = "own"
    TEAM = "team"
    ALL = "all"
    NONE = "none"


class ActorType(Enum):
    USER = "user"
    SYSTEM = "system"
    SCHEDULED_JOB = "scheduled_job"
    API_KEY = "api_key"


class AuditAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    EXPORT = "export"
    SHARE = "share"
    APPROVE = "approve"
    REJECT = "reject"


class AuditResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


# === Core entities ===

@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    full_name: str = ""
    tenant_id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    is_superadmin: bool = False
    auth_method: AuthMethod = AuthMethod.PASSWORD
    mfa_enabled: bool = False
    mfa_method: Optional[MFAMethod] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    department_id: Optional[UUID] = None


@dataclass
class Role:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    display_name: str = ""
    description: str = ""
    is_system_role: bool = False
    tenant_id: Optional[UUID] = None
    permissions: list[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Permission:
    resource: ResourceType = ResourceType.DASHBOARD
    actions: set[Action] = field(default_factory=set)
    scope: PermissionScope = PermissionScope.NONE


@dataclass
class UserRole:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    role_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    scope: PermissionScope = PermissionScope.TEAM
    granted_by: UUID = field(default_factory=uuid4)
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class UserSession:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    ip_address: str = ""
    user_agent: str = ""
    auth_method: str = "password"
    mfa_verified: bool = False
    is_active: bool = True

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class RefreshToken:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    token_hash: str = ""
    family: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_revoked: bool = False


@dataclass
class AuditLogEntry:
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor_type: ActorType = ActorType.USER
    actor_id: Optional[UUID] = None
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None
    user_agent: Optional[str] = None
    action: AuditAction = AuditAction.READ
    resource_type: ResourceType = ResourceType.DASHBOARD
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    changes: Optional[dict] = None
    filters_applied: Optional[dict] = None
    result: AuditResult = AuditResult.SUCCESS
    error_message: Optional[str] = None
    session_id: Optional[UUID] = None
    request_id: Optional[UUID] = None
    compliance_flags: list[str] = field(default_factory=list)


@dataclass
class MFAConfig:
    user_id: UUID = field(default_factory=uuid4)
    enabled: bool = False
    method: MFAMethod = MFAMethod.TOTP
    totp_secret: Optional[str] = None
    backup_codes: list[str] = field(default_factory=list)


# === Services ===

class PasswordService:
    """Password hashing and verification"""

    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        return f"{salt}:{h}"

    def verify_password(self, password: str, hashed: str) -> bool:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == h

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        errors = []
        if len(password) < 12:
            errors.append("Password must be at least 12 characters")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain special character")
        return len(errors) == 0, errors


class TokenService:
    """JWT-like token management (simplified for demo)"""

    def create_access_token(self, user: User, roles: list[Role], expires_minutes: int = 60) -> str:
        import base64, json
        payload = {
            "sub": str(user.id),
            "tid": str(user.tenant_id),
            "email": user.email,
            "roles": [r.name for r in roles],
            "exp": int(time.time()) + expires_minutes * 60,
            "iat": int(time.time()),
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def decode_token(self, token: str) -> Optional[dict]:
        import base64, json
        try:
            payload = json.loads(base64.urlsafe_b64decode(token.encode()))
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except Exception:
            return None

    def create_refresh_token(self, user_id: UUID) -> RefreshToken:
        return RefreshToken(
            user_id=user_id,
            token_hash=hashlib.sha256(secrets.token_hex(32).encode()).hexdigest(),
            family=secrets.token_hex(16),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )


class RBACService:
    """Role-Based Access Control"""

    def __init__(self):
        self.roles: dict[UUID, Role] = {}
        self.user_roles: dict[UUID, list[UserRole]] = {}

    def create_role(
        self,
        name: str,
        display_name: str,
        permissions: list[Permission],
        is_system: bool = False,
        tenant_id: Optional[UUID] = None,
    ) -> Role:
        role = Role(
            name=name,
            display_name=display_name,
            permissions=permissions,
            is_system_role=is_system,
            tenant_id=tenant_id,
        )
        self.roles[role.id] = role
        return role

    def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID,
        scope: PermissionScope = PermissionScope.TEAM,
    ) -> UserRole:
        ur = UserRole(user_id=user_id, role_id=role_id, tenant_id=tenant_id, scope=scope)
        self.user_roles.setdefault(user_id, []).append(ur)
        return ur

    def check_permission(
        self,
        user_id: UUID,
        resource: ResourceType,
        action: Action,
        resource_owner_id: Optional[UUID] = None,
        resource_team_ids: Optional[set[UUID]] = None,
    ) -> bool:
        urs = self.user_roles.get(user_id, [])
        for ur in urs:
            role = self.roles.get(ur.role_id)
            if not role:
                continue
            for perm in role.permissions:
                if perm.resource == resource and action in perm.actions:
                    if perm.scope == PermissionScope.ALL:
                        return True
                    if perm.scope == PermissionScope.TEAM and resource_team_ids and user_id in resource_team_ids:
                        return True
                    if perm.scope == PermissionScope.OWN and resource_owner_id and user_id == resource_owner_id:
                        return True
        return False

    def get_user_permissions(self, user_id: UUID) -> list[Permission]:
        merged: dict[tuple, Permission] = {}
        urs = self.user_roles.get(user_id, [])
        for ur in urs:
            role = self.roles.get(ur.role_id)
            if not role:
                continue
            for perm in role.permissions:
                key = (perm.resource, frozenset(perm.actions))
                if key not in merged:
                    merged[key] = perm
                else:
                    existing = merged[key]
                    if perm.scope == PermissionScope.ALL or (
                        perm.scope == PermissionScope.TEAM and existing.scope == PermissionScope.OWN
                    ):
                        merged[key] = perm
        return list(merged.values())


class AuditService:
    """Audit logging service"""

    def __init__(self):
        self.entries: list[AuditLogEntry] = []

    def log(
        self,
        action: AuditAction,
        resource_type: ResourceType,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        resource_name: Optional[str] = None,
        changes: Optional[dict] = None,
        result: AuditResult = AuditResult.SUCCESS,
        error_message: Optional[str] = None,
        session_id: Optional[UUID] = None,
        request_id: Optional[UUID] = None,
        compliance_flags: Optional[list[str]] = None,
        actor_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        actor_type: ActorType = ActorType.USER,
        filters_applied: Optional[dict] = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            filters_applied=filters_applied,
            result=result,
            error_message=error_message,
            session_id=session_id,
            request_id=request_id,
            compliance_flags=compliance_flags or [],
        )
        self.entries.append(entry)
        return entry

    def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[ResourceType] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        results = self.entries
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]
        if end_date:
            results = [e for e in results if e.timestamp <= end_date]
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        if action:
            results = [e for e in results if e.action == action]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        return results[-limit:]


class TenantIsolation:
    """Tenant isolation enforcement"""

    def __init__(self):
        self._current_tenant: Optional[UUID] = None

    def set_tenant(self, tenant_id: UUID):
        self._current_tenant = tenant_id

    def get_tenant(self) -> Optional[UUID]:
        return self._current_tenant

    def inject_tenant_filter(self, query: str, tenant_id: UUID) -> str:
        if "WHERE" in query.upper():
            return f"{query} AND tenant_id = '{tenant_id}'"
        return f"{query} WHERE tenant_id = '{tenant_id}'"

    def validate_tenant_access(self, resource_tenant_id: UUID, user_tenant_id: UUID) -> bool:
        return resource_tenant_id == user_tenant_id


class MFAService:
    """Multi-factor authentication"""

    def __init__(self):
        self.configs: dict[UUID, MFAConfig] = {}

    def setup_totp(self, user_id: UUID) -> tuple[str, str]:
        secret = secrets.token_hex(20)
        self.configs[user_id] = MFAConfig(
            user_id=user_id, enabled=True, method=MFAMethod.TOTP, totp_secret=secret
        )
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        self.configs[user_id].backup_codes = backup_codes
        return f"otpauth://totp/BuildIT:{user_id}?secret={secret}&issuer=BuildIT", secret

    def verify_totp(self, user_id: UUID, code: str) -> bool:
        config = self.configs.get(user_id)
        if not config or not config.enabled:
            return False
        return len(code) == 6 and code.isdigit()

    def verify_backup_code(self, user_id: UUID, code: str) -> bool:
        config = self.configs.get(user_id)
        if not config:
            return False
        if code in config.backup_codes:
            config.backup_codes.remove(code)
            return True
        return False

    def is_configured(self, user_id: UUID) -> bool:
        config = self.configs.get(user_id)
        return config is not None and config.enabled


# === Role definitions (healthcare financial) ===

PLATFORM_ADMIN_ROLE = Role(
    name="platform_admin",
    display_name="Platform Administrator",
    description="Full system access",
    is_system_role=True,
    permissions=[Permission(r, set(Action), PermissionScope.ALL) for r in ResourceType],
)

TENANT_ADMIN_ROLE = Role(
    name="tenant_admin",
    display_name="Organization Administrator",
    description="Full access within tenant",
    is_system_role=True,
    permissions=[Permission(r, set(Action), PermissionScope.ALL) for r in ResourceType],
)

CFO_ROLE = Role(
    name="cfo",
    display_name="Chief Financial Officer",
    permissions=[
        Permission(
            ResourceType.DASHBOARD,
            {Action.READ, Action.CREATE, Action.UPDATE, Action.SHARE, Action.EXPORT},
            PermissionScope.ALL,
        ),
        Permission(
            ResourceType.REPORT,
            {Action.READ, Action.CREATE, Action.UPDATE, Action.SHARE, Action.EXPORT},
            PermissionScope.ALL,
        ),
        Permission(
            ResourceType.METRIC,
            {Action.READ, Action.CREATE, Action.UPDATE, Action.CERTIFY},
            PermissionScope.ALL,
        ),
        Permission(
            ResourceType.DECISION,
            {Action.READ, Action.CREATE, Action.UPDATE, Action.APPROVE, Action.REJECT},
            PermissionScope.ALL,
        ),
        Permission(ResourceType.INTELLIGENCE, {Action.READ}, PermissionScope.ALL),
    ],
)

ANALYST_ROLE = Role(
    name="analyst",
    display_name="Financial Analyst",
    permissions=[
        Permission(
            ResourceType.DASHBOARD,
            {Action.READ, Action.CREATE, Action.UPDATE},
            PermissionScope.OWN,
        ),
        Permission(
            ResourceType.REPORT,
            {Action.READ, Action.CREATE, Action.UPDATE},
            PermissionScope.OWN,
        ),
        Permission(ResourceType.METRIC, {Action.READ, Action.CREATE}, PermissionScope.TEAM),
        Permission(ResourceType.QUERY, {Action.EXECUTE}, PermissionScope.TEAM),
        Permission(ResourceType.EXPORT, {Action.READ, Action.EXECUTE}, PermissionScope.OWN),
    ],
)

VIEWER_ROLE = Role(
    name="viewer",
    display_name="Read-Only Viewer",
    permissions=[
        Permission(ResourceType.DASHBOARD, {Action.READ}, PermissionScope.TEAM),
        Permission(ResourceType.REPORT, {Action.READ}, PermissionScope.TEAM),
        Permission(ResourceType.METRIC, {Action.READ}, PermissionScope.TEAM),
    ],
)
