# /home/mohith/Catchup-Mohith/backend/app/services/po_number_service.py
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.purchase_order import PurchaseOrder


class PONumberService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_next_po_number(self) -> str:
        year = datetime.now(timezone.utc).year
        prefix = f"SB-{year}-"

        result = await self.session.execute(
            select(PurchaseOrder.po_number)
            .where(PurchaseOrder.po_number.like(f"SB-{year}-%"))
            .order_by(PurchaseOrder.po_number.desc())
            .limit(1)
            .with_for_update(skip_locked=False)
        )
        max_po_number = result.scalar_one_or_none()

        if not max_po_number:
            sequence = 1
        else:
            try:
                sequence = int(max_po_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1

        return f"{prefix}{sequence:06d}"


async def generate_auto_po_number(session: AsyncSession, year: int) -> str:
    prefix = f"SB-AUTO-{year}-"

    for attempt in range(2):
        try:
            result = await session.execute(
                select(PurchaseOrder.po_number)
                .where(PurchaseOrder.po_number.like(f"{prefix}%"))
                .where(PurchaseOrder.auto_generated.is_(True))
                .order_by(PurchaseOrder.po_number.desc())
                .limit(1)
                .with_for_update(skip_locked=False)
            )
            max_po_number = result.scalar_one_or_none()

            if not max_po_number:
                sequence = 1
            else:
                try:
                    sequence = int(max_po_number.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    sequence = 1

            return f"{prefix}{sequence:06d}"
        except IntegrityError:
            if attempt == 0:
                continue
            raise

    raise RuntimeError("Failed to generate auto PO number")
