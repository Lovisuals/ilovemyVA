# PRODUCT_SPEC.md — ilovemyVA Platform

> **Single Source of Truth.**
> Any developer, AI agent (Antigravity, Gemini, Claude, Cursor), or executor reads this file
> first and implements exactly what is described here. BOT.md and EDGES_LOG.md are
> superseded by this document. Do not implement from memory. Do not drift from this spec.

---

```yaml
version:    "2.0-saas"
codename:   "APEX"
created:    "2026-04-23"
updated:    "2026-05-09"
replaces:   ["BOT.md v1.3-production", "EDGES_LOG.md v1.3"]
status:     "active — Phase 1 in progress"
```

---

## 1. PRODUCT VISION

ilovemyVA is a **multi-tenant content management SaaS** delivered entirely through Telegram.

Each subscriber receives a private bot instance — their own "Content Manager" — that handles
drafting, scheduling, moderating, and broadcasting content to their Telegram channels and groups.
The UX is a Gmail-inspired single-panel interface (Drafts / Scheduled / Published / Archive).

**What does NOT change from v1.3:**
- The BotFather single-panel interface and all bucket navigation
- Inline FSM editing of every content field
- Pagination (10 items/page)
- APScheduler-backed recurrence (daily / weekly / once)
- Strict owner-gate on all publish and broadcast actions
- Cross-broadcast to connected channels and groups

**What v2.0 adds:**
- Multi-tenant isolation (each subscriber = isolated DB + bot instance)
- Domain-agnostic core (rules and prompts are config-driven, not hardcoded to medical)
- Self-hosted AI stack (no Gemini dependency; HuggingFace + Ollama; $0/month)
- Fork-deploy pipeline (subscriber customises their fork; Railway deploys)
- SaaS control plane (tenant registry, billing hooks, audit dashboard)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                        │
│   TenantRegistry DB · GitHub Fork API · Stripe Billing  │
│   Admin Dashboard · Manual Supervision Interface        │
└────────────────────┬────────────────────────────────────┘
                     │ provisions
          ┌──────────▼──────────┐
          │   PER-TENANT        │  (one per subscriber)
          │   Railway Instance  │
          │                     │
          │  aiogram 3.x bot    │
          │  APScheduler        │
          │  PostgreSQL (own)   │
          │  Redis (own)        │
          │  HuggingFace NER    │
          │  Ollama mistral-7b  │
          └─────────────────────┘
```

### Layer 1 — UI/UX (IMMUTABLE)
The Telegram panel interface is unchanged from v1.3. No UI refactoring is permitted
without an explicit PRODUCT_SPEC update.

### Layer 2 — AI Stack (Self-Hosted, $0)

| Task             | Tool                              | Runtime         |
|------------------|-----------------------------------|-----------------|
| Tone scoring     | `distilbert-finetuned-sst2`       | CPU, local      |
| Spam detection   | HuggingFace zero-shot classifier  | CPU, local      |
| NER              | `dslim/bert-base-NER` via spaCy   | CPU, local      |
| Complex parsing  | Ollama `mistral:latest`           | GPU/CPU, local  |
| Spell/glossary   | `pyspellchecker` + domain dict    | CPU, local      |

**No external AI APIs. No Gemini. No monthly bills.**

AgentService stubs (`agent_service.py`) are replaced by the above in Phase 3.
Until Phase 3 is complete, stubs return safe fallback values (current behaviour preserved).

### Layer 3 — Multi-Tenant Data Isolation

Every DB query in every service MUST filter by `tenant_id` (see Section 5).
No cross-tenant data leakage is permitted under any circumstances.

---

## 3. RUNTIME STACK

```yaml
language:        "Python 3.12+"
framework:       "aiogram 3.7.0"
database:        "PostgreSQL 16 + SQLAlchemy 2.x async"
migrations:      "Alembic"
scheduler:       "APScheduler 4.0.0a4 (AsyncIOScheduler)"
cache:           "Redis 7.x"
ai_local_llm:    "Ollama mistral:latest"
ai_nlp:          "HuggingFace transformers + spaCy"
hosting:         "Webhook-first (Railway); polling fallback for local dev"
media_storage:   "Telegram file_id (primary)"
containerisation: "Docker + docker-compose (dev); single Dockerfile (prod)"
```

### Key Import Paths (do not deviate — see EDGE-018)
```python
from apscheduler import AsyncScheduler                   # public path ✓
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
# NOT: from apscheduler.schedulers.asyncio import AsyncIOScheduler  ✗
```

---

## 4. CONFIGURATION

### 4.1 Environment Variables (all tenants)

```dotenv
# Required — hard crash on missing
BOT_TOKEN=<telegram bot token>
OWNER_ID=<telegram user id, int>
DATABASE_URL=postgresql://...
STORAGE_CHANNEL_ID=<int>
MAIN_CHANNEL_ID=<int>

