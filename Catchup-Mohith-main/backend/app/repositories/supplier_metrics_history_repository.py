# backend/app/repositories/supplier_metrics_history_repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.supplier_metrics_history import SupplierMetricsHistory
from backend.app.repositories.base_repository import BaseRepository


class SupplierMetricsHistoryRepository(BaseRepository[SupplierMetricsHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(SupplierMetricsHistory, session)

    async def get_last_n_months(
        self,
        supplier_id: UUID,
        n: int = 12,
    ) -> list[SupplierMetricsHistory]:
        result = await self.session.execute(
            select(SupplierMetricsHistory)
            .where(SupplierMetricsHistory.supplier_id == supplier_id)
            .order_by(
                SupplierMetricsHistory.period_year.desc(),
                SupplierMetricsHistory.period_month.desc(),
            )
            .limit(n)
        )
        return list(result.scalars().all())

    async def get_by_period(
        self,
        supplier_id: UUID,
        year: int,
        month: int,
    ) -> SupplierMetricsHistory | None:
        result = await self.session.execute(
            select(SupplierMetricsHistory).where(
                SupplierMetricsHistory.supplier_id == supplier_id,
                SupplierMetricsHistory.period_year == year,
                SupplierMetricsHistory.period_month == month,
            )
        )
        return result.scalar_one_or_none()
