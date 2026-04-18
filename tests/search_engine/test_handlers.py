"""Tests for source handler stubs."""

from __future__ import annotations


def test_handler_registry_has_all_sources():
    from app.agents.searchEngine.config import SOURCES
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS

    for source in SOURCES:
        assert source["name"] in SOURCE_HANDLERS, (
            f"Missing handler for source '{source['name']}'"
        )


def test_all_handlers_are_callable():
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS

    for name, handler in SOURCE_HANDLERS.items():
        assert callable(handler), f"Handler '{name}' is not callable"


def test_stub_handler_returns_list():
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS

    for name, handler in SOURCE_HANDLERS.items():
        result = handler("magnesium stearate", {})
        assert isinstance(result, list), (
            f"Handler '{name}' should return a list, got {type(result)}"
        )


def test_stub_handler_result_items_have_required_keys():
    from app.agents.searchEngine.handlers import SOURCE_HANDLERS

    required_keys = {"property", "value", "source_url", "raw_excerpt"}
    for name, handler in SOURCE_HANDLERS.items():
        results = handler("magnesium stearate", {})
        for item in results:
            assert required_keys.issubset(item.keys()), (
                f"Handler '{name}' result missing keys: {required_keys - item.keys()}"
            )