# Optional
ADMIN_IDS=123,456          # comma-separated
WEBHOOK_URL=https://...    # auto-derived from RAILWAY_PUBLIC_DOMAIN if absent
WEBHOOK_SECRET=            # auto-derived from sha256(BOT_TOKEN)[:32] if absent
PORT=8080
REDIS_URL=redis://...

# Tenant customisation (v2.0)
SERVICE_DOMAIN=medical|legal|jobs|general
QUALITY_CHECK_PROMPT="Score this post for tone and accuracy"
FOOTER_TEMPLATE="⚕️ This is informational only..."
AUTO_MODERATION_THRESHOLD=0.75
SUPPORTED_BUCKETS=drafts,scheduled,published,archive
TZ_DEFAULT=Africa/Lagos
```

### 4.2 Settings Classes (bot/config.py)

`BotSettings`, `DatabaseSettings`, and `Settings` use `pydantic-settings`.
The `webhook_secret` is auto-derived from `BOT_TOKEN` via SHA-256 if not set.
The `webhook_url` is auto-derived from `RAILWAY_PUBLIC_DOMAIN` if not set.
Validation runs at import time; missing required fields crash immediately with a clear error.

---

## 5. MULTI-TENANCY

### 5.1 TenantContext

```python
@dataclass
class TenantContext:
    tenant_id:      int           # Telegram user_id of the subscriber/owner
    service_domain: str           # "medical" | "legal" | "jobs" | "general"
    db_session:     AsyncSession
    config:         dict          # loaded from env at startup
```

Injected into all router handlers via middleware. Never accessed from global state.

### 5.2 Query Pattern — Mandatory

Every service method that reads or writes tenant data MUST include the tenant filter:

```python
# CORRECT
stmt = select(ContentItem).where(
    (ContentItem.bucket == bucket) &
    (ContentItem.tenant_id == ctx.tenant_id)   # ← MANDATORY
)

