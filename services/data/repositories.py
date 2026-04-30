from __future__ import annotations

from datetime import UTC, datetime
import re
import uuid
from typing import Any

from services.data.database import connect, initialize_database, reset_database


def reset_business_data() -> None:
    reset_database()


def list_accounts() -> list[dict[str, Any]]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                a.sf_account_id,
                a.name,
                a.industry,
                a.region,
                a.segment,
                COUNT(o.sf_opportunity_id) AS opportunity_count,
                COALESCE(SUM(o.amount), 0) AS open_pipeline
            FROM accounts a
            LEFT JOIN opportunities o ON o.sf_account_id = a.sf_account_id
            GROUP BY a.sf_account_id
            ORDER BY a.sf_account_id
            """
        ).fetchall()

    return [_row(row) for row in rows]


def list_opportunities(sf_account_id: str | None = None) -> list[dict[str, Any]]:
    initialize_database()
    params: tuple[Any, ...] = ()
    where = ""
    if sf_account_id:
        where = "WHERE o.sf_account_id = ?"
        params = (sf_account_id,)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT o.*, a.name AS account_name, a.industry AS account_industry,
                   a.region AS account_region, a.segment AS account_segment
            FROM opportunities o
            JOIN accounts a ON a.sf_account_id = o.sf_account_id
            {where}
            ORDER BY o.target_close_date, o.sf_opportunity_id
            """,
            params,
        ).fetchall()

    return [_opportunity_from_row(row) for row in rows]


def get_opportunity(sf_opportunity_id: str) -> dict[str, Any] | None:
    initialize_database()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT o.*, a.name AS account_name, a.industry AS account_industry,
                   a.region AS account_region, a.segment AS account_segment
            FROM opportunities o
            JOIN accounts a ON a.sf_account_id = o.sf_account_id
            WHERE o.sf_opportunity_id = ?
            """,
            (sf_opportunity_id,),
        ).fetchone()

    if row is None:
        return None

    return _opportunity_from_row(row)


def list_quotes(sf_opportunity_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM quotes
            WHERE sf_opportunity_id = ?
            ORDER BY created_at, oracle_quote_id
            """,
            (sf_opportunity_id,),
        ).fetchall()
        quotes = [_quote_from_row(connection, row) for row in rows]

    return quotes


