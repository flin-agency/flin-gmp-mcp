from unittest.mock import Mock

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from flin_gmp_mcp import client, reporting, server


def test_creation_and_async_run(monkeypatch):
    request = Mock(return_value={"queryId": "123"})
    monkeypatch.setattr(server, "request", request)
    server.create_dv360_report_query("Yesterday", "42", account="work")
    assert request.call_args.args == ("dbm", "queries")
    body = request.call_args.kwargs["body"]
    assert body["metadata"] == {
        "title": "Yesterday",
        "dataRange": {"range": "PREVIOUS_DAY"},
        "format": "CSV",
        "sendNotification": False,
    }
    assert body["params"]["filters"] == [{"type": "FILTER_ADVERTISER", "value": "42"}]
    assert body["schedule"] == {"frequency": "ONE_TIME"}
    assert request.call_args.kwargs["account"] == "work"
    server.run_dv360_report("123")
    assert request.call_args.args == ("dbm", "queries/123:run")
    assert request.call_args.kwargs["params"] == {"synchronous": False}
    assert request.call_args.kwargs["body"] == {}
    server.run_dv360_report("123", "2026-11-01", "2026-11-02")
    assert request.call_args.kwargs["body"]["dataRange"]["customEndDate"]["day"] == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"advertiser_id": "../42"},
        {"title": " "},
        {"metrics": []},
        {"metrics": ["clicks"]},
        {"dimensions": ["bad"]},
        {"start_date": "2026-11-01"},
        {"start_date": "2026-11-02", "end_date": "2026-11-01"},
        {"start_date": "2026-02-30", "end_date": "2026-11-01"},
    ],
)
def test_invalid_report_never_reaches_google(monkeypatch, kwargs):
    request = Mock()
    monkeypatch.setattr(server, "request", request)
    with pytest.raises(ToolError, match="invalid_arguments"):
        server.create_dv360_report_query(**{"title": "Report", "advertiser_id": "42", **kwargs})
    request.assert_not_called()


@pytest.fixture
def report(monkeypatch):
    value = {
        "metadata": {
            "status": {"state": "DONE", "format": "CSV"},
            "googleCloudStoragePath": "https://storage.googleapis.com/bucket/report",
        }
    }
    monkeypatch.setattr(reporting, "request", Mock(return_value=value))
    return value


def test_csv_pagination_preserves_values_and_footer(monkeypatch, report):
    monkeypatch.setattr(
        reporting,
        "download_csv",
        Mock(
            return_value=(
                'Name,Cost\r\n"Line, one",1.2300\r\nTotal,1.2300\r\n\r\nReport generated,x\r\n'
            )
        ),
    )
    result = reporting.read_report("1", "2", "work", 0, 2)
    assert result["rows"] == [["Name", "Cost"], ["Line, one", "1.2300"]]
    assert result["next_row_offset"] == 2
    result = reporting.read_report("1", "2", "work", 2, 100)
    assert result["rows"] == [["Total", "1.2300"], [], ["Report generated", "x"]]
    assert result["next_row_offset"] is None
    assert reporting.request.call_args.kwargs["account"] == "work"


@pytest.mark.parametrize("state", ["QUEUED", "RUNNING", "FAILED", "STATE_UNSPECIFIED"])
def test_unfinished_report_does_not_download(monkeypatch, report, state):
    report["metadata"]["status"]["state"] = state
    download = Mock()
    monkeypatch.setattr(reporting, "download_csv", download)
    assert reporting.read_report("1", "2", None, 0, 100)["ready"] is False
    download.assert_not_called()


def test_non_csv_rejected(report):
    report["metadata"]["status"]["format"] = "XLSX"
    with pytest.raises(ValueError):
        reporting.read_report("1", "2", None, 0, 100)


@pytest.mark.parametrize(
    "url",
    [
        "http://storage.googleapis.com/b/r",
        "https://evil.example/r",
        "https://storage.googleapis.com.evil.example/r",
        "http://127.0.0.1/r",
        "https://user:secret@storage.googleapis.com/b/r",
        "file:///etc/passwd",
        "https://storage.googleapis.com:444/b/r",
        "https://storage.googleapis.com/",
    ],
)
def test_download_rejects_unsafe_urls_before_network(monkeypatch, url):
    session = Mock()
    monkeypatch.setattr(reporting.requests, "Session", session)
    with pytest.raises(ValueError):
        reporting.download_csv(url)
    session.assert_not_called()


def test_download_bounded_no_redirects_or_credentials(monkeypatch):
    response = Mock(status_code=200)
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.iter_content.return_value = [b"\xef\xbb\xbfA,B\n1,2"]
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.get.return_value = response
    monkeypatch.setattr(reporting.requests, "Session", Mock(return_value=session))
    url = "https://storage.googleapis.com/bucket/report"
    assert reporting.download_csv(url) == "A,B\n1,2"
    assert session.trust_env is False
    assert session.get.call_args.kwargs == {
        "timeout": (10, 60),
        "stream": True,
        "allow_redirects": False,
    }
    response.status_code = 302
    with pytest.raises(client.APIError):
        reporting.download_csv(url)
    response.status_code = 200
    monkeypatch.setattr(reporting, "MAX_RESPONSE_BYTES", 2)
    with pytest.raises(client.ResponseTooLargeError):
        reporting.download_csv(url)


async def test_report_write_annotations():
    for tool in await server.mcp.list_tools():
        if tool.name in {"create_dv360_report_query", "run_dv360_report"}:
            assert tool.annotations.readOnlyHint is False
            assert tool.annotations.idempotentHint is False
            assert tool.annotations.destructiveHint is False
