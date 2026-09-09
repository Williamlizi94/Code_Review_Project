"""Validation for user-controlled outbound HTTP destinations."""

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit


def _validate_ip(address: str) -> None:
    ip = ipaddress.ip_address(address)
    if not ip.is_global:
        raise ValueError("callback URL must resolve to a public IP address")


def validate_public_http_url(url: str) -> str:
    """Reject non-HTTP, credentialed, local, and literal non-public destinations."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("callback URL must use http or https")
    if not parsed.hostname:
        raise ValueError("callback URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("callback URL must not contain credentials")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("callback URL must not target localhost")

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        _validate_ip(hostname)
    return url


async def validate_public_http_destination(url: str) -> str:
    """Resolve a callback host and reject any non-public destination."""
    validate_public_http_url(url)
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = await asyncio.to_thread(
        socket.getaddrinfo,
        parsed.hostname,
        port,
        type=socket.SOCK_STREAM,
    )
    if not addresses:
        raise ValueError("callback hostname did not resolve")
    for address in {str(item[4][0]) for item in addresses}:
        _validate_ip(address)
    return url