def create_quote_record(pricing: dict[str, Any]) -> dict[str, Any]:
    initialize_database()
    sf_opportunity_id = str(pricing["sf_opportunity_id"])
    oracle_quote_id = _next_oracle_quote_id(sf_opportunity_id)
    created_at = _timestamp()
    line_items = pricing["line_items"]
    quote = {
        "oracle_quote_id": oracle_quote_id,
        "sf_opportunity_id": sf_opportunity_id,
        "status": "DRAFT",
        "currency": pricing.get("currency", "USD"),
        "subtotal": float(pricing.get("subtotal", pricing["total"])),
        "discount": float(pricing.get("discount", 0.0)),
        "discount_percent": float(pricing.get("discount_percent", 0.0)),
        "total": float(pricing["total"]),
        "selected_product_count": len(line_items),
        "created_at": created_at,
        "line_items": line_items,
    }

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO quotes (
                oracle_quote_id, sf_opportunity_id, status, currency, subtotal,
                discount, discount_percent, total, selected_product_count, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote["oracle_quote_id"],
                quote["sf_opportunity_id"],
                quote["status"],
                quote["currency"],
                quote["subtotal"],
                quote["discount"],
                quote["discount_percent"],
                quote["total"],
                quote["selected_product_count"],
                quote["created_at"],
            ),
        )
        connection.executemany(
            """
            INSERT INTO quote_line_items (
                oracle_quote_id, sku, name, category, quantity, term_months,
                billing_model, annual_unit_price, net_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    oracle_quote_id,
                    item["sku"],
                    item["name"],
                    item.get("category", ""),
                    int(item.get("quantity", 1)),
                    int(item.get("term_months", 12)),
                    item.get("billing_model", ""),
                    float(item.get("annual_unit_price", 0.0)),
                    float(item.get("net_price", 0.0)),
                )
                for item in line_items
            ],
        )
        _insert_activity(
            connection,
            sf_opportunity_id=sf_opportunity_id,
            oracle_quote_id=oracle_quote_id,
            system="Oracle CPQ Cloud",
            event_type="quote_created",
            title="Quote version created",
            detail=f"Oracle CPQ created {oracle_quote_id}.",
            created_at=created_at,
        )

    return quote


def finalize_quote_record(oracle_quote_id: str) -> dict[str, Any] | None:
    initialize_database()
    placed_at = _timestamp()
    with connect() as connection:
        quote_row = connection.execute(
            "SELECT * FROM quotes WHERE oracle_quote_id = ?",
            (oracle_quote_id,),
        ).fetchone()
        if quote_row is None:
            return None

        quote = _quote_from_row(connection, quote_row)
        if quote["status"] == "SUPERSEDED":
            raise ValueError(f"Cannot finalize superseded quote: {oracle_quote_id}")

        existing_order = connection.execute(
            "SELECT * FROM orders WHERE oracle_quote_id = ?",
            (oracle_quote_id,),
        ).fetchone()
        if existing_order is not None:
            return {
                "quote": quote,
                "order": _order_from_row(connection, existing_order),
            }

        connection.execute(
            """
            UPDATE quotes
            SET status = 'SUPERSEDED'
            WHERE sf_opportunity_id = ? AND status = 'DRAFT' AND oracle_quote_id <> ?
            """,
            (quote["sf_opportunity_id"], oracle_quote_id),
        )
        connection.execute(
            """
            UPDATE quotes
            SET status = 'ACCEPTED', accepted_at = ?
            WHERE oracle_quote_id = ?
            """,
            (placed_at, oracle_quote_id),
        )

        oracle_order_id = _oracle_order_id_for_quote(oracle_quote_id)
        order = {
            "oracle_order_id": oracle_order_id,
            "oracle_quote_id": oracle_quote_id,
            "sf_opportunity_id": quote["sf_opportunity_id"],
            "status": "PLACED",
            "currency": quote["currency"],
            "total": quote["total"],
            "placed_at": placed_at,
            "line_items": quote["line_items"],
        }
        connection.execute(
            """
            INSERT INTO orders (
                oracle_order_id, oracle_quote_id, sf_opportunity_id,
                status, currency, total, placed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["oracle_order_id"],
                order["oracle_quote_id"],
                order["sf_opportunity_id"],
                order["status"],
                order["currency"],
                order["total"],
                order["placed_at"],
            ),
        )
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
                    oracle_order_id,
                    item["sku"],
                    item["name"],
                    item.get("category", ""),
                    int(item.get("quantity", 1)),
                    int(item.get("term_months", 12)),
                    item.get("billing_model", ""),
                    float(item.get("annual_unit_price", 0.0)),
                    float(item.get("net_price", 0.0)),
                )
                for item in quote["line_items"]
            ],
        )
        _insert_activity(
            connection,
            sf_opportunity_id=quote["sf_opportunity_id"],
            oracle_quote_id=oracle_quote_id,
            oracle_order_id=oracle_order_id,
            system="Oracle CPQ Cloud",
            event_type="order_placed",
            title="Order placed from accepted quote",
            detail=f"Oracle CPQ placed {oracle_order_id} from {oracle_quote_id}.",
            created_at=placed_at,
        )

        accepted_quote = connection.execute(
            "SELECT * FROM quotes WHERE oracle_quote_id = ?",
            (oracle_quote_id,),
        ).fetchone()

    return {
        "quote": _quote_from_mapping(accepted_quote, quote["line_items"]),
        "order": order,
    }


def list_orders(sf_opportunity_id: str | None = None) -> list[dict[str, Any]]:
    initialize_database()
    params: tuple[Any, ...] = ()
    where = ""
    if sf_opportunity_id:
        where = "WHERE sf_opportunity_id = ?"
        params = (sf_opportunity_id,)

    with connect() as connection:
        rows = connection.execute(
            f"SELECT * FROM orders {where} ORDER BY placed_at DESC",
            params,
        ).fetchall()
        orders = [_order_from_row(connection, row) for row in rows]

    return orders


def get_order(oracle_order_id: str) -> dict[str, Any] | None:
    initialize_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM orders WHERE oracle_order_id = ?",
            (oracle_order_id,),
        ).fetchone()
        if row is None:
            return None

        return _order_from_row(connection, row)


