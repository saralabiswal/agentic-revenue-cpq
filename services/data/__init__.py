"""Package marker and exports for services.data.

Author: Sarala Biswal
"""

from services.data.database import get_database_path, initialize_database
from services.data.repositories import (
    create_quote_record,
    finalize_quote_record,
    get_agent_run,
    get_order,
    get_opportunity,
    list_agent_runs,
    list_accounts,
    list_activity,
    list_opportunities,
    list_orders,
    list_quotes,
    record_agent_run,
    record_activity,
    reset_business_data,
)

# Re-export repository functions as the public data-service API. Integrations and
# backend routes should import from here instead of reaching into database internals.
__all__ = [
    "create_quote_record",
    "finalize_quote_record",
    "get_agent_run",
    "get_database_path",
    "get_order",
    "get_opportunity",
    "initialize_database",
    "list_agent_runs",
    "list_accounts",
    "list_activity",
    "list_opportunities",
    "list_orders",
    "list_quotes",
    "record_agent_run",
    "record_activity",
    "reset_business_data",
]
