import sqlite3
from typing import Any

from integrations.cpq.catalog import list_catalog_items


ACCOUNTS: tuple[dict[str, Any], ...] = (
    {
        "sf_account_id": "SF-ACC-001",
        "name": "Northstar Telecom",
        "industry": "Telecommunications",
        "region": "North America",
        "segment": "Tier 1 Carrier",
    },
    {
        "sf_account_id": "SF-ACC-002",
        "name": "MetroWave Communications",
        "industry": "Telecommunications",
        "region": "EMEA",
        "segment": "Regional Operator",
    },
    {
        "sf_account_id": "SF-ACC-003",
        "name": "Apex Mobile Networks",
        "industry": "Telecommunications",
        "region": "APAC",
        "segment": "Mobile Network Operator",
    },
    {
        "sf_account_id": "SF-ACC-004",
        "name": "BluePeak Fiber",
        "industry": "Telecommunications",
        "region": "North America",
        "segment": "Fiber Broadband",
    },
    {
        "sf_account_id": "SF-ACC-005",
        "name": "HelioLink Wireless",
        "industry": "Telecommunications",
        "region": "LATAM",
        "segment": "Wireless Operator",
    },
)


OPPORTUNITIES: tuple[dict[str, Any], ...] = (
    {
        "sf_opportunity_id": "SF-OPP-001",
        "sf_account_id": "SF-ACC-001",
        "name": "5G Edge Data Infrastructure Modernization",
        "stage": "Proposal",
        "currency": "USD",
        "amount": 1750000.0,
        "term_months": 36,
        "use_case": "telecom_data_infrastructure_modernization",
        "sites": 12,
        "region": "North America",
        "budget": 1800000.0,
        "target_close_date": "2026-06-30",
        "compliance_need": "Low-latency SLA and operational resilience",
        "incumbent_vendor": "Legacy SAN estate",
        "risk_level": "Medium",
        "requirements": (
            "low latency storage for 5G edge applications",
            "block storage for billing databases and subscriber systems",
            "object storage for telemetry logs CDR archive and analytics data lake",
            "hybrid cloud disaster recovery for ONTAP workloads",
            "centralized management across edge and core environments",
            "premium support for mission-critical telecom operations",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-002",
        "sf_account_id": "SF-ACC-001",
        "name": "Core Billing Storage Refresh",
        "stage": "Negotiation",
        "currency": "USD",
        "amount": 920000.0,
        "term_months": 24,
        "use_case": "telecom_billing_storage_refresh",
        "sites": 3,
        "region": "North America",
        "budget": 950000.0,
        "target_close_date": "2026-05-28",
        "compliance_need": "Billing availability and recovery point objective",
        "incumbent_vendor": "Mixed block arrays",
        "risk_level": "High",
        "requirements": (
            "block storage for billing database refresh",
            "subscriber systems storage with low latency service levels",
            "hybrid cloud disaster recovery for billing workloads",
            "professional services for migration planning",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-003",
        "sf_account_id": "SF-ACC-001",
        "name": "AI Network Operations Data Lake",
        "stage": "Discovery",
        "currency": "USD",
        "amount": 1320000.0,
        "term_months": 36,
        "use_case": "telecom_ai_network_analytics",
        "sites": 6,
        "region": "North America",
        "budget": 1400000.0,
        "target_close_date": "2026-08-15",
        "compliance_need": "Data retention and analytics governance",
        "incumbent_vendor": "Cloud object storage pilot",
        "risk_level": "Medium",
        "requirements": (
            "telemetry logs and analytics data lake",
            "object storage for network operations AI",
            "centralized management for storage operations",
            "hybrid cloud disaster recovery for analytics copies",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-004",
        "sf_account_id": "SF-ACC-002",
        "name": "Regional Network Analytics Archive",
        "stage": "Discovery",
        "currency": "USD",
        "amount": 650000.0,
        "term_months": 24,
        "use_case": "telecom_object_archive_and_analytics",
        "sites": 4,
        "region": "EMEA",
        "budget": 700000.0,
        "target_close_date": "2026-07-10",
        "compliance_need": "CDR and telemetry retention",
        "incumbent_vendor": "Tape archive",
        "risk_level": "Low",
        "requirements": (
            "object storage for telemetry logs and archive",
            "analytics data lake for network operations",
            "centralized management for storage operations",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-005",
        "sf_account_id": "SF-ACC-002",
        "name": "Edge Cloud Expansion Wave 2",
        "stage": "Proposal",
        "currency": "USD",
        "amount": 1250000.0,
        "term_months": 36,
        "use_case": "telecom_edge_cloud_expansion",
        "sites": 8,
        "region": "EMEA",
        "budget": 1300000.0,
        "target_close_date": "2026-06-18",
        "compliance_need": "Customer-facing network resilience",
        "incumbent_vendor": "Legacy appliance cluster",
        "risk_level": "Medium",
        "requirements": (
            "low latency storage for new 5G edge zones",
            "hybrid cloud disaster recovery",
            "centralized management for edge and cloud environments",
            "premium support for customer-facing network services",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-006",
        "sf_account_id": "SF-ACC-002",
        "name": "Subscriber Systems VMware Refresh",
        "stage": "Procurement",
        "currency": "USD",
        "amount": 780000.0,
        "term_months": 24,
        "use_case": "telecom_subscriber_vmware_refresh",
        "sites": 2,
        "region": "EMEA",
        "budget": 800000.0,
        "target_close_date": "2026-05-20",
        "compliance_need": "Subscriber data availability",
        "incumbent_vendor": "Aging VMware datastore",
        "risk_level": "High",
        "requirements": (
            "block storage for subscriber systems",
            "VMware datastore modernization",
            "professional services for migration planning",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-007",
        "sf_account_id": "SF-ACC-003",
        "name": "National CDR Retention Platform",
        "stage": "Solution Design",
        "currency": "USD",
        "amount": 2400000.0,
        "term_months": 48,
        "use_case": "telecom_cdr_retention_platform",
        "sites": 16,
        "region": "APAC",
        "budget": 2500000.0,
        "target_close_date": "2026-09-30",
        "compliance_need": "Regulated CDR retention",
        "incumbent_vendor": "On-prem object archive",
        "risk_level": "Medium",
        "requirements": (
            "object storage for CDR retention and archive",
            "telemetry logs and analytics data lake",
            "hybrid cloud disaster recovery for compliance copies",
            "centralized management across national network regions",
            "premium support for regulated data services",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-008",
        "sf_account_id": "SF-ACC-003",
        "name": "Mobile Packet Core DR",
        "stage": "Proposal",
        "currency": "USD",
        "amount": 1680000.0,
        "term_months": 36,
        "use_case": "telecom_packet_core_dr",
        "sites": 5,
        "region": "APAC",
        "budget": 1750000.0,
        "target_close_date": "2026-07-22",
        "compliance_need": "Disaster recovery for packet core services",
        "incumbent_vendor": "Cloud DR proof of concept",
        "risk_level": "Medium",
        "requirements": (
            "hybrid cloud disaster recovery",
            "low latency storage for packet core systems",
            "premium support for mission-critical operations",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-009",
        "sf_account_id": "SF-ACC-004",
        "name": "Fiber OSS Data Platform",
        "stage": "Discovery",
        "currency": "USD",
        "amount": 880000.0,
        "term_months": 24,
        "use_case": "fiber_oss_data_platform",
        "sites": 7,
        "region": "North America",
        "budget": 900000.0,
        "target_close_date": "2026-08-05",
        "compliance_need": "OSS telemetry retention",
        "incumbent_vendor": "NAS cluster",
        "risk_level": "Low",
        "requirements": (
            "object storage for telemetry logs",
            "analytics data lake for operations",
            "centralized management",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-010",
        "sf_account_id": "SF-ACC-004",
        "name": "Metro Edge Performance Storage",
        "stage": "Negotiation",
        "currency": "USD",
        "amount": 1120000.0,
        "term_months": 36,
        "use_case": "fiber_metro_edge_storage",
        "sites": 10,
        "region": "North America",
        "budget": 1150000.0,
        "target_close_date": "2026-06-12",
        "compliance_need": "Edge service performance SLA",
        "incumbent_vendor": "Direct attached storage",
        "risk_level": "Medium",
        "requirements": (
            "low latency storage for edge applications",
            "centralized management across edge environments",
            "premium support",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-011",
        "sf_account_id": "SF-ACC-005",
        "name": "Wireless Billing Consolidation",
        "stage": "Procurement",
        "currency": "USD",
        "amount": 1040000.0,
        "term_months": 36,
        "use_case": "wireless_billing_consolidation",
        "sites": 4,
        "region": "LATAM",
        "budget": 1100000.0,
        "target_close_date": "2026-05-30",
        "compliance_need": "Billing database consolidation",
        "incumbent_vendor": "Multiple storage vendors",
        "risk_level": "High",
        "requirements": (
            "block storage for billing databases",
            "subscriber systems storage",
            "hybrid cloud disaster recovery",
            "professional services for deployment",
        ),
    },
    {
        "sf_opportunity_id": "SF-OPP-012",
        "sf_account_id": "SF-ACC-005",
        "name": "5G Telemetry Archive",
        "stage": "Closed Won",
        "currency": "USD",
        "amount": 720000.0,
        "term_months": 24,
        "use_case": "wireless_5g_telemetry_archive",
        "sites": 5,
        "region": "LATAM",
        "budget": 760000.0,
        "target_close_date": "2026-04-10",
        "compliance_need": "Telemetry archive retention",
        "incumbent_vendor": "Legacy archive software",
        "risk_level": "Low",
        "requirements": (
            "object storage for telemetry logs",
            "CDR archive",
            "centralized management",
        ),
    },
)


QUOTE_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "oracle_quote_id": "ORA-Q-001-000",
        "sf_opportunity_id": "SF-OPP-001",
        "status": "SUPERSEDED",
        "currency": "USD",
        "subtotal": 1480000.0,
        "discount": 185000.0,
        "discount_percent": 12.5,
        "total": 1295000.0,
        "selected_product_count": 3,
        "created_at": "2026-04-25T16:00:00Z",
        "line_items": (
            {
                "sku": "NTAP-AFF-A-SERIES",
                "name": "AFF A-Series Performance Storage",
                "category": "performance_storage",
                "quantity": 2,
                "term_months": 36,
                "billing_model": "annual",
                "annual_unit_price": 110000.0,
                "net_price": 660000.0,
            },
            {
                "sku": "NTAP-STORAGEGRID",
                "name": "StorageGRID Object Storage",
                "category": "object_storage",
                "quantity": 2,
                "term_months": 36,
                "billing_model": "annual",
                "annual_unit_price": 75000.0,
                "net_price": 450000.0,
            },
            {
                "sku": "NTAP-CVO",
                "name": "Cloud Volumes ONTAP",
                "category": "hybrid_cloud",
                "quantity": 1,
                "term_months": 36,
                "billing_model": "annual",
                "annual_unit_price": 55000.0,
                "net_price": 165000.0,
            },
        ),
    },
    {
        "oracle_quote_id": "ORA-Q-004-000",
        "sf_opportunity_id": "SF-OPP-004",
        "status": "DRAFT",
        "currency": "USD",
        "subtotal": 420000.0,
        "discount": 0.0,
        "discount_percent": 0.0,
        "total": 420000.0,
        "selected_product_count": 2,
        "created_at": "2026-04-26T10:30:00Z",
        "line_items": (
            {
                "sku": "NTAP-STORAGEGRID",
                "name": "StorageGRID Object Storage",
                "category": "object_storage",
                "quantity": 2,
                "term_months": 24,
                "billing_model": "annual",
                "annual_unit_price": 75000.0,
                "net_price": 300000.0,
            },
            {
                "sku": "NTAP-CONSOLE-OPS",
                "name": "NetApp Console Operations Package",
                "category": "management",
                "quantity": 1,
                "term_months": 24,
                "billing_model": "annual",
                "annual_unit_price": 30000.0,
                "net_price": 60000.0,
            },
        ),
    },
    {
        "oracle_quote_id": "ORA-Q-012-001",
        "sf_opportunity_id": "SF-OPP-012",
        "status": "ACCEPTED",
        "currency": "USD",
        "subtotal": 420000.0,
        "discount": 0.0,
        "discount_percent": 0.0,
        "total": 420000.0,
        "selected_product_count": 2,
        "created_at": "2026-04-10T14:45:00Z",
        "accepted_at": "2026-04-12T09:00:00Z",
        "line_items": (
            {
                "sku": "NTAP-STORAGEGRID",
                "name": "StorageGRID Object Storage",
                "category": "object_storage",
                "quantity": 2,
                "term_months": 24,
                "billing_model": "annual",
                "annual_unit_price": 75000.0,
                "net_price": 300000.0,
            },
            {
                "sku": "NTAP-CONSOLE-OPS",
                "name": "NetApp Console Operations Package",
                "category": "management",
                "quantity": 1,
                "term_months": 24,
                "billing_model": "annual",
                "annual_unit_price": 30000.0,
                "net_price": 60000.0,
            },
        ),
    },
)


ORDER_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "oracle_order_id": "ORA-O-012-001",
        "oracle_quote_id": "ORA-Q-012-001",
        "sf_opportunity_id": "SF-OPP-012",
        "status": "PLACED",
        "currency": "USD",
        "total": 420000.0,
        "placed_at": "2026-04-12T09:05:00Z",
    },
)


def seed_if_empty(connection: sqlite3.Connection) -> None:
    has_accounts = connection.execute("SELECT 1 FROM accounts LIMIT 1").fetchone()
    if has_accounts:
        return

    _seed_accounts(connection)
    _seed_opportunities(connection)
    _seed_products(connection)
    _seed_pricing_rules(connection)
    _seed_quotes(connection)
    _seed_orders(connection)
    _seed_activity(connection)


def _seed_accounts(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO accounts (sf_account_id, name, industry, region, segment)
        VALUES (:sf_account_id, :name, :industry, :region, :segment)
        """,
        ACCOUNTS,
    )


def _seed_opportunities(connection: sqlite3.Connection) -> None:
    for opportunity in OPPORTUNITIES:
        connection.execute(
            """
            INSERT INTO opportunities (
                sf_opportunity_id, sf_account_id, name, stage, currency, amount,
                term_months, use_case, sites, region, budget, target_close_date,
                compliance_need, incumbent_vendor, risk_level
            )
            VALUES (
                :sf_opportunity_id, :sf_account_id, :name, :stage, :currency,
                :amount, :term_months, :use_case, :sites, :region, :budget,
                :target_close_date, :compliance_need, :incumbent_vendor, :risk_level
            )
            """,
            opportunity,
        )
        connection.executemany(
            """
            INSERT INTO opportunity_requirements (sf_opportunity_id, requirement)
            VALUES (?, ?)
            """,
            [
                (opportunity["sf_opportunity_id"], requirement)
                for requirement in opportunity["requirements"]
            ],
        )


def _seed_products(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO products (
            sku, name, category, annual_unit_price, billing_model, description
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.sku,
                item.name,
                item.category,
                item.annual_unit_price,
                item.billing_model,
                item.description,
            )
            for item in list_catalog_items()
        ],
    )


def _seed_pricing_rules(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO pricing_rules (code, label, percent, condition_text)
        VALUES (?, ?, ?, ?)
        """,
        (
            (
                "TERM-36",
                "36-month telecom modernization commitment",
                10.0,
                "Applies when selected line-item term is at least 36 months.",
            ),
            (
                "TELCO-BUNDLE",
                "Multi-platform telecom bundle",
                5.0,
                "Applies when at least three infrastructure platforms are selected.",
            ),
        ),
    )


def _seed_quotes(connection: sqlite3.Connection) -> None:
    for quote in QUOTE_SEEDS:
        connection.execute(
            """
            INSERT INTO quotes (
                oracle_quote_id, sf_opportunity_id, status, currency, subtotal,
                discount, discount_percent, total, selected_product_count,
                created_at, accepted_at
            )
            VALUES (
                :oracle_quote_id, :sf_opportunity_id, :status, :currency,
                :subtotal, :discount, :discount_percent, :total,
                :selected_product_count, :created_at, :accepted_at
            )
            """,
            {
                **quote,
                "accepted_at": quote.get("accepted_at"),
            },
        )
        connection.executemany(
            """
            INSERT INTO quote_line_items (
                oracle_quote_id, sku, name, category, quantity, term_months,
                billing_model, annual_unit_price, net_price
            )
            VALUES (
                :oracle_quote_id, :sku, :name, :category, :quantity,
                :term_months, :billing_model, :annual_unit_price, :net_price
            )
            """,
            [
                {"oracle_quote_id": quote["oracle_quote_id"], **line_item}
                for line_item in quote["line_items"]
            ],
        )


def _seed_orders(connection: sqlite3.Connection) -> None:
    for order in ORDER_SEEDS:
        connection.execute(
            """
            INSERT INTO orders (
                oracle_order_id, oracle_quote_id, sf_opportunity_id, status,
                currency, total, placed_at
            )
            VALUES (
                :oracle_order_id, :oracle_quote_id, :sf_opportunity_id, :status,
                :currency, :total, :placed_at
            )
            """,
            order,
        )
        line_items = connection.execute(
            """
            SELECT sku, name, category, quantity, term_months, billing_model,
                   annual_unit_price, net_price
            FROM quote_line_items
            WHERE oracle_quote_id = ?
            """,
            (order["oracle_quote_id"],),
        ).fetchall()
        connection.executemany(
            """
            INSERT INTO order_line_items (
                oracle_order_id, sku, name, category, quantity, term_months,
                billing_model, annual_unit_price, net_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    order["oracle_order_id"],
                    item["sku"],
                    item["name"],
                    item["category"],
                    item["quantity"],
                    item["term_months"],
                    item["billing_model"],
                    item["annual_unit_price"],
                    item["net_price"],
                )
                for item in line_items
            ],
        )


def _seed_activity(connection: sqlite3.Connection) -> None:
    events = [
        (
            "ACT-SF-OPP-001-001",
            "SF-ACC-001",
            "SF-OPP-001",
            None,
            None,
            "Salesforce CRM Cloud",
            "opportunity_loaded",
            "Opportunity synced from Salesforce",
            "Loaded Northstar Telecom 5G edge modernization opportunity.",
            "2026-04-25T15:40:00Z",
        ),
        (
            "ACT-SF-OPP-001-002",
            "SF-ACC-001",
            "SF-OPP-001",
            "ORA-Q-001-000",
            None,
            "Oracle CPQ Cloud",
            "quote_created",
            "Initial quote version created",
            "Oracle CPQ created ORA-Q-001-000.",
            "2026-04-25T16:00:00Z",
        ),
        (
            "ACT-SF-OPP-012-001",
            "SF-ACC-005",
            "SF-OPP-012",
            "ORA-Q-012-001",
            "ORA-O-012-001",
            "Oracle CPQ Cloud",
            "order_placed",
            "Order placed from accepted quote",
            "Oracle CPQ placed ORA-O-012-001.",
            "2026-04-12T09:05:00Z",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO activity_events (
            activity_id, sf_account_id, sf_opportunity_id, oracle_quote_id,
            oracle_order_id, system, event_type, title, detail, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )
