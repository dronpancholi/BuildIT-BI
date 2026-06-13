import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.domain.auth import (
    PasswordService, TokenService, RBACService, AuditService, MFAService,
    TenantIsolation, User, Role, Permission, UserRole, UserSession, RefreshToken,
    AuditLogEntry, MFAConfig, ResourceType, Action, PermissionScope, ActorType,
    AuditAction, AuditResult, DataClassification, AuthMethod, MFAMethod,
    CFO_ROLE, ANALYST_ROLE, VIEWER_ROLE, PLATFORM_ADMIN_ROLE
)

class TestPasswordService:
    def test_hash_password(self):
        ps = PasswordService()
        hashed = ps.hash_password("TestPass123!@#")
        assert ":" in hashed
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        ps = PasswordService()
        hashed = ps.hash_password("correct")
        assert ps.verify_password("correct", hashed) is True

    def test_verify_wrong_password(self):
        ps = PasswordService()
        hashed = ps.hash_password("correct")
        assert ps.verify_password("wrong", hashed) is False

    def test_validate_weak_password_too_short(self):
        ps = PasswordService()
        valid, errors = ps.validate_password_strength("Ab1!")
        assert valid is False
        assert any("12 characters" in e for e in errors)

    def test_validate_weak_password_no_uppercase(self):
        ps = PasswordService()
        valid, errors = ps.validate_password_strength("alllowercase12!")
        assert valid is False
        assert any("uppercase" in e for e in errors)

    def test_validate_strong_password(self):
        ps = PasswordService()
        valid, errors = ps.validate_password_strength("StrongP@ssw0rd!")
        assert valid is True
        assert len(errors) == 0

class TestTokenService:
    def test_create_access_token(self):
        ts = TokenService()
        user = User(email="test@buildit.com")
        token = ts.create_access_token(user, [CFO_ROLE])
        assert isinstance(token, str)
        assert len(token) > 10

    def test_decode_valid_token(self):
        ts = TokenService()
        user = User(email="test@buildit.com")
        token = ts.create_access_token(user, [CFO_ROLE])
        payload = ts.decode_token(token)
        assert payload is not None
        assert payload["email"] == "test@buildit.com"

    def test_decode_expired_token(self):
        ts = TokenService()
        user = User(email="test@buildit.com")
        token = ts.create_access_token(user, [CFO_ROLE], expires_minutes=-1)
        payload = ts.decode_token(token)
        assert payload is None

    def test_create_refresh_token(self):
        ts = TokenService()
        rt = ts.create_refresh_token(uuid4())
        assert isinstance(rt, RefreshToken)
        assert rt.is_revoked is False
        assert rt.expires_at > datetime.utcnow()

class TestRBACService:
    def test_create_role(self):
        rbac = RBACService()
        role = rbac.create_role("test_role", "Test Role",
            [Permission(ResourceType.DASHBOARD, {Action.READ}, PermissionScope.ALL)])
        assert role.name == "test_role"
        assert role.id in rbac.roles

    def test_assign_role(self):
        rbac = RBACService()
        role = rbac.create_role("analyst", "Analyst",
            [Permission(ResourceType.DASHBOARD, {Action.READ}, PermissionScope.TEAM)])
        user_id = uuid4()
        ur = rbac.assign_role(user_id, role.id, uuid4())
        assert ur.user_id == user_id

    def test_check_permission_all_scope(self):
        rbac = RBACService()
        role = rbac.create_role("admin", "Admin",
            [Permission(ResourceType.DASHBOARD, {Action.READ, Action.CREATE}, PermissionScope.ALL)])
        user_id = uuid4()
        rbac.assign_role(user_id, role.id, uuid4())
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.READ) is True
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.DELETE) is False

    def test_check_permission_own_scope(self):
        rbac = RBACService()
        role = rbac.create_role("owner", "Owner",
            [Permission(ResourceType.DASHBOARD, {Action.READ}, PermissionScope.OWN)])
        user_id = uuid4()
        rbac.assign_role(user_id, role.id, uuid4())
        # Own resource
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.READ,
            resource_owner_id=user_id) is True
        # Other's resource
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.READ,
            resource_owner_id=uuid4()) is False

    def test_check_permission_team_scope(self):
        rbac = RBACService()
        role = rbac.create_role("team", "Team",
            [Permission(ResourceType.DASHBOARD, {Action.READ}, PermissionScope.TEAM)])
        user_id = uuid4()
        team_ids = {user_id, uuid4()}
        rbac.assign_role(user_id, role.id, uuid4())
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.READ,
            resource_team_ids=team_ids) is True

    def test_no_permission(self):
        rbac = RBACService()
        assert rbac.check_permission(uuid4(), ResourceType.DASHBOARD, Action.DELETE) is False

    def test_cfo_can_certify_metrics(self):
        rbac = RBACService()
        rbac.roles[CFO_ROLE.id] = CFO_ROLE
        user_id = uuid4()
        rbac.assign_role(user_id, CFO_ROLE.id, uuid4())
        assert rbac.check_permission(user_id, ResourceType.METRIC, Action.CERTIFY) is True

    def test_analyst_cannot_certify_metrics(self):
        rbac = RBACService()
        rbac.roles[ANALYST_ROLE.id] = ANALYST_ROLE
        user_id = uuid4()
        rbac.assign_role(user_id, ANALYST_ROLE.id, uuid4())
        assert rbac.check_permission(user_id, ResourceType.METRIC, Action.CERTIFY) is False

    def test_viewer_can_only_read(self):
        rbac = RBACService()
        rbac.roles[VIEWER_ROLE.id] = VIEWER_ROLE
        user_id = uuid4()
        rbac.assign_role(user_id, VIEWER_ROLE.id, uuid4())
        # TEAM scope needs team_ids to include the user
        team_ids = {user_id, uuid4()}
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.READ, resource_team_ids=team_ids) is True
        assert rbac.check_permission(user_id, ResourceType.DASHBOARD, Action.CREATE) is False

    def test_get_user_permissions(self):
        rbac = RBACService()
        rbac.roles[CFO_ROLE.id] = CFO_ROLE
        user_id = uuid4()
        rbac.assign_role(user_id, CFO_ROLE.id, uuid4())
        perms = rbac.get_user_permissions(user_id)
        assert len(perms) > 0

