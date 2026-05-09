"""
bot/tenant.py — TenantContext

Injected into every router handler via TenantMiddleware (bot/middlewares/tenant.py).
Every service method that reads or writes tenant-scoped data MUST receive this context
and filter by tenant_id.  No cross-tenant data leakage is permitted.

Usage in a router handler:
    async def my_handler(message: Message, tenant: TenantContext, session: AsyncSession):
        items = await ContentService.get_page(session, bucket, page, 10, tenant_id=tenant.tenant_id)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TenantContext:
    """
    Immutable per-request tenant context.

    tenant_id       — Telegram user_id of the subscriber / bot owner.
                      In v1.3 single-tenant mode this equals OWNER_ID.
    service_domain  — "medical" | "legal" | "jobs" | "general"
                      Drives prompt templates and moderation vocabulary.
    tz_default      — IANA timezone string for scheduling UI defaults.
    footer_template — Appended to every published post (can be empty string).
    quota_posts_mo  — Monthly post limit for this tenant tier.
    quota_ai_day    — Daily AI-call limit for this tenant tier.
    """

    tenant_id: int
    service_domain: str = "medical"
    tz_default: str = "Africa/Lagos"
    footer_template: str = ""
    quota_posts_mo: int = 1_000
    quota_ai_day: int = 500

    # ------------------------------------------------------------------ #
    # Factory                                                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_env(cls, owner_id: Optional[int] = None) -> "TenantContext":
        """
        Build a TenantContext from environment variables.
        Used at startup for single-tenant deployments (current Railway instances).
        Multi-tenant control plane will call the constructor directly with DB values.
        """
        tid = owner_id or int(os.environ.get("OWNER_ID", "0"))
        return cls(
            tenant_id=tid,
            service_domain=os.environ.get("SERVICE_DOMAIN", "medical"),
            tz_default=os.environ.get("TZ_DEFAULT", "Africa/Lagos"),
            footer_template=os.environ.get("FOOTER_TEMPLATE", ""),
            quota_posts_mo=int(os.environ.get("QUOTA_POSTS_MO", "1000")),
            quota_ai_day=int(os.environ.get("QUOTA_AI_DAY", "500")),
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @property
    def is_medical(self) -> bool:
        return self.service_domain == "medical"

    @property
    def quality_check_prompt(self) -> str:
        prompts = {
            "medical": "Score this medical post for tone, accuracy, and professionalism (0–1).",
            "legal":   "Score this legal post for precision, neutrality, and clarity (0–1).",
            "jobs":    "Score this job post for relevance, completeness, and tone (0–1).",
            "general": "Score this post for tone and quality (0–1).",
        }
        return prompts.get(self.service_domain, prompts["general"])
