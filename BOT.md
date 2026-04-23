# BOT.md — MedLocumContentBot v1.3-production

> **Single Source of Truth** — Any senior developer, Antigravity agent, Gemini Flash 3 agent, Cursor,
> or Claude instance reads this file first and implements exactly what is described here.
> This document IS the architecture. No guessing, no hallucination, no drift.

---

```yaml
################################################################################
# MANIFEST
################################################################################
version: "1.3-production"
name: MedLocumContentBot
codename: "APEX"
description: >
  Advanced Gmail-inspired Content Manager Bot for a Medical Locum Telegram
  Channel & Group (36 000+ members). Features bucket navigation (Drafts /
  Scheduled / Published / Archive), per-page pagination, inline FSM editing,
  live APScheduler-backed scheduling, cross-broadcast to linked targets,
  strict owner-gated moderation, and dual-agent AI assistance powered by
  Antigravity and Gemini Flash 3.

type: content_manager_bot
platform: "Telegram Bot API 9.x (2026)"
created: "2026-04-23"
updated: "2026-04-23"

# ─── Agent Stack ──────────────────────────────────────────────────────────────
agents:
  primary:
    name: Antigravity
    role: >
      Orchestration agent. Owns FSM transitions, bucket CRUD, pagination
      rendering, and APScheduler job lifecycle. Calls Gemini Flash 3 for
      any inference task (tone, draft assist, FAQ match). Exposes typed
      tool interfaces so Gemini can call back into bot state safely.
    capabilities:
      - async_task_dispatch
      - fsm_orchestration
      - structured_tool_registry
      - retry_and_fallback
      - audit_log_emit

  assistant:
    name: Gemini Flash 3
    role: >
      Inference agent. Handles tone scoring, glossary correction, draft
      suggestion, FAQ semantic search, disclaimer insertion, and spam
      classification. Responds only with deterministic JSON schemas —
      never raw prose into message pipelines.
    capabilities:
      - tone_scoring            # Returns { score: float, flags: str[] }
      - draft_suggestion        # Returns { improved_text: str, diff: str }
      - faq_match               # Returns { matched: bool, answer: str | null }
      - spam_classify           # Returns { is_spam: bool, confidence: float }
      - glossary_correct        # Returns { corrected_text: str, changes: dict }
    constraints:
      - always_return_json: true
      - max_latency_ms: 3000
      - fallback_on_timeout: "passthrough"   # Use original text on timeout
      - never_hallucinate_medical_facts: true
      - cite_source_if_factual: true

  anti_hallucination_protocol:
    enabled: true
    rules:
      - "Gemini Flash 3 MUST NOT generate drug dosages, diagnoses, or treatment plans"
      - "All medical content MUST pass through owner preview before publish"
      - "Tone service flags are advisory only — owner decides final action"
      - "draft_suggestion returns diff; owner must explicitly accept"
      - "faq_match confidence < 0.80 triggers 'escalate to human' response"
      - "No agent may call Telegram sendMessage without passing through BroadcastService"

################################################################################
# RUNTIME STACK
################################################################################
recommended_stack:
  language: "Python 3.12+"
  framework: "aiogram 3.x"            # async, routers, FSM, magic filters
  database: "PostgreSQL 16 + SQLAlchemy 2.x async"
  migrations: "Alembic"
  scheduler: "APScheduler 4.x AsyncIOScheduler"
  cache: "Redis 7.x"                  # rate limiting, job dedup, session cache
  ai_primary: "Antigravity SDK (async)"
  ai_assistant: "google-generativeai >= 1.10 (gemini-flash-3)"
  logging: "structlog"                # structured, JSON-compatible
  hosting: "Webhook-first (Railway/Fly.io); polling fallback for local dev"
  media_storage: "Telegram file_id (primary); MinIO/S3 (overflow >20 MB)"
  secret_management: "python-dotenv + environment injection"
  containerisation: "Docker + docker-compose (dev); single Dockerfile (prod)"

python_dependencies:
  # Core
  - aiogram==3.x
  - pydantic-settings>=2.3
  - sqlalchemy[asyncio]>=2.0
  - asyncpg>=0.29
  - alembic>=1.13
  - apscheduler>=4.0
  - redis[hiredis]>=5.0
  # Agents
  - antigravity>=1.0           # replace with actual PyPI name when stable
  - google-generativeai>=1.10
  # Utilities
  - structlog>=24.0
  - python-dotenv>=1.0
  - httpx>=0.27              # async HTTP for webhook + external calls

################################################################################
# CONFIGURATION (Pydantic Settings — config.py)
################################################################################
config:
  # Loaded from .env; all fields validated at startup. Missing = hard crash.
  bot:
    token: "${BOT_TOKEN}"             # string, non-empty
    username: "@MedLocumContentBot"
    owner_id: "${OWNER_ID:int}"
    admin_ids: "${ADMIN_IDS:list[int]}"   # comma-separated in .env
    webhook_url: "${WEBHOOK_URL:str|None}"
    webhook_port: 8443

  database:
    dsn: "${DATABASE_URL}"            # asyncpg DSN
    pool_size: 10
    pool_timeout: 30
    echo: false

  redis:
    url: "${REDIS_URL:str|None}"
    prefix: "medlocum:"

  scheduler:
    timezone: "Africa/Lagos"
    default_times: ["08:00","10:00","12:00","16:00","18:00","22:00"]
    recurrence_options: ["one_time","daily","weekly","weekdays"]
    preview_before_post: true
    auto_publish: true              # fires only after owner preview confirmed
    retry_attempts: 3
    retry_delay_seconds: 30
    misfire_grace_seconds: 120

  content_buckets:
    drafts:
      icon: "📝"
      items_per_page: 10
      preview_chars: 60
    scheduled:
      icon: "⏰"
      items_per_page: 10
      preview_chars: 60
    published:
      icon: "✅"
      items_per_page: 8
      preview_chars: 80
    archive:
      icon: "📦"
      items_per_page: 8
      preview_chars: 80
    navigation:
      buttons_per_row: 3
      use_button_styles: true       # Telegram Bot API 9 button.style

  cross_broadcast:
    enabled: true
    # Populate at runtime via /addtarget command
    linked_targets: []
    # Each: {name: str, chat_id: int, type: "channel"|"group"}
    selection_mode: "multi_select"
    require_confirmation: true
    dedup_window_hours: 24         # Block re-broadcast of same content hash

  moderation:
    spam_detection: true
    tone_check_threshold: 0.75     # Below this → flag for owner
    auto_ban: false                # NEVER auto-ban
    owner_approval_for: ["ban","sensitive_delete","bulk_delete"]
    mute_duration_minutes: 15
    warning_limit_before_mute: 2

  tone:
    default_persona: "professional, empathetic, concise, accurate medical terminology"
    glossary_enabled: true
    auto_append_disclaimer: true
    disclaimer_text: >
      ⚕️ This content is for informational purposes only.
      Always consult a qualified, licensed medical professional for clinical decisions.
    disclaimer_exempt_tags: ["#jobs","#locum_alert","#admin"]

  agents:
    antigravity:
      api_key: "${ANTIGRAVITY_API_KEY}"
      timeout_ms: 5000
      max_retries: 2
    gemini_flash:
      api_key: "${GEMINI_API_KEY}"
      model: "gemini-flash-3"
      temperature: 0.1             # Low temp for medical content — determinism
      max_output_tokens: 1024
      timeout_ms: 3000
      fallback_on_error: "passthrough"

  logging:
    level: "INFO"
    format: "json"
    retention_days: 90
    notify_owner_on: ["CRITICAL","schedule_fail","tone_flag","ban_request","agent_error"]

################################################################################
# DATABASE SCHEMA (SQLAlchemy Models — models/)
################################################################################
models:

  ContentItem:
    table: content_items
    columns:
      id:             "UUID, PK, default=uuid4()"
      bucket:         "Enum('drafts','scheduled','published','archive'), non-null, index"
      text:           "TEXT, nullable"
      parse_mode:     "Enum('HTML','MarkdownV2'), default='HTML'"
      file_ids:       "JSONB, default=[]"
      # e.g. [{type:'photo', file_id:'...'}, {type:'document', file_id:'...'}]
      media_group_id: "VARCHAR(64), nullable"
      has_poll:       "BOOLEAN, default=false"
      poll_data:      "JSONB, nullable"
      scheduled_at:   "TIMESTAMPTZ, nullable, index"
      recurrence:     "VARCHAR(20), nullable"
      tz_name:        "VARCHAR(64), default='Africa/Lagos'"
      scheduler_job_id: "VARCHAR(128), nullable"
      tone_score:     "FLOAT, nullable"
      tone_flags:     "JSONB, default=[]"
      disclaimer_appended: "BOOLEAN, default=false"
      content_hash:   "VARCHAR(64), nullable, index"
      created_by:     "BIGINT, non-null"   # Telegram user_id
      created_at:     "TIMESTAMPTZ, default=utcnow(), index"
      updated_at:     "TIMESTAMPTZ, default=utcnow(), onupdate=utcnow()"
      published_at:   "TIMESTAMPTZ, nullable"
      archived_at:    "TIMESTAMPTZ, nullable"
      tags:           "JSONB, default=[]"
      metadata:       "JSONB, default={}"
    indexes:
      - [bucket, scheduled_at]
      - [content_hash]
      - [created_by, created_at]

  BroadcastLog:
    table: broadcast_logs
    columns:
      id:           "UUID, PK, default=uuid4()"
      content_id:   "UUID, FK→content_items.id, index"
      target_chat_id: "BIGINT, non-null"
      target_name:  "VARCHAR(128)"
      message_id:   "BIGINT, nullable"   # returned Telegram message_id
      status:       "Enum('pending','sent','failed','skipped_dedup')"
      error_detail: "TEXT, nullable"
      sent_at:      "TIMESTAMPTZ, nullable"
      created_at:   "TIMESTAMPTZ, default=utcnow()"

  ModerationEvent:
    table: moderation_events
    columns:
      id:           "UUID, PK, default=uuid4()"
      event_type:   "Enum('spam','tone_flag','warn','mute','ban_request','delete')"
      actor_user_id: "BIGINT"           # user who triggered event
      chat_id:      "BIGINT"
      message_id:   "BIGINT, nullable"
      resolved_by:  "BIGINT, nullable"  # owner Telegram user_id
      resolution:   "Enum('approved','ignored','warn_issued'), nullable"
      detail:       "JSONB, default={}"
      created_at:   "TIMESTAMPTZ, default=utcnow()"

  AuditLog:
    table: audit_logs
    columns:
      id:           "BIGSERIAL, PK"
      event_code:   "VARCHAR(64), non-null, index"
      actor_id:     "BIGINT, nullable"
      target_id:    "VARCHAR(128), nullable"   # content_id, user_id, etc.
      detail:       "JSONB, default={}"
      level:        "VARCHAR(16), default='INFO'"
      created_at:   "TIMESTAMPTZ, default=utcnow(), index"

################################################################################
# SEMANTIC INTENT ANCHORS  (LLM Coding Directive §1)
# Every handler and service must state its intent in verb-object-outcome format.
################################################################################
semantic_intents:

  admin_panel:
    verb: "Display"
    object: "bucket selector with active bucket highlighted and paginated item list"
    success: "Owner sees correct bucket with exactly items_per_page rows, pagination controls, and quick-action buttons"
    failure: "Empty bucket shows 'No items yet' inline, pagination absent, no crash"

  draft_create:
    verb: "Accept and persist"
    object: "multi-media or text post from owner into drafts bucket"
    success: "ContentItem row created, FSM cleared, confirmation sent with item ID"
    failure: "DB error → FSM state preserved, owner notified, item NOT created"

  schedule_post:
    verb: "Register"
    object: "APScheduler job tied to ContentItem.id at owner-confirmed datetime"
    success: "Job registered, ContentItem.scheduler_job_id set, bucket moved to 'scheduled', owner sees countdown"
    failure: "Scheduler error → item stays in drafts, owner notified with error code SCH-001"

  publish_post:
    verb: "Send"
    object: "ContentItem to main channel (and broadcast targets if selected)"
    success: "Message sent, BroadcastLog row written with message_id, bucket→published, published_at set"
    failure: "Telegram API error → retry up to config.retry_attempts, then notify owner with error, item stays scheduled"

  tone_check:
    verb: "Score and flag"
    object: "ContentItem.text via Gemini Flash 3 tone service"
    success: "tone_score and tone_flags persisted; if score < threshold, owner notified inline (never blocks auto-publish silently)"
    failure: "Gemini timeout → passthrough (item NOT blocked), audit log entry TONE-TIMEOUT"

  cross_broadcast:
    verb: "Deliver"
    object: "ContentItem to owner-selected subset of linked_targets"
    success: "One BroadcastLog row per target; skipped duplicates logged as 'skipped_dedup'"
    failure: "Per-target failure logged individually; other targets unaffected"

  moderation_escalate:
    verb: "Escalate"
    object: "Spam/ban-request event to owner with approval inline keyboard"
    success: "Owner receives full context (user, message, confidence); acts via button"
    failure: "Owner unreachable (bot blocked) → event persisted in ModerationEvent, next startup retries notification"

################################################################################
# PROJECT STRUCTURE
################################################################################
structure:
  root: "medlocum_content_bot/"
  tree:
    - "bot/"
    - "  __init__.py"
    - "  main.py                   # Dispatcher, routers, startup/shutdown hooks"
    - "  config.py                 # Pydantic Settings — loaded once, injected everywhere"
    - "  middlewares/"
    - "    __init__.py"
    - "    auth.py                 # Owner/admin gate; rejects all non-admin in private chat"
    - "    logging_mw.py           # Structured event log per update"
    - "    rate_limit.py           # Redis sliding-window; 30 req/min per user"
    - "    error_handler.py        # Global exception → owner notification + audit log"
    - "  routers/"
    - "    __init__.py"
    - "    admin.py                # /admin, /start (private), bucket panel entry"
    - "    buckets.py              # Pagination, per-item actions (edit/preview/move/delete)"
    - "    drafting.py             # /newpost FSM, media intake, auto-save"
    - "    editing.py              # Inline edit FSM, tone re-check after change"
    - "    scheduling.py           # Schedule/reschedule flow, countdown display"
    - "    broadcast.py            # Multi-select target picker, confirmation, send"
    - "    moderation.py           # Group spam handler, warning, escalation"
    - "    settings.py             # /addtarget, /removetarget, /settimezone"
    - "  states/"
    - "    __init__.py"
    - "    draft_states.py         # DraftCreation, DraftEditing"
    - "    schedule_states.py      # SchedulePicking"
    - "    broadcast_states.py     # TargetSelection"
    - "    settings_states.py      # AddTarget"
    - "  keyboards/"
    - "    __init__.py"
    - "    bucket_kb.py            # Bucket selector (InlineKeyboardBuilder)"
    - "    pagination_kb.py        # Generic paginator builder"
    - "    item_actions_kb.py      # Per-item quick-action row"
    - "    schedule_kb.py          # Time picker grid + custom time"
    - "    broadcast_kb.py         # Multi-select checkbox targets"
    - "    confirm_kb.py           # Yes/No/Cancel for destructive actions"
    - "    moderation_kb.py        # Approve/Warn/Ignore for escalations"
    - "  services/"
    - "    __init__.py"
    - "    bucket_service.py       # CRUD, move, paginate ContentItem"
    - "    scheduler_service.py    # APScheduler job create/update/delete wrappers"
    - "    broadcast_service.py    # Dedup check, send, log"
    - "    tone_service.py         # Gemini Flash 3 wrapper (async, typed)"
    - "    moderation_service.py   # Spam detect, warn, mute, escalate"
    - "    agent_service.py        # Antigravity orchestration entry points"
    - "    media_service.py        # file_id reuse, media group handling"
    - "  models/"
    - "    __init__.py"
    - "    content_item.py"
    - "    broadcast_log.py"
    - "    moderation_event.py"
    - "    audit_log.py"
    - "  utils/"
    - "    __init__.py"
    - "    pagination.py           # Offset/limit helpers, page metadata"
    - "    preview.py              # Truncate text, media type icon"
    - "    hashing.py              # content_hash = sha256(text + sorted(file_ids))"
    - "    time_utils.py           # tz-aware parse, countdown string"
    - "    sanitize.py             # Strip unsafe HTML, validate callback data"
    - "  scheduler/"
    - "    __init__.py"
    - "    setup.py                # AsyncIOScheduler factory, startup integration"
    - "    jobs.py                 # publish_job(content_id), retry wrapper"
    - "  agents/"
    - "    __init__.py"
    - "    antigravity_client.py   # Typed async wrapper"
    - "    gemini_client.py        # Typed async wrapper; all responses → JSON"
    - "    schemas.py              # Pydantic models for agent I/O"
    - "database/"
    - "  session.py                # AsyncSessionmaker factory"
    - "  base.py                   # DeclarativeBase"
    - "migrations/                 # Alembic env + versions"
    - ".env.example"
    - "pyproject.toml"
    - "Dockerfile"
    - "docker-compose.yml"
    - "BOT.md                      # ← THIS FILE"
    - "EDGES_LOG.md                # Mandatory (see §EDGES)"

################################################################################
# MAIN ENTRY POINT — main.py (pseudocode contract)
################################################################################
main_py_contract:
  description: >
    Sets up Bot, Dispatcher, includes all routers, registers middleware,
    initialises DB pool, starts AsyncIOScheduler, and either starts webhook
    server or polling. On shutdown: gracefully stops scheduler, closes DB pool.

  startup_sequence:
    1: "Load and validate config (crash on missing env vars)"
    2: "Create SQLAlchemy async engine + run Alembic head check"
    3: "Create Redis pool (optional; skip gracefully if REDIS_URL absent)"
    4: "Initialise Antigravity client + Gemini Flash 3 client (health-check both)"
    5: "Build APScheduler; restore persisted jobs for bucket='scheduled'"
    6: "Build Dispatcher; include all routers in order"
    7: "Register middlewares: auth → rate_limit → logging_mw"
    8: "Register global error handler"
    9: "Start webhook (if WEBHOOK_URL set) else start polling"
    10: "Notify owner: '✅ MedLocumContentBot v1.3 online. {n} scheduled jobs restored.'"

  shutdown_sequence:
    1: "Stop APScheduler (wait=True)"
    2: "Close DB engine"
    3: "Close Redis pool"
    4: "Notify owner: '🔴 Bot shutting down.'"

################################################################################
# ADMIN INTERFACE SPECIFICATION
################################################################################
admin_interface:

  entry_points:
    - command: "/admin"
      scope: "private chat; owner + admin_ids only"
      action: "Send bucket panel; delete previous panel if exists (single-panel pattern)"
    - command: "/start"
      scope: "private chat"
      action: "Onboard + show bucket panel"

  bucket_panel:
    description: >
      Single message with inline keyboard. Top row: four bucket buttons.
      Active bucket uses style="primary". Below: paginated list of items
      in active bucket. Bottom row: pagination controls.
    bucket_button_callback: "bucket:select:{bucket_name}"
    item_row_format: "{icon} {short_preview} | {status_tag}"
    item_button_callback: "item:view:{item_id}"
    pagination_callback: "bucket:{bucket_name}:page:{n}"

  item_detail_view:
    triggered_by: "item:view:{item_id}"
    shows:
      - Full text (truncated at 800 chars for display)
      - Media type indicator
      - Scheduled time (if bucket='scheduled')
      - Tone score badge (if scored)
      - Tags
    action_buttons:
      - label: "✏️ Edit"         callback: "item:edit:{item_id}"         style: "primary"
      - label: "👁 Preview"      callback: "item:preview:{item_id}"
      - label: "⏰ Schedule"     callback: "item:schedule:{item_id}"     style: "success"
      - label: "📡 Broadcast"    callback: "item:broadcast:{item_id}"    style: "success"
      - label: "📦 Archive"      callback: "item:archive:{item_id}"
      - label: "🗑 Delete"       callback: "item:delete:{item_id}"       style: "danger"
      - label: "← Back"         callback: "bucket:select:{bucket_name}"

################################################################################
# FSM STATE MACHINES
################################################################################
fsm:

  DraftCreation:
    states:
      - WAITING_CONTENT:    "Accepts text, photo, video, document, media group, poll"
      - CONFIRMING:         "Show preview + tone score; buttons: Save Draft / Re-enter / Cancel"
    transitions:
      WAITING_CONTENT → CONFIRMING: "Any valid message received"
      CONFIRMING → (saved):         "User taps 'Save Draft' → ContentItem created, FSM cleared"
      CONFIRMING → WAITING_CONTENT: "User taps 'Re-enter'"
      ANY → (cancelled):            "User taps 'Cancel' or /cancel → FSM cleared, no DB write"
    auto_save: "Every WAITING_CONTENT message auto-upserts a temp draft row (bucket='drafts', metadata.temp=true)"

  DraftEditing:
    states:
      - SELECTING_FIELD:    "Inline: Edit Text / Replace Media / Add Tags / Cancel"
      - EDITING_TEXT:       "Accepts new text message"
      - EDITING_MEDIA:      "Accepts photo/video/document"
      - EDITING_TAGS:       "Accepts comma-separated tag string"
    transitions:
      EDITING_* → SELECTING_FIELD: "Valid input received → update field → re-run tone check → show updated item"

  SchedulePicking:
    states:
      - PICKING_TIME:       "Grid of default times + 'Custom' button"
      - PICKING_CUSTOM_TIME: "Accepts 'HH:MM DD-MM-YYYY' string"
      - PICKING_RECURRENCE:  "one_time / daily / weekly / weekdays"
      - CONFIRMING_SCHEDULE: "Show full schedule summary; Confirm / Back"
    transitions:
      CONFIRMING_SCHEDULE → (scheduled): "APScheduler job registered, item→scheduled bucket"

  BroadcastTargetSelection:
    states:
      - SELECTING_TARGETS:  "Checkbox-style multi-select; Done / Cancel"
      - CONFIRMING_BROADCAST: "Show selected targets + full preview; Send / Back"
    transitions:
      CONFIRMING_BROADCAST → (sent): "BroadcastService.send() called per target"

################################################################################
# KEYBOARD BUILDERS (keyboard/ contracts)
################################################################################
keyboards:

  bucket_kb:
    function: "build_bucket_panel(active_bucket, items, page, total_pages) → InlineKeyboardMarkup"
    rules:
      - "Bucket row: 4 buttons; active bucket style='primary', others style='secondary'"
      - "Item rows: one button per item, truncated preview, callback item:view:{id}"
      - "Pagination row: '«' (page>1), 'Page {n}/{total}' (disabled), '»' (page<total)"
      - "Max total buttons per message: 30 (Telegram hard limit 8×8 grid, keep headroom)"

  pagination_kb:
    function: "build_paginator(callback_prefix, page, total_pages) → list[InlineKeyboardButton]"
    rules:
      - "Disabled page indicator uses callback_data='noop' (always answer() with no action)"

  confirm_kb:
    function: "build_confirm(yes_cb, no_cb, cancel_cb=None) → InlineKeyboardMarkup"
    rules:
      - "Yes: style='success'; No: style='danger'; Cancel: no style (style=None)"
      - "Destructive actions ALWAYS require this keyboard — no direct execute"

  broadcast_kb:
    function: "build_target_selector(targets, selected_ids) → InlineKeyboardMarkup"
    rules:
      - "Each target: '☑ {name}' if selected else '☐ {name}'; callback: broadcast:toggle:{chat_id}"
      - "Bottom row: '✅ Done (N selected)' | '✗ Cancel'"

################################################################################
# SERVICE CONTRACTS
################################################################################
services:

  BucketService:
    methods:
      get_page:
        signature: "async def get_page(session, bucket, page, per_page) → tuple[list[ContentItem], int]"
        contract: "Returns (items, total_count). Empty bucket → ([], 0). Never raises."
      create_draft:
        signature: "async def create_draft(session, data: DraftCreate) → ContentItem"
        contract: "Inserts row, sets content_hash, triggers tone check (non-blocking task)."
      move_bucket:
        signature: "async def move_bucket(session, item_id, target_bucket) → ContentItem"
        contract: "Updates bucket + timestamp fields. Raises ItemNotFound if missing."
      delete_item:
        signature: "async def delete_item(session, item_id) → None"
        contract: "Hard delete. Caller must cancel scheduler job first via SchedulerService."

  SchedulerService:
    methods:
      register_job:
        signature: "async def register_job(session, scheduler, item_id, run_at, recurrence) → str"
        contract: >
          Adds APScheduler job. Returns job_id. Persists job_id to ContentItem.
          Raises SchedulerError with code SCH-001 on failure (item NOT moved to scheduled).
      cancel_job:
        signature: "async def cancel_job(scheduler, job_id) → None"
        contract: "Silently no-ops if job_id not found (idempotent)."
      publish_job:
        description: "The actual APScheduler trigger function."
        steps:
          1: "Load ContentItem by id (fresh session)"
          2: "Verify still in 'scheduled' bucket (guard against double-fire)"
          3: "Append disclaimer if tone.auto_append_disclaimer and not item.disclaimer_appended"
          4: "Send to main channel via BroadcastService"
          5: "Move item → 'published'; set published_at"
          6: "Log AuditLog event 'publish_success'"
          7: "On any send failure → retry up to config.retry_attempts with retry_delay_seconds backoff"
          8: "After max retries → notify owner with item link + error; keep item in 'scheduled'"

  BroadcastService:
    methods:
      send:
        signature: "async def send(bot, item, target_chat_id, target_name) → BroadcastLog"
        contract: >
          Checks dedup (content_hash + target_chat_id within dedup_window_hours).
          If duplicate → returns log with status='skipped_dedup'.
          Sends via aiogram bot.send_* based on media type.
          Returns BroadcastLog with status='sent' and message_id on success.
          On Telegram error → status='failed', error_detail set, raises BroadcastError for caller to retry.
        # SIDE EFFECT: Calls Telegram API (sendMessage/sendPhoto/etc).
        # Why necessary and unavoidable: core delivery function; no mock possible in prod.

  ToneService:
    methods:
      score:
        signature: "async def score(text: str) → ToneResult"
        contract: >
          Calls Gemini Flash 3 with medical tone prompt.
          Returns ToneResult(score=float, flags=list[str]).
          On timeout/error → returns ToneResult(score=1.0, flags=['service_unavailable']).
          NEVER blocks publishing. Always returns within 3 000 ms (enforced by asyncio.wait_for).
    anti_hallucination:
      - "Gemini prompt explicitly forbids generating drug names, dosages, or diagnoses"
      - "Prompt: 'Score ONLY the tone (0.0=unprofessional, 1.0=professional). Return JSON only.'"
      - "Response schema enforced via Pydantic; any extra fields stripped"

  ModerationService:
    methods:
      handle_message:
        signature: "async def handle_message(bot, message, session) → ModerationAction"
        contract: >
          1. Run spam_classify via Gemini Flash 3.
          2. If is_spam and confidence > 0.85 → delete message, increment warn count,
             mute if warn_count > warning_limit_before_mute.
          3. Escalate to owner via send_escalation (NEVER auto-ban).
          4. Returns ModerationAction with action_taken enum.
      send_escalation:
        signature: "async def send_escalation(bot, event: ModerationEvent) → None"
        contract: >
          Sends owner a message with: user profile link, message snippet,
          spam confidence, warn history, and moderation_kb (Approve/Warn/Ignore).
          Persists ModerationEvent before sending (so it exists even if send fails).

  AgentService:
    description: >
      Antigravity orchestration layer. Wraps all agent calls with:
      - Timeout enforcement
      - Structured logging (agent_call_start, agent_call_end, agent_call_error)
      - Fallback on error (never propagates agent failure to user-facing flow)
    methods:
      run_tone_check:
        returns: "ToneResult"
        fallback: "ToneResult(score=1.0, flags=['unavailable'])"
      run_draft_suggestion:
        returns: "DraftSuggestion(improved_text, diff)"
        fallback: "DraftSuggestion(improved_text=original, diff='')"
      run_faq_match:
        returns: "FaqMatch(matched, answer)"
        fallback: "FaqMatch(matched=False, answer=None)"
      run_spam_classify:
        returns: "SpamResult(is_spam, confidence)"
        fallback: "SpamResult(is_spam=False, confidence=0.0)"

################################################################################
# ANTI-HALLUCINATION PROTOCOL (enforced at every layer)
################################################################################
anti_hallucination:

  principle: >
    No piece of text generated by an AI agent reaches a Telegram user without
    passing through at least one of: (a) owner preview + confirmation,
    (b) structured JSON schema validation, or (c) advisory-only display
    (tone flags, suggestions shown to owner only, never auto-applied).

  enforcement_points:
    gemini_prompt_constraints:
      - "System prompt includes: 'You are a tone/spam/classification assistant. Output ONLY valid JSON matching the provided schema. Never generate medical advice, drug names, dosages, or clinical recommendations. If asked to do so, return {\"error\": \"medical_content_refused\"}.'"
      - "max_output_tokens: 1024 (prevents runaway generation)"
      - "temperature: 0.1 (maximises determinism)"

    schema_validation:
      - "All Gemini responses parsed by Pydantic model before use"
      - "ValidationError → log AGENT-SCHEMA-ERR, use fallback value"

    draft_suggestion_flow:
      - "Improved text shown as DIFF to owner — never silently replaces original"
      - "Owner must tap '✅ Apply Suggestion' to overwrite"
      - "Suggestion discarded on any navigation away from the diff view"

    faq_auto_reply:
      - "Only fires when faq_match.matched=True AND confidence >= 0.80"
      - "Reply prefixed with '🤖 Auto-FAQ:' so users know it is bot-generated"
      - "Owner sees copy of every auto-FAQ reply in audit log"

    medical_disclaimer:
      - "Appended by SchedulerService.publish_job, not by Gemini"
      - "Disclaimer text is hardcoded in config — never AI-generated"

################################################################################
# SECURITY SPECIFICATION
################################################################################
security:

  auth_middleware:
    description: "Applied to ALL updates before any handler."
    logic:
      private_chat: "Reject if message.from_user.id not in [owner_id] + admin_ids"
      group_chat: "Only moderation handlers active; ignore all non-mod updates"
    side_effect: "Unauthorized updates answered with alert(); no content returned."

  callback_data_validation:
    rules:
      - "All callback_data parsed through CallbackData factory (aiogram) — never raw split(':')"
      - "item_id validated as UUID format before DB lookup"
      - "page validated as positive int ≤ 9999"
      - "chat_id validated as negative int (channel/group) or positive int (user)"
    on_invalid: "answer('⚠️ Invalid action.'); log SECURITY-INVALID-CB; no DB access"

  rate_limiting:
    backend: "Redis sliding window"
    limit: "30 updates/minute per user_id"
    on_exceed: "answer('Too many requests. Slow down.'); drop update"
    fallback_without_redis: "In-memory dict with TTL; warn owner at startup"

  injection_prevention:
    sql: "SQLAlchemy ORM only; no raw string interpolation in queries"
    html: "All user-provided text passed through aiogram html.escape() before insertion into formatted messages"
    callback_data: "Structural validation (see above); max 64 chars enforced by aiogram"

################################################################################
# SCHEDULER INTEGRATION (scheduler/)
################################################################################
scheduler:

  setup:
    description: "APScheduler AsyncIOScheduler, timezone from config"
    job_store: "SQLAlchemyJobStore async (same DB) for persistence across restarts"
    executor: "AsyncIOExecutor"
    job_defaults:
      coalesce: true
      max_instances: 1             # Prevent double-fire
      misfire_grace_time: 120      # seconds

  job_recovery_on_startup:
    description: >
      On startup, query ContentItem WHERE bucket='scheduled' AND scheduler_job_id IS NOT NULL.
      For each: verify APScheduler job exists; re-add if missing (handles crash recovery).
    log_event: "SCHEDULER-RESTORE"

  publish_job_pseudocode: |
    async def publish_job(content_id: str, bot_token: str):
        """
        # SIDE EFFECT: Sends message to Telegram channel. Why necessary and unavoidable:
        #   This is the scheduled delivery function; Telegram send is its only purpose.
        """
        async with get_session() as session:
            item = await BucketService.get_by_id(session, content_id)
            assert item is not None, f"[SCH-002] ContentItem {content_id} not found"
            assert item.bucket == "scheduled", f"[SCH-003] Item {content_id} not in scheduled bucket"
            
            if item.tone_score and item.tone_score < config.tone_check_threshold:
                await notify_owner_tone_warning(bot, item)
                # Still publish — tone check is advisory only
            
            if config.tone.auto_append_disclaimer and not item.disclaimer_appended:
                item.text = (item.text or "") + "\n\n" + config.tone.disclaimer_text
                item.disclaimer_appended = True
                await session.commit()
            
            for attempt in range(1, config.retry_attempts + 1):
                try:
                    log = await BroadcastService.send(bot, item, main_channel_id, "Main Channel")
                    await AuditLog.write(session, "publish_success", detail={"attempt": attempt})
                    await BucketService.move_bucket(session, item.id, "published")
                    return
                except BroadcastError as e:
                    log.error("publish_attempt_failed", attempt=attempt, error=str(e), code="PUB-FAIL")
                    if attempt < config.retry_attempts:
                        await asyncio.sleep(config.retry_delay_seconds)
            
            await notify_owner_publish_failure(bot, item, last_error=e)
            # Item remains in 'scheduled' bucket for manual intervention

################################################################################
# LOGGING SPECIFICATION
################################################################################
logging:

  library: structlog
  format: json
  output: stdout (container log collection)

  mandatory_log_fields:
    - event_code     # e.g. "draft_create", "publish_success", "TONE-FLAG"
    - level          # DEBUG / INFO / WARNING / ERROR / CRITICAL
    - function_name  # __name__ of calling function
    - actor_id       # Telegram user_id if applicable
    - target_id      # content_id or user_id if applicable
    - error_code     # short code (e.g. SCH-001) on all error paths
    - timestamp      # ISO-8601, UTC

  event_codes:
    - draft_create
    - draft_edit
    - item_schedule
    - publish_success
    - publish_fail          # code PUB-FAIL
    - broadcast_send
    - broadcast_skip_dedup
    - broadcast_fail
    - tone_check_pass
    - tone_check_flag       # code TONE-FLAG
    - tone_check_timeout    # code TONE-TIMEOUT
    - scheduler_restore
    - scheduler_job_missing # code SCH-002
    - moderation_delete
    - moderation_mute
    - moderation_escalate
    - owner_notified
    - agent_call_start
    - agent_call_end
    - agent_call_error      # code AGENT-ERR
    - security_invalid_cb   # code SECURITY-INVALID-CB
    - rate_limit_exceeded   # code RATE-LIMIT
    - CRITICAL              # triggers owner Telegram notification

  owner_notifications:
    - "All CRITICAL events"
    - "publish_fail after max retries"
    - "tone_check_flag (score < threshold)"
    - "moderation_escalate"
    - "agent_call_error (if persistent)"

################################################################################
# EDGES_LOG.md — Mandatory Edge Cases (LLM Coding Directive §7)
################################################################################
edges_initial_entries:
  description: >
    EDGES_LOG.md must exist at project root and be updated immediately
    whenever a new edge case is discovered. Agents must read it before changes.
    Minimum initial entries below — copy verbatim to EDGES_LOG.md at project setup.

  entries:
    - id: EDGE-001
      description: "APScheduler job fires while item is being edited in FSM"
      risk: "Double-publish or publish of partially edited content"
      mitigation: >
        publish_job checks item.bucket == 'scheduled' AND
        item.metadata.get('editing_lock') is None.
        Editing FSM sets editing_lock=True on entry, clears on exit.

    - id: EDGE-002
      description: "Owner sends media group (album) as new post"
      risk: "Multiple updates arrive for same media group; duplicate ContentItem rows"
      mitigation: >
        Collect updates with same media_group_id in a 1-second buffer
        (asyncio.gather with delay). Create ONE ContentItem with all file_ids.
        Use media_group_id as dedup key in DB (unique constraint).

    - id: EDGE-003
      description: "Gemini Flash 3 returns malformed JSON (not matching schema)"
      risk: "Pydantic ValidationError crashes tone check; item blocked"
      mitigation: >
        ToneService wraps parse in try/except ValidationError.
        On failure: returns ToneResult(score=1.0, flags=['schema_error']).
        Logs AGENT-SCHEMA-ERR. Publishing continues unblocked.

    - id: EDGE-004
      description: "Scheduled post time passes while bot is down (misfire)"
      risk: "Post never sent; item stuck in 'scheduled'"
      mitigation: >
        APScheduler misfire_grace_time=120s handles brief downtime.
        On startup, job recovery loop detects overdue jobs and fires immediately
        if within 1 hour of scheduled time; notifies owner otherwise.

    - id: EDGE-005
      description: "Linked target channel removes bot admin rights mid-broadcast"
      risk: "BroadcastError mid-loop; partial broadcast; owner unaware"
      mitigation: >
        BroadcastService catches ChatAdminRequired / BotKicked errors separately.
        Logs broadcast_fail with code BC-PERM. Notifies owner with target name.
        Continues to other targets. Does NOT retry permission errors.

    - id: EDGE-006
      description: "Content hash collision between two different posts"
      risk: "Legitimate re-post skipped as duplicate"
      mitigation: >
        Dedup uses content_hash + target_chat_id + window (24h).
        If owner explicitly taps 'Force Broadcast', dedup is bypassed
        and a flag force=True is written to BroadcastLog.

    - id: EDGE-007
      description: "PostgreSQL connection pool exhausted under burst load"
      risk: "Timeouts on paginated list requests; users see error"
      mitigation: >
        pool_timeout=30s; SQLAlchemy raises TimeoutError caught in error_handler middleware.
        Owner notified with code DB-POOL. Implement Redis cache for bucket page reads
        (TTL 10s) to reduce DB pressure under burst.

################################################################################
# IMPLEMENTATION DOS AND DON'TS (non-negotiable)
################################################################################
rules:

  DO:
    - "Async/await everywhere — zero sync DB or scheduler calls in handlers"
    - "Answer all callback queries immediately (await query.answer()) before any async work"
    - "Keep handlers thin — delegate all logic to services"
    - "Show owner exact previews before every publish and broadcast"
    - "Validate all callback_data through typed CallbackData classes"
    - "Label every side effect with: # SIDE EFFECT: [desc]. Why necessary and unavoidable: [one sentence]"
    - "Write EDGES_LOG.md entry for every new edge case discovered during implementation"
    - "Use content_hash for broadcast deduplication"
    - "Log every error with level, function_name, context, and unique error code"
    - "Add asyncio.wait_for(timeout=3.0) to every Gemini Flash 3 call"
    - "Test pagination with 150+ items; test scheduler with 50+ concurrent jobs"
    - "Restore scheduler jobs on every startup (crash recovery)"

  DO_NOT:
    - "NEVER auto-ban — always escalate to owner with approval keyboard"
    - "NEVER auto-publish or broadcast without owner confirmation on first use"
    - "NEVER allow Gemini to write text directly to a Telegram send call"
    - "NEVER trust raw callback_data strings — always parse through CallbackData"
    - "NEVER block the event loop (no time.sleep, no sync requests, no sync DB)"
    - "NEVER omit disclaimer on medical content posts"
    - "NEVER store bot token, API keys, or owner_id in code — .env only"
    - "NEVER exceed 3 buttons per row in item action keyboards (mobile readability)"
    - "NEVER stack more than 8 rows of inline buttons (Telegram renders poorly)"
    - "NEVER generate medical dosages, diagnoses, or treatment plans from any agent"
    - "NEVER skip the EDGES_LOG.md update after discovering a new edge case"

################################################################################
# TESTING REQUIREMENTS
################################################################################
testing:

  philosophy: >
    Tests are written BEFORE implementation code (TDD, LLM Coding Directive §5).
    Negative tests must fail on the initial broken/missing implementation.

  required_test_modules:
    - tests/test_bucket_service.py
    - tests/test_scheduler_service.py
    - tests/test_broadcast_service.py
    - tests/test_tone_service.py
    - tests/test_moderation_service.py
    - tests/test_keyboards.py
    - tests/test_pagination.py
    - tests/test_sanitize.py
    - tests/test_hashing.py
    - tests/test_agent_schemas.py

  mandatory_test_cases:
    bucket_service:
      - "get_page returns empty list and 0 for empty bucket (not None, not exception)"
      - "get_page page=99 beyond total returns empty list (no IndexError)"
      - "create_draft sets content_hash correctly"
      - "move_bucket raises ItemNotFound for non-existent id"
      - "delete_item is idempotent (second delete does not raise)"

    scheduler_service:
      - "register_job stores job_id in ContentItem"
      - "cancel_job with non-existent id does not raise"
      - "publish_job skips item not in 'scheduled' bucket (EDGE-001)"
      - "publish_job retries up to config.retry_attempts on BroadcastError"
      - "publish_job notifies owner after max retries exhausted"

    broadcast_service:
      - "send skips duplicate within dedup_window (returns skipped_dedup)"
      - "send with force=True bypasses dedup"
      - "send with ChatAdminRequired logs BC-PERM and does NOT retry"

    tone_service:
      - "score returns ToneResult on valid Gemini response"
      - "score returns fallback ToneResult on Gemini timeout (not exception)"
      - "score returns fallback ToneResult on Pydantic ValidationError (EDGE-003)"

    keyboards:
      - "build_bucket_panel with 0 items renders without pagination row"
      - "build_bucket_panel with 150 items across 15 pages renders page 7 correctly"
      - "build_target_selector with all selected renders all checkmarks"

  negative_test_requirement: >
    Every negative test must assert the EXACT exception type, error code, or
    fallback return value. A negative test that passes before the fix is written
    is invalid and must be rewritten.

################################################################################
# ROADMAP
################################################################################
roadmap:
  "v1.3 (Current)":
    - Bucket navigation + pagination
    - APScheduler scheduling with recovery
    - Cross-broadcast with dedup
    - Tone enforcement via Gemini Flash 3
    - Antigravity orchestration layer
    - Full audit logging
    - Owner safety gates (previews, confirmations, no auto-ban)

  "v1.4":
    - AI-assisted draft suggestions (diff-based, owner-approved)
    - Post analytics (reach, engagement pull from channel stats API)
    - Bulk import via CSV forward

  "v1.5":
    - Telegram Mini App dashboard (React, read-only analytics)
    - Webhook-based real-time delivery status

################################################################################
# IMPLEMENTATION CHECKLIST (agent/developer completes before marking task done)
################################################################################
implementation_checklist:
  - "[x] config.py loads all env vars; crashes with clear message on missing"
  - "[x] All SQLAlchemy models match schema above; Alembic migration generated"
  - "[x] All 5 routers created and registered in main.py"
  - "[x] All FSM states defined; no orphaned states"
  - "[x] All keyboard builders return InlineKeyboardMarkup (not raw list)"
  - "[x] BucketService, SchedulerService, BroadcastService, ToneService, ModerationService, AgentService implemented"
  - "[x] Gemini Flash 3 client uses asyncio.wait_for(timeout=3.0) on every call"
  - "[ ] Antigravity client wraps all tool calls with error fallback"
  - "[x] publish_job implements full retry loop with owner notification"
  - "[ ] Scheduler job recovery runs on startup"
  - "[x] Auth middleware blocks non-admin private chat updates"
  - "[ ] Callback data validation in place for all callbacks"
  - "[x] Rate limiting active (Redis or in-memory fallback)"
  - "[x] All side effects labeled in code"
  - "[x] EDGES_LOG.md created with at minimum EDGE-001 through EDGE-007"
  - "[ ] All mandatory test modules created; negative tests fail before implementation"
  - "[x] Disclaimer appended by SchedulerService — never by Gemini"
  - "[x] No auto-ban path exists anywhere in codebase (grep: 'ban' must show only escalation code)"
  - "[x] Dockerfile and docker-compose.yml functional"
  - "[x] .env.example populated with all required keys (no real values)"

################################################################################
# AUDIT TRACE (LLM Coding Directive §8)
################################################################################
audit_trace:
  Intent:       "confirmed — Content Manager Bot, owner-controlled, zero hallucination pipeline"
  Asserts:      "7 runtime assertions specified (job existence, bucket state, item existence, schema validity, dedup logic, pool bounds, lock state)"
  Tests:        "pre-defined per module; negatives specified to fail before implementation"
  SideEffects:  "labeled at BroadcastService.send, publish_job — both justified as core delivery"
  Idempotency:  "cancel_job idempotent; delete_item idempotent; publish_job guarded by bucket check"
  Resources:    "Gemini timeout 3000ms enforced; DB pool_size/timeout set; Redis state TTL enforced"
  Logging:      "all non-immediate error paths log level+function+context+error_code"
  EDGES:        "7 entries pre-populated in EDGES_LOG.md spec above"
  Checklist:    "all 19 items listed; agent must tick each before declaring implementation complete"
```
