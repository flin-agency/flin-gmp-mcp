"""Bounded requests to an explicit allowlist of read-only Google API routes."""

from __future__ import annotations

import json
import re
from typing import Any

import requests
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession

from . import __version__
from .auth import AuthenticationRequiredError, get_credentials, save_credentials
from .config import ConfigurationError, load_settings, resolve_token_path

BASE_URLS = {
    "admin": "https://marketingplatformadmin.googleapis.com/v1alpha/",
    "dv360": "https://displayvideo.googleapis.com/v4/",
    "cm360": "https://dfareporting.googleapis.com/dfareporting/v5/",
    "sa360": "https://searchads360.googleapis.com/v0/",
    "dbm": "https://doubleclickbidmanager.googleapis.com/v2/",
}
# No arbitrary URL, method, or write endpoint is accepted, even by this internal client.
READ_PATHS = {
    "admin": r"organizations(?:/[A-Za-z0-9_-]+(?:/analyticsAccountLinks)?)?",
    "dv360": r"(?:partners|advertisers)(?:/[0-9]+)?|advertisers/[0-9]+/(?:campaigns|insertionOrders|lineItems|creatives)(?:/[0-9]+)?",
    "cm360": r"userprofiles|userprofiles/[0-9]+/(?:advertisers|campaigns|reports|creatives(?:/[0-9]+)?)|userprofiles/[0-9]+/reports/[0-9]+/files(?:/[0-9]+)?",
    "sa360": r"customers:listAccessibleCustomers|customers/[0-9]+/customColumns",
    "dbm": r"queries(?:/[0-9]+(?:/reports(?:/[0-9]+)?)?)?",
}
SEARCH_PATH = r"(?:customers/[0-9]+/searchAds360:search|searchAds360Fields:search)"
MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class APIError(RuntimeError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Google API request failed ({status}).")


class ResponseTooLargeError(ValueError):
    """A response exceeded the maximum size the client can safely return."""


def numeric_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{1,20}", value):
        raise ValueError("Expected a numeric ID without separators.")
    return value


def organization_id(value: str) -> str:
    value = value.removeprefix("organizations/")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("Invalid organization ID.")
    return value


def page_params(
    page_size: int, page_token: str | None, *, maximum: int = 1000, size_key: str = "pageSize"
) -> dict[str, Any]:
    if isinstance(page_size, bool) or not 1 <= page_size <= maximum:
        raise ValueError(f"Page size must be between 1 and {maximum}.")
    if page_token is not None and len(page_token) > 16384:
        raise ValueError("Page token too long.")
    return {size_key: page_size, **({"pageToken": page_token} if page_token else {})}


def validate_query(query: str) -> str:
    # This is an early usability check; the only target is Google's reporting search API.
    if len(query) > 100_000 or not re.match(r"\s*SELECT\s+", query, flags=re.IGNORECASE):
        raise ValueError("Use a Search Ads 360 SELECT query.")
    return query


def request(
    service: str,
    path: str,
    *,
    account: str | None = None,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
    method = "POST" if body is not None else "GET"
    if service not in BASE_URLS:
        raise ValueError("Unknown service.")
    pattern = SEARCH_PATH if service == "sa360" and method == "POST" else READ_PATHS[service]
    if (method == "POST" and service != "sa360") or not re.fullmatch(pattern, path):
        raise ValueError("Only allowlisted read operations are supported.")
    if body is not None:
        validate_query(body.get("query", ""))
    if login_customer_id is not None:
        if service != "sa360":
            raise ValueError("Manager login headers are only supported for SA360.")
        numeric_id(login_customer_id)
    settings = load_settings()
    product = "dv360" if service == "dbm" else service
    if product not in settings.services:
        raise ConfigurationError("Enable this product in GOOGLE_GMP_SERVICES.")
    credentials = get_credentials(settings=settings, account=account, interactive=False)
    headers = {"User-Agent": f"flin-gmp-mcp/{__version__}", "Accept": "application/json"}
    if settings.quota_project:
        headers["x-goog-user-project"] = settings.quota_project
    if login_customer_id:
        headers["login-customer-id"] = login_customer_id
    params = {key: value for key, value in (params or {}).items() if value is not None}
    # Requests serializes booleans as True/False; Google's query format is lowercase.
    params = {
        key: str(value).lower() if isinstance(value, bool) else value
        for key, value in params.items()
    }
    before_token = credentials.token
    try:
        with AuthorizedSession(credentials, refresh_timeout=30) as session:
            with session.request(
                method,
                BASE_URLS[service] + path,
                params=params,
                json=body,
                headers=headers,
                timeout=(10, 60),
                allow_redirects=False,
                stream=True,
            ) as response:
                if not 200 <= response.status_code < 300:
                    raise APIError(response.status_code)
                chunks = []
                length = 0
                for chunk in response.iter_content(chunk_size=65536):
                    length += len(chunk)
                    if length > MAX_RESPONSE_BYTES:
                        raise ResponseTooLargeError("Response too large.")
                    chunks.append(chunk)
                try:
                    data = json.loads(b"".join(chunks))
                except (ValueError, UnicodeError) as exc:
                    raise APIError(502) from exc
                if not isinstance(data, dict):
                    raise APIError(502)
    except GoogleAuthError as exc:
        raise AuthenticationRequiredError("Sign in again with authenticate.") from exc
    finally:
        if credentials.token != before_token:
            save_credentials(credentials, resolve_token_path(settings=settings, account=account))
    return data


def error_message(exc: Exception) -> str:
    # Never expose upstream bodies, exception text, OAuth URLs or credentials.
    from .auth import AuthenticationError

    if isinstance(exc, AuthenticationRequiredError):
        return "oauth_required: Run authenticate for this account, then retry."
    if isinstance(exc, AuthenticationError):
        return "authentication_failed: Check the token file and private storage directory."
    if isinstance(exc, ConfigurationError):
        return "invalid_configuration: Check OAuth credentials, enabled services and account name."
    if isinstance(exc, APIError):
        if exc.status == 401:
            return "oauth_required: Run authenticate with force=true, then retry."
        if exc.status == 403:
            return "permission_denied: Check product access, enabled APIs, OAuth scopes and quota."
        if exc.status == 404:
            return "not_found: Check the resource ID and selected Google account."
        if exc.status == 429:
            return "quota_exceeded: Retry later with fewer requests."
        if exc.status >= 500:
            return "service_unavailable: Google is temporarily unavailable. Retry later."
        return "google_request_failed: Check IDs, query fields, filters and page tokens."
    if isinstance(exc, (requests.Timeout, TimeoutError)):
        return "request_timeout: Retry, or complete browser sign-in before the timeout."
    if isinstance(exc, (requests.RequestException, OSError)):
        return "connection_error: Check network access and token storage permissions."
    if isinstance(exc, ResponseTooLargeError):
        return "response_too_large: Reduce page_size or select fewer query fields, then retry."
    if isinstance(exc, ValueError):
        return "invalid_arguments: Check IDs, page sizes, dates and SELECT query syntax."
    return "internal_error: Restart the MCP server and retry."
