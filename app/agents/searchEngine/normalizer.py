"""Material name normalization — extracts clean name from raw DB fields.

SKU format: RM-C{companyNum}-{material-name}-{8char-hex-hash}
"""

from __future__ import annotations

import re


def normalize_sku(sku: str) -> str:
    """Extract clean material name from a raw SKU string."""
    # Strip prefix: RM-C{digits}-
    without_prefix = re.sub(r"^RM-C\d+-", "", sku)
    # Strip suffix: -{8 hex chars} at end
    without_hash = re.sub(r"-[0-9a-f]{8}$", "", without_prefix)
    # Replace hyphens with spaces
    return without_hash.replace("-", " ")


def normalize(raw_fields: dict) -> dict:
    """Normalize raw DB fields into a clean context dict for the engine."""
    supplier_ids_raw = raw_fields.get("SupplierIds", [])
    return {
        "material_id": f"ing_db_{raw_fields['Id']}",
        "raw_sku": raw_fields["SKU"],
        "normalized_name": normalize_sku(raw_fields["SKU"]),
        "company_id": f"co_db_{raw_fields['CompanyId']}",
        "supplier_ids": [f"sup_db_{sid}" for sid in supplier_ids_raw],
    }