# WRONG — cross-tenant leak
stmt = select(ContentItem).where(ContentItem.bucket == bucket)
```

The `tenant_id` column is added to `content_items`, `broadcast_logs`,
`moderation_events`, `storage_records`, and `audit_logs` in migration 0003.

### 5.3 Control Plane — TenantRegistry (master DB)

```sql
CREATE TABLE tenant_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_tg_id BIGINT UNIQUE NOT NULL,
    service_name    VARCHAR(64)  NOT NULL,
    railway_app_id  VARCHAR(128),
    railway_env     JSONB,           -- encrypted: Fernet cipher
    status          VARCHAR(16) DEFAULT 'onboarding',
    created_at      TIMESTAMPTZ DEFAULT now(),
    deployed_at     TIMESTAMPTZ
);
```

### 5.4 Per-Tenant Quotas

| Tier  | Posts/month | AI calls/day | Channels |
|-------|-------------|--------------|----------|
| Free  | 100         | 50           | 1        |
| Pro   | 1 000       | 500          | 10       |
| Scale | unlimited   | unlimited    | unlimited|

---

## 6. CORE DOMAINS

### 6.1 Content Buckets (IMMUTABLE UX)

```
DRAFTS → SCHEDULED → PUBLISHED → ARCHIVE
```

- Pagination: 10 items/page, ◀ ▶ navigation
- Each bucket is a read-only view; FSM transitions move items between buckets
- `ContentBucket` enum in `bot/models/content_item.py` is authoritative

### 6.2 ContentItem Schema (actual columns)

See `bot/models/content_item.py`. Key fields:

| Field              | Type          | Notes                            |
|--------------------|---------------|----------------------------------|
| `id`               | UUID          | Primary key                      |
| `bucket`           | ContentBucket | DRAFTS/SCHEDULED/PUBLISHED/ARCHIVE|
| `text`             | Text          | Nullable (media-only posts ok)   |
| `file_ids`         | JSONB[]       | Telegram file_id objects         |
| `scheduled_at`     | TIMESTAMPTZ   | Always timezone-aware (EDGE-021) |
| `recurrence`       | VARCHAR(20)   | "once" | "daily" | "weekly"      |
| `tz_name`          | VARCHAR(64)   | Default: Africa/Lagos            |
| `scheduler_job_id` | VARCHAR(1024) | Comma-sep APScheduler job IDs    |
| `tone_score`       | Float         | 0.0–1.0; null if unchecked       |
| `tone_flags`       | JSONB         | Advisory only; owner decides     |
| `content_hash`     | VARCHAR(64)   | Dedup guard; force-bypass allowed|
| `tenant_id`        | BIGINT        | v2.0 addition; migration 0003    |

### 6.3 Scheduling

- APScheduler `AsyncScheduler` manages all jobs
- `CronTrigger` for daily/weekly; `DateTrigger` for once
- `misfire_grace_time=120s` (EDGE-004)
- Jobs fetch fresh DB state by `item_id` — never carry payload (EDGE-025)
- Time string parsing: if `:` present split on it, else slice `HH` and `MM` (EDGE-023)

### 6.4 Broadcasting

- `BroadcastService` is the ONLY path to `bot.send_message` / `sendMessage`
- Dedup via `content_hash`; `force=True` bypasses with audit log entry
- On `ChatAdminRequired`: log `BC-PERM`, notify owner, continue remaining targets (EDGE-005)

### 6.5 Moderation

- All moderation flags are advisory; owner/admin makes final call
- `ModerationEvent` records every flag with `event_type`, `actor_user_id`, `resolution`
- Group messages: `AuthMiddleware` PENDING block applies only in private chat (EDGE-017)

### 6.6 AI Pipeline (Phase 3 — replacing stubs)

```
Input text
    │
    ├─ ToneService       → distilbert (score 0–1, flags[])
    ├─ SpamService       → zero-shot classifier (is_spam, confidence)
    ├─ NERService        → bert-base-NER (entities[])
    └─ ComplexParser     → Ollama mistral (structured JSON)
         │
         └─ Anti-hallucination gate:
              - No drug dosages, diagnoses, or treatment plans generated
              - All medical content requires owner preview before publish
              - Confidence < 0.80 → "escalate to human"
```

`AgentService` methods return typed Pydantic models (`ToneResult`, `SpamResult`, etc.).
On any exception or timeout: return safe fallback, never block the publish pipeline.

---

## 7. MIDDLEWARE STACK

Registration order matters. `last-registered = outermost wrap` in aiogram:

```python
# main.py — correct registration order (EDGE-008, EDGE-020)
dp.update.middleware(LoggingMiddleware())       # 1st registered = innermost
dp.update.middleware(RateLimitMiddleware())
dp.update.middleware(DbSessionMiddleware())
dp.update.middleware(AuthMiddleware())
dp.update.middleware(SchedulerMiddleware())
dp.update.middleware(ErrorHandlerMiddleware())  # last = outermost try/catch
```

---

## 8. DATABASE & MIGRATIONS

```
migrations/versions/
  0001_initial.py           — all v1.3 tables
  0002_subject_sched.py     — subject, sched_days, sched_time, post_type, target_chat_ids
  0003_tenant_id.py         — tenant_id column on content_items + indexes  [PLANNED]
  0004_tenant_registry.py   — TenantRegistry table on master DB             [PLANNED]
```

Migrations run automatically at startup via `run_migrations()` in `main.py`.

---

## 9. DEPLOYMENT PIPELINE (v2.0 SaaS)

```
1. Subscriber purchases plan (Stripe)
2. Control plane creates TenantRegistry entry
3. GitHub fork created from ilovemyVA main
4. .env.tenant generated with subscriber secrets (Fernet-encrypted at rest)
5. Railway app scaffolded + linked to fork
6. Subscriber customises their fork:
     - FOOTER_TEMPLATE, SERVICE_DOMAIN, QUALITY_CHECK_PROMPT
     - Bucket labels, linked channels/groups
