"""Mock data for testing purposes when using 'test' access token."""

from datetime import datetime, timedelta, timezone
from typing import Any

MOCK_WHOAMI = {
    "authenticated": True,
    "client_id": "test_client_id",
    "user_id": "test_user_id",
}

MOCK_ACCOUNTS = {
    "accounts": [
        {
            "id": "acc_test_account_1",
            "description": "Test Current Account",
            "created": (
                datetime.now(tz=timezone.utc) - timedelta(days=365)
            ).isoformat(),
        },
        {
            "id": "acc_test_account_2",
            "description": "Test Joint Account",
            "created": (
                datetime.now(tz=timezone.utc) - timedelta(days=180)
            ).isoformat(),
        },
    ]
}

MOCK_BALANCE = {
    "balance": 285043,
    "total_balance": 295043,
    "currency": "GBP",
    "spend_today": 1250,
}

MOCK_TRANSACTIONS = {
    "transactions": [
        {
            "id": "tx_test_transaction_1",
            "amount": -350,
            "created": (datetime.now(tz=timezone.utc) - timedelta(hours=2)).isoformat(),
            "currency": "GBP",
            "description": "Pret A Manger",
            "account_balance": 285043,
            "category": "eating_out",
            "is_load": False,
            "settled": (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat(),
            "merchant": {
                "id": "merch_test_pret",
                "name": "Pret A Manger",
                "category": "eating_out",
                "created": (
                    datetime.now(tz=timezone.utc) - timedelta(days=1000)
                ).isoformat(),
                "group_id": "grp_test_pret",
                "logo": "https://logos.example.com/pret.png",
                "emoji": "🥪",
            },
            "metadata": {},
            "notes": "Coffee and sandwich",
        },
        {
            "id": "tx_test_transaction_2",
            "amount": -2550,
            "created": (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat(),
            "currency": "GBP",
            "description": "Tesco Store 1234",
            "account_balance": 285393,
            "category": "groceries",
            "is_load": False,
            "settled": (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat(),
            "merchant": {
                "id": "merch_test_tesco",
                "name": "Tesco",
                "category": "groceries",
                "created": (
                    datetime.now(tz=timezone.utc) - timedelta(days=2000)
                ).isoformat(),
                "group_id": "grp_test_tesco",
                "logo": "https://logos.example.com/tesco.png",
                "emoji": "🛒",
            },
            "metadata": {"contactless": True},
            "notes": "Weekly groceries",
        },
        {
            "id": "tx_test_transaction_3",
            "amount": 150000,
            "created": (datetime.now(tz=timezone.utc) - timedelta(days=7)).isoformat(),
            "currency": "GBP",
            "description": "Salary Payment",
            "account_balance": 287943,
            "category": "income",
            "is_load": True,
            "settled": (datetime.now(tz=timezone.utc) - timedelta(days=7)).isoformat(),
            "merchant": None,
            "metadata": {"payroll": True},
            "notes": "Monthly salary",
        },
    ]
}

MOCK_POTS = {
    "pots": [
        {
            "id": "pot_test_holiday",
            "name": "Holiday Fund",
            "style": "beach_ball",
            "balance": 45000,
            "currency": "GBP",
            "created": (
                datetime.now(tz=timezone.utc) - timedelta(days=120)
            ).isoformat(),
            "updated": (datetime.now(tz=timezone.utc) - timedelta(days=5)).isoformat(),
            "deleted": False,
        },
        {
            "id": "pot_test_emergency",
            "name": "Emergency Fund",
            "style": "fire_coral",
            "balance": 100000,
            "currency": "GBP",
            "created": (
                datetime.now(tz=timezone.utc) - timedelta(days=300)
            ).isoformat(),
            "updated": (datetime.now(tz=timezone.utc) - timedelta(days=30)).isoformat(),
            "deleted": False,
        },
    ]
}

MOCK_WEBHOOKS = {
    "webhooks": [
        {
            "id": "webhook_test_1",
            "account_id": "acc_test_account_1",
            "url": "https://example.com/webhook",
        }
    ]
}


def get_mock_response(
    endpoint: str, method: str = "GET", **kwargs: Any
) -> dict[str, Any]:
    """Get mock response data for a given endpoint.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        **kwargs: Additional parameters (params, data, json_data, etc.)

    Returns:
        Mock response data
    """
    params = kwargs.get("params", {})

    if endpoint == "/ping/whoami":
        return MOCK_WHOAMI
    elif endpoint == "/accounts":
        return MOCK_ACCOUNTS
    elif endpoint == "/balance" or (
        endpoint.startswith("/accounts/") and endpoint.endswith("/balance")
    ):
        return MOCK_BALANCE
    elif endpoint == "/transactions" or (
        endpoint.startswith("/accounts/") and "transactions" in endpoint
    ):
        return MOCK_TRANSACTIONS
    elif endpoint == "/pots":
        return MOCK_POTS
    elif endpoint == "/webhooks":
        return MOCK_WEBHOOKS
    elif endpoint.startswith("/transactions/") and not endpoint.endswith(
        "/transactions"
    ):
        return {"transaction": MOCK_TRANSACTIONS["transactions"][0]}
    elif endpoint.startswith("/pots/") and not endpoint.endswith("/pots"):
        return {"pot": MOCK_POTS["pots"][0]}
    elif endpoint.startswith("/webhooks/") and not endpoint.endswith("/webhooks"):
        return {"webhook": MOCK_WEBHOOKS["webhooks"][0]}
    else:
        return {
            "message": "Mock endpoint not implemented",
            "endpoint": endpoint,
            "params": params,
        }
