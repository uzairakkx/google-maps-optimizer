from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def test_settings_validate_supported_infrastructure_urls() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://user:password@localhost/database",
        redis_url="redis://localhost:6379/0",
        cors_origins="http://localhost:3000, http://localhost:3001",
    )

    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]


def test_settings_reject_unsupported_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///not-supported", redis_url="redis://localhost")