class TestAuditService:
    def test_log_event(self):
        audit = AuditService()
        entry = audit.log(AuditAction.LOGIN, ResourceType.USER, actor_id=uuid4())
        assert isinstance(entry, AuditLogEntry)
        assert entry.action == AuditAction.LOGIN
        assert len(audit.entries) == 1

    def test_log_with_compliance_flags(self):
        audit = AuditService()
        entry = audit.log(AuditAction.READ, ResourceType.DASHBOARD,
            compliance_flags=["PHI", "FINANCIAL"])
        assert "PHI" in entry.compliance_flags

    def test_query_by_action(self):
        audit = AuditService()
        audit.log(AuditAction.LOGIN, ResourceType.USER)
        audit.log(AuditAction.READ, ResourceType.DASHBOARD)
        results = audit.query(action=AuditAction.LOGIN)
        assert len(results) == 1

    def test_query_by_date_range(self):
        audit = AuditService()
        audit.log(AuditAction.LOGIN, ResourceType.USER)
        results = audit.query(start_date=datetime.utcnow() - timedelta(hours=1))
        assert len(results) == 1

    def test_query_limit(self):
        audit = AuditService()
        for _ in range(50):
            audit.log(AuditAction.READ, ResourceType.DASHBOARD)
        results = audit.query(limit=10)
        assert len(results) == 10

class TestTenantIsolation:
    def test_set_get_tenant(self):
        ti = TenantIsolation()
        tid = uuid4()
        ti.set_tenant(tid)
        assert ti.get_tenant() == tid

    def test_inject_tenant_filter(self):
        ti = TenantIsolation()
        tid = uuid4()
        result = ti.inject_tenant_filter("SELECT * FROM metrics", tid)
        assert "tenant_id" in result
        assert str(tid) in result

    def test_validate_tenant_access_same(self):
        ti = TenantIsolation()
        tid = uuid4()
        assert ti.validate_tenant_access(tid, tid) is True

    def test_validate_tenant_access_different(self):
        ti = TenantIsolation()
        assert ti.validate_tenant_access(uuid4(), uuid4()) is False

class TestMFAService:
    def test_setup_totp(self):
        mfa = MFAService()
        user_id = uuid4()
        qr_url, secret = mfa.setup_totp(user_id)
        assert "otpauth://" in qr_url
        assert len(secret) > 10

    def test_verify_totp_valid(self):
        mfa = MFAService()
        user_id = uuid4()
        mfa.setup_totp(user_id)
        assert mfa.verify_totp(user_id, "123456") is True

    def test_verify_totp_invalid_length(self):
        mfa = MFAService()
        user_id = uuid4()
        mfa.setup_totp(user_id)
        assert mfa.verify_totp(user_id, "123") is False

    def test_verify_backup_code(self):
        mfa = MFAService()
        user_id = uuid4()
        mfa.setup_totp(user_id)
        config = mfa.configs[user_id]
        code = config.backup_codes[0]
        assert mfa.verify_backup_code(user_id, code) is True
        assert code not in config.backup_codes

    def test_is_configured(self):
        mfa = MFAService()
        user_id = uuid4()
        assert mfa.is_configured(user_id) is False
        mfa.setup_totp(user_id)
        assert mfa.is_configured(user_id) is True

class TestUserSession:
    def test_session_not_expired(self):
        session = UserSession(expires_at=datetime.utcnow() + timedelta(hours=1))
        assert session.is_expired() is False

    def test_session_expired(self):
        session = UserSession(expires_at=datetime.utcnow() - timedelta(hours=1))
        assert session.is_expired() is True

    def test_session_no_expiry(self):
        session = UserSession(expires_at=None)
        assert session.is_expired() is False
