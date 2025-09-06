![Package version](https://img.shields.io/pypi/v/monzoh)
![Python versions](https://img.shields.io/pypi/pyversions/monzoh.svg)
![License](https://img.shields.io/pypi/l/monzoh)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![py.typed](https://img.shields.io/badge/py-typed-FFD43B)
[![Coverage Status](https://coveralls.io/repos/github/samdobson/monzoh/badge.svg?branch=main)](https://coveralls.io/github/samdobson/monzoh?branch=main)

![Hero](hero.png)

A Python library for the Monzo Developer API.

📖 [View Full Documentation](https://sjd333-organization.mintlify.app/docs/introduction)


## Features

- 📦 Trusted PyPI publishing
- 🌐 Full Monzo API coverage
- 🔐 Simple OAuth2 authentication flow
- 🔒 Type-safe with Pydantic models
- ⚡ Async/await support with httpx
- ✅ Well-tested and documented
- ⚠️ Comprehensive error handling

## Installation

```bash
uv add monzoh
```

## Quick Start

1. Create an OAuth2 client on the [Monzo Developers Portal](https://developers.monzo.com/). *Redirect URL* must be `http://localhost:8080/callback` and *Confidentiality* must be `Confidential`.
1. Run `monzo-auth` and complete the login flow.
1. Authorise access on the Monzo app.

You can now use the API:

```python
from monzoh import MonzoClient

client = MonzoClient() # No access token needed!

account = client.accounts.list()[0]

balance = account.get_balance()
print(f"Total Balance (incl. pots): £{balance.total_balance / 100:.2f}")

transactions = account.list_transactions(limit=10)
for transaction in transactions:
    if transaction.amount < -5000:  # Transactions over £50
        transaction.annotate({"category": "large_expense"})

transactions[0].upload_attachment("image.jpg")

pots = account.list_pots()
for pot in pots:
    if pot.name == "Savings":
        pot.deposit(1000)  # Deposit £10.00
        break
```

### Asynchronous API

```python
import asyncio
from monzoh import AsyncMonzoClient

async def main():
    async with AsyncMonzoClient() as client:
        account = (await client.accounts.list())[0]
        
        balance = await account.aget_balance()
        print(f"Total Balance (incl. pots): £{balance.total_balance / 100:.2f}")
        
        transactions = await account.alist_transactions(limit=10)
        for transaction in transactions:
            if transaction.amount < -5000:  # Transactions over £50
                await transaction.aannotate({"category": "large_expense"})
        
        pots = await account.alist_pots()
        for pot in pots:
            if pot.name == "Savings":
                await pot.adeposit(1000)  # Deposit £10.00
                break

asyncio.run(main())
```

## Why not call the API directly?

It's much simpler with Monzoh! As an example, here's what uploading an attachment looks like, compared with using the API directly:

### With monzoh

```python
from monzoh import MonzoClient

client = MonzoClient()
account = client.accounts.list()[0]
transaction = account.list_transactions(limit=1)[0]
attachment = transaction.upload_attachment("receipt.jpg")
```

### Without monzoh

```python
import requests
from pathlib import Path

accounts_response = requests.get(
    "https://api.monzo.com/accounts",
    headers={"Authorization": f"Bearer {access_token}"}
)
account_id = accounts_response.json()["accounts"][0]["id"]

transactions_response = requests.get(
    "https://api.monzo.com/transactions",
    headers={"Authorization": f"Bearer {access_token}"},
    params={"account_id": account_id, "limit": 1}
)
transaction_id = transactions_response.json()["transactions"][0]["id"]

response = requests.post(
    "https://api.monzo.com/attachment/upload",
    headers={"Authorization": f"Bearer {access_token}"},
    data={
        "file_name": "receipt.jpg",
        "file_type": "image/jpeg",
        "content_length": str(len(Path("receipt.jpg").read_bytes()))
    }
)
upload_info = response.json()

file_data = Path("receipt.jpg").read_bytes()
requests.put(
    upload_info["upload_url"], 
    data=file_data,
    headers={
        "Content-Type": "image/jpeg",
        "Content-Length": str(len(file_data))
    }
)

requests.post(
    "https://api.monzo.com/attachment/register",
    headers={"Authorization": f"Bearer {access_token}"},
    data={
        "external_id": transaction_id,
        "file_url": upload_info["file_url"],
        "file_type": "image/jpeg"
    }
)
```