def list_activity(
    sf_opportunity_id: str | None = None,
    sf_account_id: str | None = None,
) -> list[dict[str, Any]]:
    initialize_database()
    filters: list[str] = []
    params: list[Any] = []
    if sf_opportunity_id:
        filters.append("sf_opportunity_id = ?")
        params.append(sf_opportunity_id)
    if sf_account_id:
        filters.append("sf_account_id = ?")
        params.append(sf_account_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM activity_events
            {where}
            ORDER BY created_at DESC, activity_id DESC
            LIMIT 80
            """,
            tuple(params),
        ).fetchall()

    return [_row(row) for row in rows]


def record_agent_run(
    *,
    intent: str,
    status: str,
    steps: list[dict[str, Any]],
    sf_opportunity_id: str | None = None,
) -> dict[str, Any]:
    initialize_database()
    run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"
    created_at = _timestamp()
    sf_account_id = _sf_account_id_for_opportunity(sf_opportunity_id)
    normalized_steps = [
        {
            "step_id": str(step.get("id", f"step_{index + 1}")),
            "label": str(step.get("label", "Step")),
            "layer": str(step.get("layer", "Unknown")),
            "status": str(step.get("status", "completed")),
            "detail": str(step.get("detail", "")),
        }
        for index, step in enumerate(steps)
    ]

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO agent_runs (
                run_id, sf_account_id, sf_opportunity_id, intent, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, sf_account_id, sf_opportunity_id, intent, status, created_at),
        )
        connection.executemany(
            """
            INSERT INTO agent_run_steps (
                run_id, step_id, label, layer, status, detail, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    step["step_id"],
                    step["label"],
                    step["layer"],
                    step["status"],
                    step["detail"],
                    created_at,
                )
                for step in normalized_steps
            ],
        )

    return get_agent_run(run_id) or {
        "run_id": run_id,
        "sf_account_id": sf_account_id,
        "sf_opportunity_id": sf_opportunity_id,
        "intent": intent,
        "status": status,
        "created_at": created_at,
        "steps": normalized_steps,
    }


def list_agent_runs(
    sf_opportunity_id: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    initialize_database()
    params: tuple[Any, ...] = ()
    where = ""
    if sf_opportunity_id:
        where = "WHERE sf_opportunity_id = ?"
        params = (sf_opportunity_id,)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT r.*, COUNT(s.id) AS step_count
            FROM agent_runs r
            LEFT JOIN agent_run_steps s ON s.run_id = r.run_id
            {where}
            GROUP BY r.run_id
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (*params, max(1, min(int(limit), 100))),
        ).fetchall()

    return [_row(row) for row in rows]