7. git push to fork → Railway deploys automatically
8. Bot instance starts, runs Alembic, connects to isolated PostgreSQL
9. Subscriber receives bot link + onboarding guide via Telegram
```

### Deploy Files (already present)
- `Dockerfile` — single-stage production build
- `railway.json` — Railway service config
- `Procfile` — process declaration
- `docker-compose.yml` — local dev with PostgreSQL + Redis

---

## 10. WEB EDITOR (`static/editor.html`)

The HTML/JS rich editor submits drafts via `POST /api/draft` on the bot's aiohttp server.
It authenticates using `tg.initData` (Telegram WebApp). **It does NOT use `tg.sendData()`**
(EDGE-016). The handler in `bot/routers/drafting.py` validates `initData` before processing.

---

## 11. EDGE CASES (CONSOLIDATED — 25 known)

> All mitigations are implemented unless marked `[PLANNED]`.

| ID       | Title                                     | Mitigation summary                                               |
|----------|-------------------------------------------|------------------------------------------------------------------|
| EDGE-001 | Scheduler fires during FSM edit           | Check `bucket=scheduled AND editing_lock=None` in publish job   |
| EDGE-002 | Media group duplicate rows                | 1s buffer on `media_group_id`; unique DB constraint             |
| EDGE-003 | AI returns malformed JSON                 | `try/except ValidationError` → safe fallback ToneResult         |
| EDGE-004 | Bot downtime causes scheduler misfire     | `misfire_grace_time=120s`; startup job recovery loop            |
| EDGE-005 | Bot loses channel admin mid-broadcast     | Catch `ChatAdminRequired` → log BC-PERM → notify owner          |
| EDGE-006 | Hash collision on legitimate re-post      | "Force Broadcast" button bypasses dedup; logged `force=True`    |
| EDGE-007 | DB pool exhaustion under burst            | `pool_timeout=30s`; Redis page cache TTL=10s                    |
| EDGE-008 | ErrorHandlerMiddleware too inner          | Middleware registered in correct order (see Section 7)          |
| EDGE-009 | Invite code never stored                  | `OnboardGen` callback persists via `UserService.set_verification_code` |
| EDGE-010 | Verification code no expiry               | Reject codes older than 600s; respond `CODE_EXPIRED`            |
| EDGE-011 | Owner not notified of PENDING users       | `cmd_start` sends `NEW_USER_NOTIFICATION` + OnboardGen button   |
| EDGE-012 | `joined_at` never set on USER upgrade     | `on_code_received` sets `joined_at` on successful verification  |
| EDGE-013 | Health check latency                      | Async data gathering with 2s timeout                            |
| EDGE-014 | Moderation enforce permission denied      | `try/except` reports specific Telegram error back to admin      |
| EDGE-015 | Edit tags schema mismatch                 | Tag sanitisation: strip whitespace, filter empty before commit  |
| EDGE-016 | WebApp `sendData` silent fail             | Use `fetch()` to `/api/draft`; authenticate via `tg.initData`   |
| EDGE-017 | AuthMiddleware group spam                 | PENDING hard-block restricted to private chats only             |
| EDGE-018 | APScheduler private import path           | Use `from apscheduler import AsyncScheduler` (public)           |
| EDGE-019 | `api_draft_handler` KeyError dispatcher   | Removed unused `dp` assignment in `drafting.py`                 |
| EDGE-020 | Middleware stack inverted                 | Registration order reversed; ErrorHandlerMiddleware is outermost|
| EDGE-021 | Naive datetime in timezone-aware column   | Apply `timezone.utc` to all `strptime` results before storage   |
| EDGE-022 | Invalid Gemini model name                 | Use `"gemini-2.0-flash"` not `"gemini-flash-3"` if Gemini used |
| EDGE-023 | 30-minute interval mismatch               | Split on `:` if colon present, else slice `HH` and `MM`        |
| EDGE-024 | Time picker vertical sprawl               | Max 8 rows of buttons (BOT.md DO_NOT limit); use sub-menus      |
| EDGE-025 | Scheduled item content desync             | Jobs fetch DB by `item_id` not payload — confirmed safe         |

---

## 12. SAFETY & ANTI-HALLUCINATION PROTOCOL

```yaml
rules:
  - "AI MUST NOT generate drug dosages, diagnoses, or treatment plans"
  - "All medical content MUST pass owner preview before publish"
  - "Tone/spam flags are advisory only — owner decides final action"
  - "draft_suggestion returns diff; owner must explicitly accept"
  - "faq_match confidence < 0.80 → 'escalate to human' response"
  - "No agent may call sendMessage without passing through BroadcastService"
  - "On AI timeout or exception: passthrough original content, never block"
