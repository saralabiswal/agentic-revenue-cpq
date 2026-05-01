"""Package marker and exports for integrations.salesforce.

Author: Sarala Biswal
"""

from integrations.salesforce.mock import (
    OpportunityNotFoundError,
    get_opportunity,
    list_accounts,
    list_opportunities,
)

__all__ = [
    "OpportunityNotFoundError",
    "get_opportunity",
    "list_accounts",
    "list_opportunities",
]
