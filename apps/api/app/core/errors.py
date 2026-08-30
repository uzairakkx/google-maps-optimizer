from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationError(Exception):
    """Safe, typed error boundary for future application services."""

    code: str
    message: str
    status_code: int = 400