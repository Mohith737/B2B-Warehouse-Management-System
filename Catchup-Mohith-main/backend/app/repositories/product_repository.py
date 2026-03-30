# /home/mohith/Catchup-Mohith/backend/app/repositories/product_repository.py
from uuid import UUID

from backend.app.models.product import Product
from backend.app.repositories.base_repository import BaseRepository
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.sku == sku)
            .where(Product.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.barcode == barcode)
            .where(Product.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, id: UUID) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == id)
            .where(Product.deleted_at.is_(None))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        search: str | None = None,
        badge: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        base_query = select(Product).where(Product.deleted_at.is_(None))

        if search:
            base_query = base_query.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                )
            )

        if badge == "out_of_stock":
            base_query = base_query.where(Product.current_stock == 0)
        elif badge == "low_stock":
            base_query = base_query.where(
                and_(
                    Product.current_stock > 0,
                    Product.current_stock
                    <= func.coalesce(
                        func.nullif(
                            Product.low_stock_threshold_override,
                            0,
                        ),
                        Product.reorder_point,
                    ),
                )
            )
        elif badge == "in_stock":
            base_query = base_query.where(
                Product.current_stock
                > func.coalesce(
                    func.nullif(
                        Product.low_stock_threshold_override,
                        0,
                    ),
                    Product.reorder_point,
                )
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        data_query = base_query.order_by(Product.name.asc()).offset(skip).limit(limit)
        result = await self.session.execute(data_query)
        items = list(result.scalars().all())
        return items, total

    async def sku_exists(self, sku: str) -> bool:
        result = await self.session.execute(
            select(func.count(Product.id))
            .where(Product.sku == sku)
            .where(Product.deleted_at.is_(None))
        )
        return result.scalar_one() > 0

    async def barcode_exists(self, barcode: str) -> bool:
        result = await self.session.execute(
            select(func.count(Product.id))
            .where(Product.barcode == barcode)
            .where(Product.deleted_at.is_(None))
        )
        return result.scalar_one() > 0
