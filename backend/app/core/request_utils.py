"""Helpers for extracting client information from an incoming request."""

from fastapi import Request

from app.core.config import get_settings


def get_client_ip(request: Request) -> str | None:
    """
    Best-effort client IP for audit logging.

    X-Forwarded-For is only honoured when TRUST_PROXY_HEADERS=true, i.e. when
    the API runs behind a proxy you control. Otherwise any client could put
    a fake address in the header and pollute (or evade) IP-based detection.
    """
    if get_settings().TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first_hop = forwarded.split(",")[0].strip()
            if first_hop:
                return first_hop[:45]
    return request.client.host[:45] if request.client else None


def get_user_agent(request: Request) -> str | None:
    agent = request.headers.get("user-agent")
    return agent[:255] if agent else None
