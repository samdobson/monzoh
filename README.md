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
- ⚠️  Comprehensive error handling

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

pots = account.list_pots()
for pot in pots:
    if pot.name == "Savings":
        pot.deposit(1000)  # Deposit £10.00
        break

```
