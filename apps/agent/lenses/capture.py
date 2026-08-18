"""
URL -> screenshot capture via headless Chromium, for URL-sourced audits.

Uploaded files are a trust boundary, and so is a URL a user hands us to
fetch server-side -- this is an SSRF-shaped surface (the server, not the
user's browser, makes the request). Reject anything that isn't a plain
http(s) URL to a public host before ever launching the browser.
"""
import ipaddress
import socket
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1280, "height": 800}


class UnsafeUrlError(ValueError):
    pass


def _is_private_or_loopback(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True  # can't resolve -- treat as unsafe rather than silently proceeding
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True
    return False


def validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Only http/https URLs are allowed, got: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no host")
    if parsed.hostname in ("localhost",) or _is_private_or_loopback(parsed.hostname):
        raise UnsafeUrlError(f"Refusing to capture a private/loopback host: {parsed.hostname}")
    return url


def capture_screenshot(url: str, output_path: str, timeout_ms: int = 20_000) -> None:
    validate_public_http_url(url)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport=VIEWPORT)
            page.goto(url, wait_until="load", timeout=timeout_ms)
            page.screenshot(path=output_path)
        finally:
            browser.close()
