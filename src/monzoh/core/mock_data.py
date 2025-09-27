"""Mock data for testing purposes when using 'test' access token."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from monzoh.types import JSONObject

MOCK_WHOAMI: JSONObject = {
    "authenticated": True,
    "client_id": "test_client_id",
    "user_id": "test_user_id",
}

MOCK_ACCOUNTS: JSONObject = {
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

MOCK_BALANCE: JSONObject = {
    "balance": 285043,
    "total_balance": 295043,
    "currency": "GBP",
    "spend_today": 1250,
}

MOCK_TRANSACTIONS: JSONObject = {
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

MOCK_POTS: JSONObject = {
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

MOCK_WEBHOOKS: JSONObject = {
    "webhooks": [
        {
            "id": "webhook_test_1",
            "account_id": "acc_test_account_1",
            "url": "https://example.com/webhook",
        }
    ]
}


def get_mock_response(
    endpoint: str, _method: str = "GET", **_kwargs: object
) -> JSONObject:
    """Get mock response data for a given endpoint.

    Args:
        endpoint: API endpoint path
        _method: HTTP method
        **_kwargs: Additional parameters (params, data, json_data, etc.)

    Returns:
        Mock response data
    """
    params = _kwargs.get("params", {})

    endpoint_mappings = {
        "/ping/whoami": MOCK_WHOAMI,
        "/accounts": MOCK_ACCOUNTS,
        "/transactions": MOCK_TRANSACTIONS,
        "/pots": MOCK_POTS,
        "/webhooks": MOCK_WEBHOOKS,
    }

    if endpoint in endpoint_mappings:
        return endpoint_mappings[endpoint]

    if endpoint == "/balance" or (
        endpoint.startswith("/accounts/") and endpoint.endswith("/balance")
    ):
        return MOCK_BALANCE

    if endpoint.startswith("/accounts/") and "transactions" in endpoint:
        return MOCK_TRANSACTIONS

    individual_resource_patterns = [
        (
            "/transactions/",
            "transaction",
            cast("list", MOCK_TRANSACTIONS["transactions"])[0],
        ),
        ("/pots/", "pot", cast("list", MOCK_POTS["pots"])[0]),
        ("/webhooks/", "webhook", cast("list", MOCK_WEBHOOKS["webhooks"])[0]),
    ]

    for prefix, key, mock_data in individual_resource_patterns:
        if endpoint.startswith(prefix) and not endpoint.endswith(prefix.rstrip("/")):
            return {key: mock_data}

    return {
        "message": "Mock endpoint not implemented",
        "endpoint": endpoint,
        "params": params if isinstance(params, dict) else {},
    }
