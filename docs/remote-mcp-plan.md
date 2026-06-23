# Remote MCP + OAuth — Deployment Plan

Goal: run Mythic Index as a **remote, hosted MCP server** so users connect with one click
(no install, no key paste). This single deliverable unlocks all three targets:
**Claude Connectors Directory**, **ChatGPT Apps**, and **Gemini Enterprise**.

---

## 1. The key realization

Under the current MCP auth spec (2025-06-18), your server is **not** an OAuth Authorization
Server — it's an OAuth 2.1 **Resource Server** that points at an external **Authorization
Server (a managed IdP)**:

- Your server exposes `/.well-known/oauth-protected-resource` (RFC 9728) listing the IdP.
- The IdP exposes `/.well-known/oauth-authorization-server` (RFC 8414) + a DCR endpoint (RFC 7591).
- The client (Claude/ChatGPT) auto-discovers the IdP, **dynamically registers** (DCR), runs
  OAuth 2.1 + PKCE, and sends a bearer token to your server.
- Your server just **validates the bearer token**.

**FastMCP does the Resource-Server plumbing for you** (`RemoteAuthProvider`): it serves the
protected-resource metadata and validates tokens. So "build OAuth" collapses to "configure an IdP."

---

## 2. Architecture (reuses your existing AWS stack)

```
Claude / ChatGPT / Gemini
        │  (Streamable HTTP + OAuth 2.1 bearer token)
        ▼
   ALB (HTTPS, existing)  ──►  mcp.mythic-index.com  (new listener rule + cert SAN)
        │
        ▼
   ECS Fargate: "mcp" service (NEW)         ◄── delegates token validation ──►  IdP (Stytch/WorkOS/Auth0)
   FastMCP, transport=streamable-http              (Authorization Server + DCR)
        │  service API key (Secrets Manager)
        ▼
   Mythic Index API (existing)  ──►  RDS Postgres
        │
        └─ per-user rate limiting keyed by OAuth `sub`  ──►  ElastiCache Redis (existing)
```

Everything below the ALB already exists. The new pieces: one ECS service, one ALB rule, one
DNS record, an IdP account, and a privacy-policy page.

---

## 3. The data-access simplification (important)

All 19 tools are **read-only, public data**. So OAuth here is about **access control,
identity, and meeting directory requirements — not per-user data scoping.** Concretely:

- After a user authenticates, the MCP server calls the Mythic Index API with **one service
  key** (not a per-user key).
- Per-user **rate limiting** is keyed by the OAuth subject (`sub`) in Redis — reusing the
  limiter we just built.

This means we do **not** need to map MCP users to Mythic Index API keys. Big simplification.

It also raises a real fork ↓.

---

## 4. The pivotal decision — do you even need OAuth?

| Option | Effort | UX | Notes |
|---|---|---|---|
| **A. Public, no-auth remote server** | Low | Best (zero login) | Allowed for read-only public data on Claude's directory; simplest. No per-user identity → abuse control relies on global/IP limits. |
| **B. OAuth-gated (delegated IdP)** | Medium | One-time login | Required for the *authenticated* directory path + per-user throttling/analytics. Future-proofs paid tiers. |

Recommendation: **start with A (public) to ship fast and validate demand, design for B.**
Since the data is public and you already have global rate limiting, a public remote server is
a legitimate, fast path to "listed and one-click." Add OAuth (B) when you want per-user limits,
paid tiers, or the authenticated directory placement.

---

## 5. Concrete changes

### 5a. MCP server (code)
- Run FastMCP in **Streamable HTTP**: `mcp.run(transport="streamable-http", host=..., port=8080)`.
- Add a `/health` route for the ALB target group.
- **Option B only:** add `RemoteAuthProvider` pointed at the IdP issuer; gate tools on a valid token;
  key the Redis limiter on `token.sub` instead of the API key.
- Read the **service key** + IdP config from env (Secrets Manager).

### 5b. Image / CI-CD
- Add `RUN_MODE=mcp` to the existing `entrypoint.sh` → launches the MCP server in HTTP mode.
- Reuses the existing ECR image + GitHub Actions build. No new pipeline.

