from fastapi import HTTPException
import pytest

from app.core.permissions import require_permission


def test_permission_check_rejects_ungranted_operation():
    dependency = require_permission("tenants.delete")
    with pytest.raises(HTTPException) as error:
        dependency({"permissions": ["tenants.view"]})
    assert error.value.status_code == 403


def test_super_admin_wildcard_grants_permission():
    dependency = require_permission("tenants.delete")
    assert dependency({"permissions": ["*"]})["permissions"] == ["*"]