```

These rules apply regardless of `SERVICE_DOMAIN`. Medical is the default domain.
Other domains (legal, jobs, general) may adjust the prompt but not remove the gate.

---

## 13. EXECUTOR ROADMAP

```
Phase 1  (Weeks 1–2)   Multi-tenant foundation
  ├─ Add tenant_id column to all tenant-scoped tables (migration 0003)
  ├─ Add TenantContext dataclass + middleware injection
  ├─ Filter all service queries by tenant_id
  └─ Preserve 100% of existing single-tenant behaviour

Phase 2  (Weeks 3–4)   Fork-deploy pipeline
  ├─ Control plane TenantRegistry API
  ├─ GitHub forking engine
  ├─ Railway orchestration module
  └─ .env.tenant generator (Fernet encryption)

Phase 3  (Weeks 5–6)   Local AI stack
  ├─ Replace AgentService stubs with HuggingFace models
  ├─ Integrate Ollama mistral for complex parsing
  ├─ Add domain dictionary for medical/legal/jobs
  └─ Validate anti-hallucination gate

Phase 4  (Weeks 7–9)   Social aggregators
  ├─ Facebook / Instagram / X feed fetchers (4h interval)
  ├─ Calendar sync (Google Calendar API, free tier)
  └─ Link preview + auto-caption

Phase 5  (Weeks 10–12) Job / scholarship scrapers
  ├─ Indeed + LinkedIn scraper (BeautifulSoup + Selenium)
  ├─ Scholarship aggregator
  └─ 6h fetch interval; dedup via content_hash

Phase 6  (Weeks 13+)   SaaS hardening
  ├─ Stripe billing integration
  ├─ Per-tier quota enforcement
  ├─ Kubernetes / Docker Swarm horizontal scale
  └─ Monitoring dashboard (Grafana + Prometheus)
```

---

## 14. TECH STACK COST SUMMARY

| Component        | Technology                        | Monthly Cost |
|------------------|-----------------------------------|--------------|
| LLM              | Ollama mistral-7b (self-hosted)   | $0           |
| NLP/NER          | HuggingFace transformers + spaCy  | $0           |
| Sentiment        | distilbert-finetuned-sst2         | $0           |
| Scheduler        | APScheduler 4.x                   | $0           |
| Database         | PostgreSQL (Railway free tier)    | $0–$5        |
| Bot API          | Telegram Bot API                  | $0           |
| Social fetching  | Official APIs (free tiers)        | $0           |
| Hosting          | Railway (per instance)            | $5–$20       |
| **Total AI cost**| —                                 | **$0**       |

---

## 15. FILE MAP

```
ilovemyVA/
├── PRODUCT_SPEC.md          ← this file (replaces BOT.md + EDGES_LOG.md)
├── bot/
│   ├── config.py            ← BotSettings, DatabaseSettings, Settings
│   ├── main.py              ← app startup, webhook, middleware registration
│   ├── strings.py           ← all user-facing strings (no hardcoded strings in routers)
│   ├── models/              ← SQLAlchemy ORM models
│   ├── routers/             ← aiogram router handlers (17 modules)
│   ├── services/            ← business logic (12 modules)
│   ├── middlewares/         ← 6 middleware modules; order matters (Section 7)
│   ├── scheduler/           ← APScheduler setup + publish_content_job
│   ├── keyboards/           ← InlineKeyboardMarkup builders
│   ├── states/              ← FSM state groups
│   └── utils/               ← helpers, hashing, sniffer
├── database/
│   ├── base.py              ← DeclarativeBase
│   └── session.py           ← async_sessionmaker factory
├── migrations/              ← Alembic versions
├── static/
│   └── editor.html          ← rich text web editor
├── Dockerfile
├── docker-compose.yml
├── railway.json
├── Procfile
├── pyproject.toml
└── alembic.ini
```

---

## 16. DESIGN PRINCIPLES

1. **UI is sacred.** The BotFather panel is never refactored without explicit approval.
2. **Tenant isolation is absolute