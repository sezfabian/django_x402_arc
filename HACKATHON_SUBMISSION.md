# django_x402_arc - Hackathon Documentation

## Project in one sentence

`django_x402_arc` is a Django paywall module that lets any API endpoint charge USDC per request (including sub-cent pricing) by adding a single `@monetize(...)` decorator.

## What problem this solves

Most APIs and agent workflows are monetized with subscriptions, prepaid credits, or invoice-based billing. That model is poor for:

- tiny, high-frequency requests
- machine-to-machine interactions
- dynamic pay-per-action pricing

This project enables real per-action pricing with on-demand settlement behavior through x402 + Circle Gateway on Arc, so an API call can be economically priced at micro-values (for example `0.000001` USDC).

## Track alignment

Primary track: **Per-API Monetization Engine**

Why:

- The module wraps Django endpoints and enforces payment per HTTP request.
- It returns 402 payment requirements, validates payment signatures, and settles before the view logic runs.
- Different endpoints can have different prices by applying `@monetize("...")` with distinct values.

Secondary fit:

- **Usage-Based Compute Billing** (same pattern can meter per query/per operation by pricing specific endpoints)
- **Real-Time Micro-Commerce Flow** (buyer pays per interaction, seller receives per interaction)

## How I built it

### 1) Core Django module

- Implemented a reusable decorator: `django_arc_monitize_api.decorators.monetize`.
- Supports async Django views for x402 payment enforcement.
- On missing/invalid payment signature, returns proper HTTP 402 payload + headers.
- On successful verification/settlement, injects `request.payer` and runs business logic.

### 2) Gateway integration

- Uses `circle-titanoboa-sdk` (`circlekit`) for payment flow:
  - payment requirement handling
  - signature verification
  - settlement
- Added robust runtime behavior for repeated calls in development:
  - loop-aware gateway lifecycle to avoid async event loop reuse issues.

### 3) Real demo app

Built `django_arc_demo` to prove practical use:

- Demo repository: `https://github.com/sezfabian/django_arc_demo`
- Added one free endpoint and two paid endpoints:
  - `GET /api/free/` (free)
  - `GET /api/cheap/` (paywalled)
  - `GET /api/expensive/` (paywalled)
- Applied endpoint-level pricing with `@monetize("...")`.
- Added `.env`-driven config loading so local setup is reproducible.

### 4) Real-life simulation (not pytest)

- Added `scripts/call_local_endpoints.py` in the demo project:
  - calls free and paid endpoints repeatedly over HTTP
  - performs x402 negotiation + payment for paid routes via `GatewayClient`
  - prints per-call result and appends a Markdown run log
  - supports high-frequency runs (default includes 50 calls to `/api/cheap/`)
- Added `scripts/gen_buyer_wallet.py` in the demo project to create a test buyer keypair quickly.

## Application architecture (request flow)

1. Client calls paywalled endpoint with no payment header.
2. Server responds `402` with payment requirements.
3. Buyer client signs payment intent (`PAYMENT-SIGNATURE`).
4. Client retries request with signature.
5. Decorator verifies + settles payment through Gateway.
6. Server executes endpoint and returns paid response.

This turns API access itself into the economic unit.

## Why this satisfies the hackathon requirements

### Requirement 1: Real per-action pricing (<= $0.01)

- Pricing is per request and configurable per endpoint.
- Demo endpoint uses `0.000001` USDC per call (well below $0.01).

### Requirement 2: Transaction frequency data (50+ in demo)

- Simulation demonstrates 50 paid calls to `/api/cheap/` in one run.
- The runner logs each call with payment status and API response details.
- This produces a measurable frequency trace for evaluation.

### Requirement 3: Margin explanation (why traditional gas fails)

Traditional direct onchain payment per API call is not viable at micro-price levels because:

- network gas and approval/transfer overhead can exceed the value of the API unit
- confirmation latency creates poor UX for high-frequency interactions
- fixed per-transaction overhead destroys margins for sub-cent pricing

In contrast, this model keeps endpoint pricing at micro-values while using Gateway-mediated settlement semantics suited to high-frequency per-call payments.

## Demo checklist

- [ ] Django server running with Arc/Circle environment variables
- [ ] Seller address configured (`ARC_PAY_SELLER_ADDRESS`)
- [ ] Buyer wallet funded and deposited into Gateway
- [ ] Run local endpoint simulation:
  - `python scripts/call_local_endpoints.py --base-url http://127.0.0.1:8000 --log-file run1.md`
- [ ] Capture output logs (status + transaction identifiers)
- [ ] Explain margin model and track alignment in submission notes

## What judges should look at

- Module: `django_arc_monitize_api/decorators.py`
- Gateway bootstrapping: `django_arc_monitize_api/logic.py`
- Demo endpoints: `django_arc_demo/pay_apis/views.py`
- Endpoint runner: `django_arc_demo/scripts/call_local_endpoints.py`
- Buyer wallet helper: `django_arc_demo/scripts/gen_buyer_wallet.py`
- Demo repository: `https://github.com/sezfabian/django_arc_demo`

## Feedback from building

- Developer experience is strongest when payment setup is automated (`.env` loading, wallet helper scripts).
- Error transparency is critical; detailed failure output made it much easier to diagnose:
  - insufficient Gateway balance
  - loop/runtime issues
  - environment mismatch across services
- A reusable decorator abstraction makes monetization easy for existing Django APIs with minimal code changes.

## Defects and work to be done

- **Dynamic payment values per endpoint:** today prices are set in code via `@monetize("...")`. A better production design is a configuration table (for example DB-backed endpoint pricing) so payment amounts can be updated without redeploying or editing code.
- **Async endpoint support for x402:** paid endpoints are currently documented and supported on async Django views. Future work may revisit robust sync compatibility.
