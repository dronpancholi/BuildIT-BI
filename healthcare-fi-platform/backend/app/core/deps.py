"""
Shared FastAPI dependencies.
"""
from fastapi import Depends

from app.core.dev_auth import DevUser, dep_dev_user


async def dep_tenant_id(user: DevUser = Depends(dep_dev_user)) -> str:
    """Extract tenant_id from the authenticated dev user."""
    return str(user.tenant_id)
