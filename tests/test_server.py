import json
import os
import re
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.exceptions import ToolError

from flin_gmp_mcp import server
from flin_gmp_mcp.client import BASE_URLS


@pytest.fixture
def recorded(monkeypatch):
    request = Mock(return_value={"results": [], "nextPageToken": "next-page"})
    monkeypatch.setattr(server, "request", request)
    return request


@pytest.mark.parametrize(
    "name,args,service,path",
    [
        ("list_organizations", {}, "admin", "organizations"),
        (
            "get_organization",
            {"organization": "organizations/abc-123"},
            "admin",
            "organizations/abc-123",
        ),
        (
            "list_analytics_account_links",
            {"organization": "abc"},
            "admin",
            "organizations/abc/analyticsAccountLinks",
        ),
        ("list_dv360_partners", {}, "dv360", "partners"),
        ("list_dv360_advertisers", {"partner_id": "1"}, "dv360", "advertisers"),
        ("get_dv360_advertiser", {"advertiser_id": "1"}, "dv360", "advertisers/1"),
        ("list_dv360_campaigns", {"advertiser_id": "1"}, "dv360", "advertisers/1/campaigns"),
        (
            "list_dv360_insertion_orders",
            {"advertiser_id": "1"},
            "dv360",
            "advertisers/1/insertionOrders",
        ),
        ("list_dv360_line_items", {"advertiser_id": "1"}, "dv360", "advertisers/1/lineItems"),
        ("list_dv360_creatives", {"advertiser_id": "1"}, "dv360", "advertisers/1/creatives"),
        ("list_dv360_report_queries", {}, "dbm", "queries"),
        ("list_dv360_reports", {"query_id": "1"}, "dbm", "queries/1/reports"),
        ("get_dv360_report", {"query_id": "1", "report_id": "2"}, "dbm", "queries/1/reports/2"),
        ("list_cm360_profiles", {}, "cm360", "userprofiles"),
        ("list_cm360_advertisers", {"profile_id": "1"}, "cm360", "userprofiles/1/advertisers"),
        ("list_cm360_campaigns", {"profile_id": "1"}, "cm360", "userprofiles/1/campaigns"),
        ("list_cm360_reports", {"profile_id": "1"}, "cm360", "userprofiles/1/reports"),
        (
            "list_cm360_report_files",
            {"profile_id": "1", "report_id": "2"},
            "cm360",
            "userprofiles/1/reports/2/files",
        ),
        (
            "get_cm360_report_file",
            {"profile_id": "1", "report_id": "2", "file_id": "3"},
            "cm360",
            "userprofiles/1/reports/2/files/3",
        ),
        ("list_sa360_customers", {}, "sa360", "customers:listAccessibleCustomers"),
        ("list_sa360_custom_columns", {"customer_id": "1"}, "sa360", "customers/1/customColumns"),
        (
            "get_sa360_customer_clients",
            {"customer_id": "1"},
            "sa360",
            "customers/1/searchAds360:search",
        ),
        (
            "get_sa360_campaign_performance",
            {"customer_id": "1", "start_date": "2026-10-01", "end_date": "2026-10-15"},
            "sa360",
            "customers/1/searchAds360:search",
        ),
        (
            "query_sa360",
            {"customer_id": "1", "query": "SELECT campaign.id FROM campaign"},
            "sa360",
            "customers/1/searchAds360:search",
        ),
        (
            "search_sa360_fields",
            {"query": "SELECT name WHERE name LIKE 'metrics.%'"},
            "sa360",
            "searchAds360Fields:search",
        ),
    ],
)
def test_every_data_tool_routes_to_correct_product(recorded, name, args, service, path):
    result = getattr(server, name)(**args, account="work")
    assert recorded.call_args.args == (service, path)
    assert recorded.call_args.kwargs["account"] == "work"
    assert result["data"]["nextPageToken"] == "next-page"
    assert result["ok"] is True
    # Independently validate our route/parameters against Google's published contract.
    contracts = json.loads(
        (Path(__file__).parent / "fixtures/google-discovery-contracts.json").read_text()
    )
    kwargs = recorded.call_args.kwargs
    method = "POST" if "body" in kwargs else "GET"
    matches = [
        entry
        for entry in contracts["services"][service]["methods"]
        if entry["method"] == method
        and re.fullmatch(
            re.sub(r"\\\{[^}]+\\\}", r"[^?]+", re.escape(entry["url"])), BASE_URLS[service] + path
        )
    ]
    assert matches, f"No Google API contract matches {method} {service}/{path}"
    assert any(
        set(kwargs.get("params", {})).issubset(entry["query_parameters"])
        and set(kwargs.get("body", {})).issubset(entry["body_parameters"])
        for entry in matches
    )


def test_list_parameters_and_pagination(recorded):
    server.list_dv360_advertisers(
        "123", page_size=10, page_token="next", filter='entityStatus="ENTITY_STATUS_ACTIVE"'
    )
    assert recorded.call_args.kwargs["params"] == {
        "partnerId": "123",
        "pageSize": 10,
        "pageToken": "next",
        "filter": 'entityStatus="ENTITY_STATUS_ACTIVE"',
    }
    server.list_cm360_campaigns("1", advertiser_id="2", archived=False, page_token="next")
    params = recorded.call_args.kwargs["params"]
    assert params["maxResults"] == 100 and params["advertiserIds"] == "2"
    assert params["archived"] is False and params["pageToken"] == "next"


def test_campaign_query_includes_currency_dates_and_paging(recorded):
    server.get_sa360_campaign_performance(
        "1", "2026-01-01", "2026-01-31", True, page_token="next", login_customer_id="2"
    )
    kwargs = recorded.call_args.kwargs
    assert kwargs["login_customer_id"] == "2"
    assert kwargs["body"]["pageToken"] == "next"
    query = kwargs["body"]["query"]
    assert "customer.currency_code" in query and "metrics.cost_micros" in query
    assert "segments.date FROM" in query
    assert "BETWEEN '2026-01-01' AND '2026-01-31'" in query


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-02-30", "2026-03-01"),
        ("2026-10-10", "2026-01-01"),
        ("2026-01-01' OR 1=1", "2026-01-31"),
    ],
)
def test_invalid_dates_never_reach_google(recorded, start, end):
    with pytest.raises(ToolError, match="invalid_arguments"):
        server.get_sa360_campaign_performance("1", start, end)
    recorded.assert_not_called()


async def test_schema_annotations_and_validation(recorded):
    tools = await server.mcp.list_tools()
    assert len(tools) == 27
    for tool in tools:
        assert tool.annotations.readOnlyHint is (tool.name != "authenticate")
        assert tool.annotations.destructiveHint is False
        if tool.name == "health_check":
            assert tool.annotations.openWorldHint is False
    with pytest.raises(ToolError):
        await server.mcp.call_tool("list_cm360_reports", {"profile_id": "1", "scope": "INVALID"})
    recorded.assert_not_called()


async def test_stdio_handshake_and_missing_config_without_google():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GOOGLE_")}
    params = StdioServerParameters(command=sys.executable, args=["-m", "flin_gmp_mcp"], env=env)
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        init = await session.initialize()
        assert init.serverInfo.name == "flin-gmp-mcp"
        listed = await session.list_tools()
        assert len(listed.tools) == 27
        health = await session.call_tool("health_check", {})
        assert not health.isError
        assert "missing_configuration" in health.content[0].text
        failure = await session.call_tool("get_organization", {"organization": "../bad"})
        assert failure.isError
        assert "invalid_arguments" in failure.content[0].text