def get_agent_run(run_id: str) -> dict[str, Any] | None:
    initialize_database()
    with connect() as connection:
        run_row = connection.execute(
            "SELECT * FROM agent_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if run_row is None:
            return None

        step_rows = connection.execute(
            """
            SELECT step_id AS id, label, layer, status, detail, created_at
            FROM agent_run_steps
            WHERE run_id = ?
            ORDER BY agent_run_steps.id
            """,
            (run_id,),
        ).fetchall()

    run = _row(run_row)
    run["steps"] = [_row(row) for row in step_rows]
    return run


def record_activity(
    *,
    sf_opportunity_id: str | None = None,
    sf_account_id: str | None = None,
    system: str,
    event_type: str,
    title: str,
    detail: str,
    oracle_quote_id: str | None = None,
    oracle_order_id: str | None = None,
) -> dict[str, Any]:
    initialize_database()
    created_at = _timestamp()
    with connect() as connection:
        activity = _insert_activity(
            connection,
            sf_opportunity_id=sf_opportunity_id,
            sf_account_id=sf_account_id,
            oracle_quote_id=oracle_quote_id,
            oracle_order_id=oracle_order_id,
            system=system,
            event_type=event_type,
            title=title,
            detail=detail,
            created_at=created_at,
        )

    return activity


def _opportunity_from_row(row: Any) -> dict[str, Any]:
    sf_opportunity_id = row["sf_opportunity_id"]
    with connect() as connection:
        requirement_rows = connection.execute(
            """
            SELECT requirement
            FROM opportunity_requirements
            WHERE sf_opportunity_id = ?
            ORDER BY id
            """,
            (sf_opportunity_id,),
        ).fetchall()

    return {
        "sf_opportunity_id": sf_opportunity_id,
        "name": row["name"],
        "account": {
            "sf_account_id": row["sf_account_id"],
            "name": row["account_name"],
            "industry": row["account_industry"],
            "region": row["account_region"],
            "segment": row["account_segment"],
        },
        "stage": row["stage"],
        "currency": row["currency"],
        "amount": row["amount"],
        "term_months": row["term_months"],
        "use_case": row["use_case"],
        "sites": row["sites"],
        "region": row["region"],
        "budget": row["budget"],
        "target_close_date": row["target_close_date"],
        "compliance_need": row["compliance_need"],
        "incumbent_vendor": row["incumbent_vendor"],
        "risk_level": row["risk_level"],
        "requirements": [item["requirement"] for item in requirement_rows],
    }


def _quote_from_row(connection: Any, row: Any) -> dict[str, Any]:
    line_items = connection.execute(
        """
        SELECT sku, name, category, quantity, term_months, billing_model,
               annual_unit_price, net_price
        FROM quote_line_items
        WHERE oracle_quote_id = ?
        ORDER BY id
        """,
        (row["oracle_quote_id"],),
    ).fetchall()
    return _quote_from_mapping(row, [_row(item) for item in line_items])


def _quote_from_mapping(row: Any, line_items: list[dict[str, Any]]) -> dict[str, Any]:
    quote = _row(row)
    quote["line_items"] = line_items
    return quote


def _order_from_row(connection: Any, row: Any) -> dict[str, Any]:
    line_items = connection.execute(
        """
        SELECT sku, name, category, quantity, term_months, billing_model,
               annual_unit_price, net_price
        FROM order_line_items
        WHERE oracle_order_id = ?
        ORDER BY id
        """,
        (row["oracle_order_id"],),
    ).fetchall()
    order = _row(row)
    order["line_items"] = [_row(item) for item in line_items]
    return order


def _next_oracle_quote_id(sf_opportunity_id: str) -> str:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT oracle_quote_id
            FROM quotes
            WHERE sf_opportunity_id = ?
            """,
            (sf_opportunity_id,),
        ).fetchall()

    sequence = 1
    for row in rows:
        match = re.search(r"-(\d{3})$", row["oracle_quote_id"])
        if match:
            sequence = max(sequence, int(match.group(1)) + 1)

    return f"ORA-Q-{_record_number(sf_opportunity_id)}-{sequence:03d}"


def _oracle_order_id_for_quote(oracle_quote_id: str) -> str:
    if oracle_quote_id.startswith("ORA-Q-"):
        return oracle_quote_id.replace("ORA-Q-", "ORA-O-", 1)

    legacy_match = re.fullmatch(r"ORA-QUOTE-SF-OPP-(\d+)-(\d+)", oracle_quote_id)
    if legacy_match:
        return f"ORA-O-{legacy_match.group(1)}-{legacy_match.group(2)}"

    if oracle_quote_id.startswith("ORA-QUOTE-"):
        return oracle_quote_id.replace("ORA-QUOTE-", "ORA-O-", 1)

    return f"ORA-O-{_record_number(oracle_quote_id)}"


def _record_number(source_id: str) -> str:
    match = re.search(r"(\d+)$", source_id)
    if match:
        return f"{int(match.group(1)):03d}"

    compacted = re.sub(r"[^A-Za-z0-9]+", "-", source_id).strip("-")
    return compacted[:12] or "000"


def _insert_activity(
    connection: Any,
    *,
    sf_opportunity_id: str | None,
    sf_account_id: str | None = None,
    system: str,
    event_type: str,
    title: str,
    detail: str,
    created_at: str,
    oracle_quote_id: str | None = None,
    oracle_order_id: str | None = None,
) -> dict[str, Any]:
    sf_account_id = sf_account_id or _sf_account_id_for_opportunity(
        sf_opportunity_id,
        connection=connection,
    )

    activity = {
        "activity_id": f"ACT-{uuid.uuid4().hex[:12].upper()}",
        "sf_account_id": sf_account_id,
        "sf_opportunity_id": sf_opportunity_id,
        "oracle_quote_id": oracle_quote_id,
        "oracle_order_id": oracle_order_id,
        "system": system,
        "event_type": event_type,
        "title": title,
        "detail": detail,
        "created_at": created_at,
    }
    connection.execute(
        """
        INSERT INTO activity_events (
            activity_id, sf_account_id, sf_opportunity_id, oracle_quote_id,
            oracle_order_id, system, event_type, title, detail, created_at
        )
        VALUES (
            :activity_id, :sf_account_id, :sf_opportunity_id, :oracle_quote_id,
            :oracle_order_id, :system, :event_type, :title, :detail, :created_at
        )
        """,
        activity,
    )
    return activity


def _row(row: Any) -> dict[str, Any]:
    return dict(row)


def _sf_account_id_for_opportunity(
    sf_opportunity_id: str | None,
    *,
    connection: Any | None = None,
) -> str | None:
    if not sf_opportunity_id:
        return None

    owns_connection = connection is None
    active_connection = connection or connect()
    try:
        row = active_connection.execute(
            """
            SELECT sf_account_id
            FROM opportunities
            WHERE sf_opportunity_id = ?
            """,
            (sf_opportunity_id,),
        ).fetchone()
        return row["sf_account_id"] if row is not None else None
    finally:
        if owns_connection:
            active_connection.close()


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
