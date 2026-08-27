# Advice: building Super-AI-Trader as a third-party app that links to Binance, Gate.io & others

_Date: 2026-08 · Verdict: **Yes, it's possible and proven.** But security and legal
setup decide whether you succeed or get burned._

---

## 1. The model — non-custodial third-party trading app

Your app does **not** hold customer money. The customer keeps funds on their exchange
(Binance, Gate.io, …) and grants your app permission to trade via an **API key**.
This is the standard model of 3Commas, Bitsgap, Cryptohopper, Coinrule, Pionex.

Two ways to connect:

| Method | How it works | Pros | Cons |
|---|---|---|---|
| **API key + secret** (classic) | User creates a key on the exchange and pastes it into your app | Works on every exchange immediately; no approval needed | User must handle keys; *you* must protect them |
| **OAuth / "Fast Connect" / Broker program** | User clicks "Connect Binance" and authorizes your registered app | Best UX, no secret pasting, safer, revenue-share | Must be approved/registered by each exchange |

**Multi-exchange is solved by [CCXT](https://pypi.org/project/ccxt/)**: one library,
100+ exchanges (Binance and Gate.io are "CCXT Certified"), public + private REST and
WebSocket, normalized data. You write the grid/AI logic once and target both venues.
For grid execution you either (a) place spot limit orders yourself via CCXT (simplest,
full control), or (b) call the exchange's native strategy endpoints (needs extra
permissions). Start with (a).

---

## 2. How money is made
- **Subscription** (3Commas / Bitsgap / Coinrule): monthly fee for bots/tools.
- **Exchange rebates / Broker program** (Binance Broker, Gate.io Broker): you earn a
  share of the trading fees your users generate — this is how Pionex and even CCXT
  itself are funded. Often *no cost to the user*.
- **Freemium + pay for advanced strategies/AI.**
Most successful apps combine a free tier with rebates and a paid pro tier.

---

## 3. Security is the whole game (your #1 priority — and the #1 failure point)

The cautionary tale is **3Commas**: in **December 2022 attackers exposed a dataset of
~100,000 customer API credentials** from its systems (after initially blaming
phishing); victims reported **$14.8M–$22M+ stolen** across Binance, Coinbase Pro,
KuCoin. Phishing fake sites compounded it. Key lessons from
[Decrypt](https://decrypt.co/decrypt/117826/3commas-api-dispute-highlights-risks-of-algorithmic-trading)
and [Coin Bureau](https://coinbureau.com/review/3commas-review):

1. **Even a *trade-only* key (withdrawals OFF) can lose money** — an attacker can use
   it to place bad orders (e.g. buy an illiquid token they're dumping). So trade-only
   is necessary but **not sufficient**.
2. Keys leaked from the **vendor's database**. Never store secrets in plaintext.
   After the hack, 3Commas rebuilt with an isolated signing service ("Sign Center").
3. Phishing captured users on fake look-alike sites.

**Required controls for a hosted multi-user app:**
- **Encryption at rest with a KMS/HSM** (AWS KMS / Secrets Manager / HashiCorp Vault).
  Better: **zero-knowledge architecture** — the user's password encrypts the secret
  client-side; your server stores only ciphertext and *cannot decrypt it*; signing
  happens in a hardened, isolated service (or on the user's device).
- Keys **never** sent to the browser, never logged, never shown back (only a redacted
  fingerprint — what our local app already does).
- On the exchange: **trade-only**, **withdrawals disabled**, **IP allowlist** to your
  server IPs, and restrict to needed pairs/notional where the exchange allows.
- Per-user **max-spend caps**, daily limits, rate limiting, and a **global kill switch**.
- Mandatory **2FA** on app accounts; official-domain anti-phishing; sub-accounts.
- Audit logging, monitoring for anomalous orders, and an incident/key-revoke process.
- Tell users that **deleting the app connection isn't enough — revoke the key on the
  exchange too.**

> The good news: our current design keeps keys **on the user's own MacBook** in an
> encrypted local vault and binds the web app to `127.0.0.1`. That "local-first /
> self-hosted" model (like Hummingbot) is the **safest possible** because you never
> hold anyone's keys — and it can be a shipped product by itself before you ever run
> a hosted multi-tenant service.

---

## 4. Legal & regulatory (do not skip this)
- **Non-custodial** greatly reduces licensing (you don't transmit/hold funds), but
  offering automated trading / signals to the **public** can still require licenses.
- **Thailand:** marketing an automated digital-asset trading/advisory service to Thai
  users can fall under Thai **SEC digital-asset business/advisory rules**. Exchange
  connectivity for Thai users should prefer **Thai-licensed venues (Binance TH,
  Bitkub, etc.)** for the regulated, tax-advantaged path (see
  [RESEARCH-deep-dive-2026.md](./RESEARCH-deep-dive-2026.md)). Offshore venues carry
  blocking/consumer-protection risk.
- Exchange **Terms of Service**: commercial automation at scale generally expects you
  to join the exchange's **Broker/Partner program** (also your rebate path) and respect
  rate limits. Binance and Gate geo-block some countries.
- Practical minimum: clear **terms of service**, "not financial advice / educational",
  eligibility/geography screening, risk warnings, privacy policy — and get **legal
  counsel** before taking public money or charging users.

---

## 5. Recommended path (lowest risk → full product)

- **Stage 0 — Local-first app (NOW).** Everything runs on the user's computer; keys in
  the encrypted local vault; practice mode first; CCXT used for live trading. Zero
  custody, zero multi-tenant key risk. Ship this and get real users/paper results.
- **Stage 1 — Cloud features without keys.** Shared strategies, marketplace,
  education, leaderboards, backtests — all non-sensitive.
- **Stage 2 — Optional hosted trading.** Connect via exchange **OAuth/Broker program**
  + **KMS** or a **zero-knowledge** vault so even a breach exposes nothing. Start with
  a small private beta, per-user caps, and the full security checklist above.
- **Stage 3 — Company/licensing.** Register, join broker programs, obtain any needed
  Thai/regional licenses, add monitoring and insurance/disclosures as you scale.

## 6. What we'd add to the code next
1. `ccxt` live/paper connector with a unified `Exchange` interface (`binance`,
   `gateio`, then any CCXT venue).
2. Exchange-connection setup wizard that *forces* trade-only + no-withdrawal and
   explains IP allowlisting.
3. Place the grid as real spot limit orders with order tracking and a kill switch.
4. (Later) broker-program fields and a zero-knowledge vault design for the hosted version.
```
