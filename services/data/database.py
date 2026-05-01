"""SQLite connection, initialization, and reset helpers for business data.

Author: Sarala Biswal
"""

import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "app_data" / "business.sqlite3"


def get_database_path() -> Path:
    """Resolve the SQLite database path from configuration or defaults."""
    configured_path = os.getenv("BUSINESS_DB_PATH")
    if configured_path:
        return Path(configured_path)

    return DEFAULT_DATABASE_PATH


def connect() -> sqlite3.Connection:
    """Open a SQLite connection configured for row-style access."""
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create the database schema and seed records when needed."""
    from services.data.seed import seed_if_empty

    with connect() as connection:
        _create_schema(connection)
        seed_if_empty(connection)


def reset_database() -> None:
    """Delete and rebuild the local SQLite business database."""
    database_path = get_database_path()
    if database_path.exists():
        database_path.unlink()
    initialize_database()


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create all database tables required by the demo workflow."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sf_account_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            industry TEXT NOT NULL,
            region TEXT NOT NULL,
            segment TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sf_opportunity_id TEXT NOT NULL UNIQUE,
            sf_account_id TEXT NOT NULL,
            name TEXT NOT NULL,
            stage TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            term_months INTEGER NOT NULL,
            use_case TEXT NOT NULL,
            sites INTEGER NOT NULL,
            region TEXT NOT NULL,
            budget REAL NOT NULL,
            target_close_date TEXT NOT NULL,
            compliance_need TEXT NOT NULL,
            incumbent_vendor TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            FOREIGN KEY (sf_account_id) REFERENCES accounts(sf_account_id)
        );

        CREATE TABLE IF NOT EXISTS opportunity_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sf_opportunity_id TEXT NOT NULL,
            requirement TEXT NOT NULL,
            FOREIGN KEY (sf_opportunity_id) REFERENCES opportunities(sf_opportunity_id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            annual_unit_price REAL NOT NULL,
            billing_model TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pricing_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL,
            percent REAL NOT NULL,
            condition_text TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_quote_id TEXT NOT NULL UNIQUE,
            sf_opportunity_id TEXT NOT NULL,
            status TEXT NOT NULL,
            currency TEXT NOT NULL,
            subtotal REAL NOT NULL,
            discount REAL NOT NULL,
            discount_percent REAL NOT NULL,
            total REAL NOT NULL,
            selected_product_count INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            accepted_at TEXT,
            FOREIGN KEY (sf_opportunity_id) REFERENCES opportunities(sf_opportunity_id)
        );

        CREATE TABLE IF NOT EXISTS quote_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_quote_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            term_months INTEGER NOT NULL,
            billing_model TEXT NOT NULL,
            annual_unit_price REAL NOT NULL,
            net_price REAL NOT NULL,
            FOREIGN KEY (oracle_quote_id) REFERENCES quotes(oracle_quote_id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_order_id TEXT NOT NULL UNIQUE,
            oracle_quote_id TEXT NOT NULL,
            sf_opportunity_id TEXT NOT NULL,
            status TEXT NOT NULL,
            currency TEXT NOT NULL,
            total REAL NOT NULL,
            placed_at TEXT NOT NULL,
            FOREIGN KEY (oracle_quote_id) REFERENCES quotes(oracle_quote_id),
            FOREIGN KEY (sf_opportunity_id) REFERENCES opportunities(sf_opportunity_id)
        );

        CREATE TABLE IF NOT EXISTS order_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_order_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            term_months INTEGER NOT NULL,
            billing_model TEXT NOT NULL,
            annual_unit_price REAL NOT NULL,
            net_price REAL NOT NULL,
            FOREIGN KEY (oracle_order_id) REFERENCES orders(oracle_order_id)
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL UNIQUE,
            sf_account_id TEXT,
            sf_opportunity_id TEXT,
            intent TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS agent_run_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            label TEXT NOT NULL,
            layer TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES agent_runs(run_id)
        );

        CREATE TABLE IF NOT EXISTS activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id TEXT NOT NULL UNIQUE,
            sf_account_id TEXT,
            sf_opportunity_id TEXT,
            oracle_quote_id TEXT,
            oracle_order_id TEXT,
            system TEXT NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
