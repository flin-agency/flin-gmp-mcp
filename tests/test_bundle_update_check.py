import pytest

from scripts.check_mcpb import validate_runtime


def test_update_check_rejects_working_bundled_fallback():
    with pytest.raises(RuntimeError, match="fallback"):
        validate_runtime(
            {"version": "0.1.5"},
            "flin-gmp-mcp: starting bundled runtime 0.1.5\n",
            auto_update=True,
            expected_version="0.1.5",
        )


def test_update_check_rejects_old_pypi_runtime():
    with pytest.raises(RuntimeError, match="Expected server"):
        validate_runtime(
            {"version": "0.1.4"},
            "flin-gmp-mcp: starting PyPI runtime 0.1.4\n",
            auto_update=True,
            expected_version="0.1.5",
        )


def test_update_check_requires_matching_launch_and_runtime_version():
    with pytest.raises(RuntimeError, match="did not start"):
        validate_runtime(
            {"version": "0.1.5"},
            "flin-gmp-mcp: starting PyPI runtime 0.1.50\n",
            auto_update=True,
            expected_version="0.1.5",
        )


def test_old_bundle_can_confirm_new_pypi_server():
    assert (
        validate_runtime(
            {"version": "0.1.5"},
            "flin-gmp-mcp: starting PyPI runtime 0.1.5\n",
            auto_update=True,
            expected_version="0.1.5",
        )
        == "0.1.5"
    )


def test_bundled_check_still_works_before_pypi_publication():
    assert (
        validate_runtime(
            {"version": "0.1.5"},
            "flin-gmp-mcp: starting bundled runtime 0.1.5\n",
            auto_update=False,
            expected_version="0.1.5",
        )
        == "0.1.5"
    )


def test_cached_fallback_cannot_pass_online_release_verification():
    with pytest.raises(RuntimeError, match="fallback"):
        validate_runtime(
            {"version": "0.1.6", "fallback_active": True},
            "flin-gmp-mcp: starting PyPI runtime 0.1.6\n",
            auto_update=True,
            expected_version="0.1.6",
        )
