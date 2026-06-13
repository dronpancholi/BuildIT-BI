"""
Development Authentication Constants.
Replace full auth stack with dev constants during Phase 4 analytics work.
Enterprise auth returns post-Phase 4.
"""
from dataclasses import dataclass
from uuid import UUID
from fastapi import Depends


@dataclass(frozen=True)
class DevUser:
    id: UUID
    email: str
    full_name: str
    role: str
    tenant_id: UUID


DEV_ADMIN = DevUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    email="dev@buildit.health",
    full_name="Development Administrator",
    role="admin",
    tenant_id=UUID("51267a17-735c-479a-979c-cd4c5f04cabb"),
)

DEV_CFO = DevUser(
    id=UUID("00000000-0000-0000-0000-000000000002"),
    email="cfo@buildit.health",
    full_name="Development CFO",
    role="cfo",
    tenant_id=UUID("51267a17-735c-479a-979c-cd4c5f04cabb"),
)


async def dep_dev_admin() -> DevUser:
    """Dependency that returns the dev admin user. No auth required."""
    return DEV_ADMIN


async def dep_dev_cfo() -> DevUser:
    """Dependency that returns the dev CFO user. No auth required."""
    return DEV_CFO


async def dep_dev_user() -> DevUser:
    """Dependency that returns the default dev user. No auth required."""
    return DEV_ADMIN
