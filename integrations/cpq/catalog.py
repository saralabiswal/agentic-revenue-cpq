"""Mock Oracle CPQ product catalog used by recommendation and pricing flows.

Author: Sarala Biswal
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductCatalogItem:
    """Catalog record describing a sellable CPQ product and its pricing metadata."""
    sku: str
    name: str
    category: str
    annual_unit_price: float
    billing_model: str
    description: str


PRODUCT_CATALOG: dict[str, ProductCatalogItem] = {
    "NTAP-AFF-A-SERIES": ProductCatalogItem(
        sku="NTAP-AFF-A-SERIES",
        name="AFF A-Series Performance Storage",
        category="performance_storage",
        annual_unit_price=110000.0,
        billing_model="annual",
        description="High-performance ONTAP storage for low-latency edge and core workloads.",
    ),
    "NTAP-ASA-A-SERIES": ProductCatalogItem(
        sku="NTAP-ASA-A-SERIES",
        name="ASA A-Series Block Storage",
        category="block_storage",
        annual_unit_price=95000.0,
        billing_model="annual",
        description="Dedicated block storage for billing, subscriber, database, and VMware workloads.",
    ),
    "NTAP-STORAGEGRID": ProductCatalogItem(
        sku="NTAP-STORAGEGRID",
        name="StorageGRID Object Storage",
        category="object_storage",
        annual_unit_price=75000.0,
        billing_model="annual",
        description="S3-compatible object storage for telemetry, logs, CDR, archive, and data lakes.",
    ),
    "NTAP-CVO": ProductCatalogItem(
        sku="NTAP-CVO",
        name="Cloud Volumes ONTAP",
        category="hybrid_cloud",
        annual_unit_price=55000.0,
        billing_model="annual",
        description="Hybrid cloud data mobility and disaster recovery for ONTAP workloads.",
    ),
    "NTAP-CONSOLE-OPS": ProductCatalogItem(
        sku="NTAP-CONSOLE-OPS",
        name="NetApp Console Operations Package",
        category="management",
        annual_unit_price=30000.0,
        billing_model="annual",
        description="Centralized management, governance, and operations for the NetApp estate.",
    ),
    "NTAP-PRO-SERVICES": ProductCatalogItem(
        sku="NTAP-PRO-SERVICES",
        name="Professional Services Deployment",
        category="services",
        annual_unit_price=65000.0,
        billing_model="one_time",
        description="Architecture, deployment, migration planning, and operational handoff.",
    ),
    "NTAP-PREMIUM-SUPPORT": ProductCatalogItem(
        sku="NTAP-PREMIUM-SUPPORT",
        name="Premium Support Plan",
        category="support",
        annual_unit_price=45000.0,
        billing_model="annual",
        description="Enhanced support coverage for mission-critical telecom platforms.",
    ),
}


def get_catalog_item(sku: str) -> ProductCatalogItem | None:
    """Return one catalog item by SKU, or None when the SKU is unknown."""
    return PRODUCT_CATALOG.get(sku)


def list_catalog_items() -> list[ProductCatalogItem]:
    """Return all mock CPQ catalog items in their configured order."""
    return list(PRODUCT_CATALOG.values())
