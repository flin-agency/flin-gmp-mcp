import json
from unittest.mock import Mock

import pytest
import requests

from flin_gmp_mcp import client
from flin_gmp_mcp.auth import AuthenticationRequiredError
from flin_gmp_mcp.config import ConfigurationError, Settings


@pytest.fixture
def transport(monkeypatch, tmp_path):
    settings = Settings("id", "secret", tmp_path)
    monkeypatch.setattr(client, "load_settings", lambda: settings)
    credentials = Mock(token="private-token")
    monkeypatch.setattr(client, "get_credentials", Mock(return_value=credentials))
    response = Mock(status_code=200)
    response.iter_content.return_value = [
        json.dumps({"items": [], "nextPageToken": "next"}).encode()
    ]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.request.return_value = response
    monkeypatch.setattr(client, "AuthorizedSession", Mock(return_value=session))
    return session, response


def test_get_transport_and_pagination(transport):
    session, _ = transport
    data = client.request(
        "cm360",
        "userprofiles/12/campaigns",
        params={"archived": False, "pageToken": "next", "unused": None},
    )
    assert data["nextPageToken"] == "next"
    args, kwargs = session.request.call_args
    assert args == (
        "GET",
        "https://dfareporting.googleapis.com/dfareporting/v5/userprofiles/12/campaigns",
    )
    assert kwargs["params"] == {"archived": "false", "pageToken": "next"}
    assert kwargs["timeout"] == (10, 60)
    assert kwargs["allow_redirects"] is False


def test_search_only_post_and_manager_header(transport):
    session, _ = transport
    body = {"query": "SELECT campaign.id FROM campaign", "pageSize": 5}
    client.request("sa360", "customers/123/searchAds360:search", body=body, login_customer_id="456")
    assert session.request.call_args.args[0] == "POST"
    assert session.request.call_args.kwargs["headers"]["login-customer-id"] == "456"
    assert session.request.call_args.kwargs["json"] == body


@pytest.mark.parametrize(
    "service,path,body",
    [
        ("admin", "https://evil.example/token", None),
        ("dv360", "advertisers/1:bulkEdit", {}),
        ("cm360", "userprofiles/1/reports/2/run", {}),
        ("cm360", "userprofiles/1/creatives", {}),
        ("cm360", "userprofiles/1/creatives/2", {}),
        ("cm360", "userprofiles/1/creatives/2/preview", None),
        ("cm360", "userprofiles/1/creativeAssets/2", None),
        ("dbm", "queries/1:run", {}),
        ("sa360", "customers/1:mutate", {"query": "SELECT campaign.id FROM campaign"}),
        ("sa360", "customers/1/searchAds360:search", {"query": "DELETE FROM campaign"}),
        ("dv360", "advertisers/../users", None),
        ("admin", "organizations?key=secret", None),
        ("sa360", "customers:listAccessibleCustomers", {}),
        ("unknown", "organizations", None),
    ],
)
def test_transport_blocks_non_read_routes_before_auth(monkeypatch, service, path, body):
    get = Mock()
    monkeypatch.setattr(client, "get_credentials", get)
    with pytest.raises(ValueError):
        client.request(service, path, body=body)
    get.assert_not_called()


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "google_request_failed"),
        (401, "oauth_required"),
        (403, "permission_denied"),
        (404, "not_found"),
        (429, "quota_exceeded"),
        (503, "service_unavailable"),
    ],
)
def test_sanitized_errors(transport, status, code):
    _, response = transport
    response.status_code = status
    response.text = "secret-refresh-token and private account data"
    with pytest.raises(client.APIError) as error:
        client.request("admin", "organizations")
    assert client.error_message(error.value).startswith(code)
    assert "secret" not in str(error.value)
    response.iter_content.assert_not_called()


def test_size_bound_and_bad_response(transport, monkeypatch):
    _, response = transport
    monkeypatch.setattr(client, "MAX_RESPONSE_BYTES", 4)
    response.iter_content.return_value = [b"12345"]
    with pytest.raises(ValueError):
        client.request("admin", "organizations")
    response.iter_content.return_value = [b"bad"]
    with pytest.raises(client.APIError):
        client.request("admin", "organizations")
    response.iter_content.return_value = [b"[]"]
    with pytest.raises(client.APIError):
        client.request("admin", "organizations")


def test_disabled_service_does_not_authenticate(monkeypatch, tmp_path):
    monkeypatch.setattr(
        client, "load_settings", lambda: Settings("id", "secret", tmp_path, services=("admin",))
    )
    get = Mock()
    monkeypatch.setattr(client, "get_credentials", get)
    with pytest.raises(ConfigurationError):
        client.request("dv360", "partners")
    get.assert_not_called()


@pytest.mark.parametrize("value", ["../abc", "123/../../x", "12?x=1", "123-456", "-1", ""])
def test_ids_cannot_escape_routes(value):
    with pytest.raises(ValueError):
        client.numeric_id(value)


@pytest.mark.parametrize("size", [0, -1, 201, True])
def test_page_limits(size):
    with pytest.raises(ValueError):
        client.page_params(size, None, maximum=200)


def test_generic_errors_never_expose_exception_text():
    for error in [
        RuntimeError("secret"),
        requests.Timeout("secret"),
        requests.ConnectionError("secret"),
        AuthenticationRequiredError("secret"),
    ]:
        assert "secret" not in client.error_message(error)


def test_oversized_response_has_actionable_error():
    assert client.error_message(client.ResponseTooLargeError()).startswith("response_too_large:")
    assert "page_size" in client.error_message(client.ResponseTooLargeError())


@pytest.mark.parametrize("path", ["userprofiles/1/creatives", "userprofiles/1/creatives/2"])
def test_creative_read_routes(transport, path):
    session, _ = transport
    client.request("cm360", path, params={"ids": ["2", "3"], "active": False})
    assert session.request.call_args.args == ("GET", client.BASE_URLS["cm360"] + path)
    assert session.request.call_args.kwargs["params"] == {"ids": ["2", "3"], "active": "false"}