### 5c. CloudFormation (mirror the existing API service)
- `MCPTaskDefinition` + `MCPService` (Fargate), `RUN_MODE=mcp`, env: `MYTHIC_INDEX_API_URL` (internal),
  `MYTHIC_INDEX_API_KEY` (service key, Secrets Manager), `REDIS_URL`, `OAUTH_ISSUER` (Option B).
- `MCPTargetGroup` (health `/health`) + an **ALB listener rule** matching host `mcp.mythic-index.com`.
- Add `mcp.mythic-index.com` as a **SAN on the ACM cert** (or a path rule `/mcp` on the existing host to skip new cert work).
- `MCPDNSRecord` (Route 53 alias to the ALB).
- Reuse `APISecurityGroup` pattern; allow the MCP service to reach the API + Redis.

### 5d. Privacy policy (required for directory submission)
Stub to publish at `https://mythic-index.com/privacy`:
- What data is processed (card queries; for Option B: account identifier from the IdP).
- No selling of data; retention; contact email; third parties (your IdP, AWS).
- Link it from the repo README and the submission form. (A one-page static file on the ALB/S3 site.)

---

## 6. IdP choice (Option B only)

Pick one with **DCR + MCP support** (so Claude/ChatGPT auto-register):

- **Stytch Connected Apps** — purpose-built for MCP, DCR, B2C/B2B, Cloudflare partnership. *Recommended for fastest MCP-specific path.*
- **WorkOS AuthKit** — strong if you want enterprise SSO/SCIM later.
- **Auth0** — natural if you standardize on Okta.

FastMCP's `RemoteAuthProvider` supports all DCR-capable OIDC providers.

---

## 7. Phased rollout

1. **Phase 1 — Remote server, public (Option A).** Streamable HTTP + `/health`, `RUN_MODE=mcp`,
   CloudFormation service + ALB rule + DNS + cert SAN. → Connectable remote URL. *~1–2 days.*
2. **Phase 2 — Submit to Claude.** Privacy policy page + directory submission (annotations already done). *~hours + review time.*
3. **Phase 3 — OAuth (Option B).** Stand up the IdP, add `RemoteAuthProvider`, per-`sub` limiting. *~2–4 days.*
4. **Phase 4 — ChatGPT Apps + Gemini Enterprise.** Apps SDK submission; Gemini Enterprise custom-MCP connect. *~variable, review-gated.*

---

## 8. Per-platform submission (once the remote URL is live)

- **Claude:** Settings/Admin → submit Remote MCP server (Team/Enterprise org) with the URL + privacy policy.
- **ChatGPT:** build per Apps SDK conventions, submit via OpenAI Developer Platform.
- **Gemini:** Gemini Enterprise → connect custom Streamable-HTTP MCP server (per-customer; no public listing).

---

## 8b. Confirmed technical approach (after API verification)

- **No package migration.** The `mcp` SDK's FastMCP (already in use) natively supports
  resource-server auth: `FastMCP(token_verifier=..., auth=AuthSettings(issuer_url=...,
  resource_server_url=..., required_scopes=[...]))`. Published server, `.mcpb`, and remote
  server stay one codebase. Auth activates **only** when `STYTCH_DOMAIN` is set — stdio/Desktop
  stay unauthenticated.
- **IdP = Stytch Connected Apps.** Validate bearer JWTs against Stytch JWKS:
  `jwks_uri = {STYTCH_DOMAIN}/.well-known/jwks.json`, `issuer = STYTCH_DOMAIN`,
  `audience = STYTCH_PROJECT_ID`, alg `RS256`. New dep for this path: `pyjwt[crypto]`.
- Per-user rate limiting keys on the JWT `sub`.

### Stytch setup (your action — the long pole)
1. Create a Stytch project (Consumer/B2C is simplest for a public MCP).
2. Connected Apps → enable → turn on **"Allow dynamic client registration"**.
3. Allowed scopes: `openid email profile`; add a login method (email magic link / Google).
4. Send back: **Stytch domain** (issuer URL) + **Project ID** (JWT audience).

## 9. Open decisions for you
1. **Auth model:** A (public, fast) or B (OAuth) first?
2. **Routing:** `mcp.mythic-index.com` (new cert SAN) vs `api.mythic-index.com/mcp` (no cert change)?
3. **IdP** (if B): Stytch / WorkOS / Auth0?
4. **Privacy policy** hosting: static page on the existing site/S3?
