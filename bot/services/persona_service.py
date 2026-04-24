import uuid
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.persona import BotPersona


class PersonaService:
    @staticmethod
    async def get_active(session: AsyncSession) -> Optional[BotPersona]:
        result = await session.execute(
            select(BotPersona).where(BotPersona.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(session: AsyncSession) -> List[BotPersona]:
        result = await session.execute(
            select(BotPersona).order_by(BotPersona.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, persona_id: uuid.UUID) -> Optional[BotPersona]:
        result = await session.execute(
            select(BotPersona).where(BotPersona.id == persona_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        title: Optional[str],
        signature: str,
        created_by: int,
    ) -> BotPersona:
        persona = BotPersona(
            name=name, title=title, signature=signature,
            is_active=False, created_by=created_by,
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)
        return persona

    @staticmethod
    async def activate(session: AsyncSession, persona_id: uuid.UUID) -> None:
        await session.execute(update(BotPersona).values(is_active=False))
        await session.execute(
            update(BotPersona).where(BotPersona.id == persona_id).values(is_active=True)
        )
        await session.commit()

    @staticmethod
    async def delete(session: AsyncSession, persona_id: uuid.UUID) -> None:
        persona = await PersonaService.get_by_id(session, persona_id)
        if persona:
            await session.delete(persona)
            await session.commit()

    @staticmethod
    def render_signature(persona: BotPersona) -> str:
        sig = persona.signature.replace("{name}", persona.name)
        if persona.title:
            sig = sig.replace("{title}", persona.title)
        else:
            sig = sig.replace(" · {title}", "").replace("{title}", "")
        return sig.strip()

    @staticmethod
    def apply_to_text(text: str, persona: Optional[BotPersona]) -> str:
        if not persona:
            return text
        sig = PersonaService.render_signature(persona)
        return f"{text}\n\n─────────────────\n{sig}"
