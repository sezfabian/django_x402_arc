# django-arc-pay

**PyPI package name:** `django-arc-pay`  
**Python import package:** `django_arc_monitize_api`

Drop-in [Django](https://www.djangoproject.com/) integration for **x402-style USDC payments** on **Circle Arc** (and other networks supported by [circle-titanoboa-sdk](https://github.com/vyperlang/circle-titanoboa-sdk)) using a single **`@monetize(...)`** decorator on any view.

## What it does

- Wraps a Django view so clients must pay a **fixed USDC price** before the handler runs.
- Uses Circle’s **Gateway / batching** flow (via `circlekit`) to **verify and settle** the `PAYMENT-SIGNATURE` header against your seller address and chain.
- Returns **HTTP 402** with the correct **payment-required** payload and headers when no valid payment is present.
- On success, attaches **`request.payer`** (payer address from the settled payment) and runs your view.
- Supports **async** views (`async def`, `await` gateway) and **sync** views (gateway bridged with `async_to_sync`).

You do **not** need to add this project to `INSTALLED_APPS` unless you extend it with Django app features (models, migrations, etc.). Configure Django settings and import the decorator.

---

## Getting Started

### 1) Install into your Django project

`django-arc-pay` depends on **`circle-titanoboa-sdk`** (import name **`circlekit`**), pulled directly from GitHub:

- https://github.com/vyperlang/circle-titanoboa-sdk

When you install `django-arc-pay`, pip will also install `circle-titanoboa-sdk` from that repository (via a direct URL dependency in `setup.py`).

Choose one install method:

#### Option A: Clone + local path (recommended for development)

```bash
# 1) Clone
git clone https://github.com/sezfabian/django_x402_arc.git
cd django_x402_arc

# 2) Optional: create and activate venv
python -m venv .venv
source .venv/bin/activate

# 3) Install into your Django project from local path
pip install -e /absolute/path/to/django_x402_arc
```

#### Option B: Install directly from GitHub (no manual clone)

```bash
pip install "django-arc-pay @ git+https://github.com/sezfabian/django_x402_arc.git"
```

If your pip is old and does not handle direct URL dependencies well, upgrade pip first:

```bash
python -m pip install --upgrade pip
```

**Transitive dependencies** (installed with the Circle SDK) include **titanoboa** / **`boa`**, **httpx**, **eth-account**, and related tooling used for on-chain and HTTP calls.

Requirements: **Django ≥ 4.0**, **Python** matching your Django version (see Django release notes).

### 2) Configure Django settings

The first time a paywalled view runs, the library validates settings and builds a **singleton** gateway. You must supply the following **Django settings** (e.g. in `settings.py` or via environment variables your settings module reads).

### Required

| Setting | Purpose |
|--------|---------|
| **`ARC_PAY_SELLER_ADDRESS`** | EVM address that receives USDC for paid requests (your seller / merchant wallet). |
| **`CIRCLE_API_KEY`** | [Circle Platform API key](https://developers.circle.com/) used by the SDK to talk to Circle services (e.g. Gateway verification/settlement). |
| **`CIRCLE_ENTITY_SECRET`** | [Entity secret](https://developers.circle.com/w3s/docs) used with Circle’s APIs where the SDK expects it (store securely; never commit plaintext to git). |

### Optional (defaults shown)

| Setting | Default | Purpose |
|--------|---------|---------|
| **`ARC_PAY_NETWORK`** | `"arcTestnet"` | Chain/network name as understood by `circlekit` (e.g. `arcTestnet`, `baseSepolia`). |
| **`ARC_RPC_URL`** | `https://arc-testnet.drpc.org` | RPC URL passed to **titanoboa** (`boa.set_network_env`) for Arc reads. |
| **`ARC_CHAIN_ID`** | `5042002` | Documented default for Arc testnet; available on `arc_settings` if you need it elsewhere. |

If any **required** setting is missing, Django raises **`django.core.exceptions.ImproperlyConfigured`** when the gateway is first used.

### How to obtain Circle API key and entity secret

1. **Circle Developer account** — Sign in at [Circle Console](https://console.circle.com/) (or the current Circle developer portal for your product).
2. **API key** — Create a **Platform API** (or app) key with the scopes your integration needs. Put the value in **`CIRCLE_API_KEY`** (environment variable `CIRCLE_API_KEY` is a common pattern, then `os.environ` in settings).
3. **Entity secret** — Follow Circle’s docs for **entity secret** generation and registration. You usually generate a secret, register its **ciphertext** with Circle, and keep the **plaintext secret** only in a secrets manager or local env. Set **`CIRCLE_ENTITY_SECRET`** to the value your deployment uses (the SDK reads these settings through your Django `settings` object only if you wire them there; many teams mirror env vars into `settings.py`).
4. **Seller address** — Use a wallet you control on the target network (e.g. Arc testnet) as **`ARC_PAY_SELLER_ADDRESS`**. Testnet USDC is available from [Circle’s faucet](https://faucet.circle.com/) for supported testnets.

> **Security:** Use env vars or a secrets manager for keys and entity secret. Restrict API key rotation and logging so secrets never appear in logs or error pages.

### Example `settings.py` fragment

```python
import os

ARC_PAY_SELLER_ADDRESS = os.environ["ARC_PAY_SELLER_ADDRESS"]
CIRCLE_API_KEY = os.environ["CIRCLE_API_KEY"]
CIRCLE_ENTITY_SECRET = os.environ["CIRCLE_ENTITY_SECRET"]

ARC_PAY_NETWORK = os.environ.get("ARC_PAY_NETWORK", "arcTestnet")
ARC_RPC_URL = os.environ.get("ARC_RPC_URL", "https://arc-testnet.drpc.org")
```

---

## How To Use

### 1. Import the decorator

```python
from django_arc_monitize_api.decorators import monetize
```

### 2. Decorate your API views with a paywall

**Price string:** Pass a USDC amount in the same style **`circlekit`** expects (e.g. `"0.01"`, `"$0.01"` — see [circle-titanoboa-sdk](https://github.com/vyperlang/circle-titanoboa-sdk) / `parse_usdc`).

**Header:** Clients must send a valid **`PAYMENT-SIGNATURE`** header when retrying after a 402 (the Circle / x402 client libraries produce this).

### Sync view example

```python
from django.http import JsonResponse
from django_arc_monitize_api.decorators import monetize

@monetize("0.005")
def expensive_report(request):
    return JsonResponse(
        {"report": "...", "paid_by": request.payer},
        json_dumps_params={"indent": 2},
    )
```

### Async view example (recommended under ASGI)

```python
from django.http import JsonResponse
from django_arc_monitize_api.decorators import monetize

@monetize("$0.01")
async def premium_embedding(request):
    # Gateway payment was verified and settled before this runs.
    return JsonResponse({"vector": [0.1, 0.2], "payer": request.payer})
```

### 3. Wire URLs in your Django app

```python
from django.urls import path
from . import views

urlpatterns = [
    path("api/report/", views.expensive_report),
    path("api/embed/", views.premium_embedding),
]
```

### 4. Call from a payment-aware client

1. Client calls your URL **without** `PAYMENT-SIGNATURE` → response **402** with body + headers describing payment requirements (x402 / Gateway batching).
2. Client uses a **wallet + Circle Gateway–compatible** client (e.g. `circlekit.GatewayClient` in Python, or another x402-aware client) to build the header.
3. Client retries with **`PAYMENT-SIGNATURE`** → decorator verifies/settles payment → your view runs and **`request.payer`** is set.

### Buyer wallet setup (testnet) and Gateway deposit

If your paid call fails with:

- `Payment failed with status 402`
- response reason like `"insufficient_balance"`

it usually means the buyer has USDC in their wallet, but **not deposited into Circle Gateway** yet.

#### 1) Create a buyer wallet (EOA)

Use any EVM keypair. In this monorepo, a helper script exists:

```bash
cd test_django_api_project
./venv/bin/python scripts/gen_buyer_wallet.py
```

Copy the printed `BUYER_PRIVATE_KEY=0x...` into your `.env`.

> Use a buyer address different from `ARC_PAY_SELLER_ADDRESS`.

#### 2) Fund the buyer wallet on Arc testnet

Request test USDC from [Circle faucet](https://faucet.circle.com/) for **Arc Testnet** to the buyer address.

#### 3) Deposit buyer USDC into Circle Gateway

Wallet balance alone is not enough for gasless `GatewayClient.pay(...)`. Deposit first:

```bash
cd circle-titanoboa-sdk
source ../test_django_api_project/venv/bin/activate
PRIVATE_KEY="<BUYER_PRIVATE_KEY>" python examples/deposit.py --amount 0.01
```

#### 4) Verify balances

```bash
cd circle-titanoboa-sdk
PRIVATE_KEY="<BUYER_PRIVATE_KEY>" python examples/check_balances.py
```

On **Arc Testnet**, check:

- `Wallet USDC` > 0
- `Gateway Available` > 0   <-- required for paid API calls

#### 5) Run your paid API simulation

```bash
cd test_django_api_project
./venv/bin/python scripts/micro_pay_sim.py
```

If still 402 after signature, verify these match across server and buyer flow:

- `ARC_PAY_NETWORK` (`arcTestnet` expected for this setup)
- `CIRCLE_API_KEY` and `CIRCLE_ENTITY_SECRET`
- `ARC_PAY_SELLER_ADDRESS`

---

## Use cases

| Use case | Why this fits |
|----------|----------------|
| **Paid HTTP APIs** | Same Django views and URL patterns; payment is enforced before business logic. |
| **Metered “credits” in USDC** | Fixed price per endpoint or wrap different views with different `@monetize("…")` amounts. |
| **Arc / testnet demos** | Defaults target Arc testnet; swap `ARC_PAY_NETWORK` / `ARC_RPC_URL` for other supported chains. |
| **Premium JSON / ML / data endpoints** | Return JSON from sync or async views after payment without building custom 402 plumbing. |

---

## Development and tests

```bash
cd django_x402_arc
pip install -e ".[test]" -e ../circle-titanoboa-sdk   # adjust path to SDK
pytest
```

---

## Related documentation

- **Circle + titanoboa SDK:** middleware and `process_request` behavior — see the **circle-titanoboa-sdk** README (`create_gateway_middleware`, `GatewayClient`, networks).
- **x402:** [x402 HTTP payment required](https://github.com/coinbase/x402) (protocol context; header names and flows align with that ecosystem).

---

## License

See the repository’s `LICENSE` if present; otherwise inherit the license of the parent project you vendor this module from.
