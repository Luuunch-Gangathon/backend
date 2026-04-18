"""Tests for material name normalization."""

from __future__ import annotations


def test_basic_normalization():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C52-magnesium-stearate-c3a91d20") == "magnesium stearate"


def test_long_name():
    from app.api.search_engine.normalizer import normalize_sku

    result = normalize_sku(
        "RM-C47-organic-dairy-whey-protein-concentrate-380e0c61"
    )
    assert result == "organic dairy whey protein concentrate"


def test_single_word_name():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C62-salt-8c7e3d71") == "salt"


def test_double_digit_company():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C17-cupric-oxide-95cf9a6a") == "cupric oxide"


def test_name_with_numbers():
    from app.api.search_engine.normalizer import normalize_sku

    assert normalize_sku("RM-C40-l-leucine-dc251fa2") == "l leucine"


def test_normalize_raw_fields():
    from app.api.search_engine.normalizer import normalize

    fields = {
        "SKU": "RM-C5-magnesium-stearate-c3a91d20",
        "CompanyId": 5,
        "Id": 42,
    }
    result = normalize(fields)
    assert result["normalized_name"] == "magnesium stearate"
    assert result["material_id"] == "ing_db_42"
    assert result["company_id"] == "co_db_5"
    assert result["raw_sku"] == "RM-C5-magnesium-stearate-c3a91d20"


def test_normalize_includes_supplier_ids():
    from app.api.search_engine.normalizer import normalize

    fields = {
        "SKU": "RM-C5-magnesium-stearate-c3a91d20",
        "CompanyId": 5,
        "Id": 42,
        "SupplierIds": [12, 7],
    }
    result = normalize(fields)
    assert result["supplier_ids"] == ["sup_db_12", "sup_db_7"]


def test_normalize_no_suppliers():
    from app.api.search_engine.normalizer import normalize

    fields = {"SKU": "RM-C1-test-abcd1234", "CompanyId": 1, "Id": 1}
    result = normalize(fields)
    assert result["supplier_ids"] == []
