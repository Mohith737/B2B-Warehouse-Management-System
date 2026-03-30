# /home/mohith/Catchup-Mohith/backend/app/services/product_service.py
from decimal import Decimal
from uuid import UUID

from backend.app.core.exceptions import (
    BarcodeNotFoundException,
    ConflictException,
    NotFoundException,
    PageLimitExceededException,
)
from backend.app.models.product import Product
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.common import (
    ListResponse,
    make_pagination_meta,
)
from backend.app.schemas.product import (
    ProductCreate,
    ProductListParams,
    ProductRead,
    ProductUpdate,
    StockBadge,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


def compute_stock_badge(
    current_stock: Decimal,
    reorder_point: Decimal,
    low_stock_threshold_override: Decimal | None,
) -> StockBadge:
    threshold = (
        low_stock_threshold_override
        if low_stock_threshold_override is not None and low_stock_threshold_override > 0
        else reorder_point
    )
    if current_stock <= 0:
        return "out_of_stock"
    if current_stock <= threshold:
        return "low_stock"
    return "in_stock"


def _to_read(product: Product) -> ProductRead:
    badge = compute_stock_badge(
        product.current_stock,
        product.reorder_point,
        product.low_stock_threshold_override,
    )
    return ProductRead(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        unit_of_measure=product.unit_of_measure,
        current_stock=product.current_stock,
        reorder_point=product.reorder_point,
        reorder_quantity=product.reorder_quantity,
        unit_price=product.unit_price,
        barcode=product.barcode,
        low_stock_threshold_override=product.low_stock_threshold_override,
        version=product.version,
        stock_badge=badge,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProductRepository(session)

    async def get_product(self, id: UUID) -> ProductRead:
        product = await self.repo.get_by_id(id)
        if product is None:
            raise NotFoundException(message=f"Product with id={id} not found")
        return _to_read(product)

    async def list_products(
        self, params: ProductListParams
    ) -> ListResponse[ProductRead]:
        if params.page_size > 100:
            raise PageLimitExceededException(
                details={"max": 100, "requested": params.page_size}
            )
        skip = (params.page - 1) * params.page_size
        items, total = await self.repo.list_with_filters(
            search=params.search,
            badge=params.badge,
            skip=skip,
            limit=params.page_size,
        )
        return ListResponse(
            data=[_to_read(p) for p in items],
            meta=make_pagination_meta(
                total=total,
                page=params.page,
                page_size=params.page_size,
            ),
        )

    async def create_product(self, data: ProductCreate) -> ProductRead:
        if await self.repo.sku_exists(data.sku):
            raise ConflictException(
                details={
                    "field": "sku",
                    "value": data.sku,
                    "message": "A product with this SKU already exists",
                }
            )
        if data.barcode and await self.repo.barcode_exists(data.barcode):
            raise ConflictException(
                details={
                    "field": "barcode",
                    "value": data.barcode,
                    "message": "A product with this barcode already exists",
                }
            )

        product = Product(
            sku=data.sku,
            name=data.name,
            description=data.description,
            unit_of_measure=data.unit_of_measure,
            reorder_point=data.reorder_point,
            reorder_quantity=data.reorder_quantity,
            unit_price=data.unit_price,
            barcode=data.barcode,
            low_stock_threshold_override=data.low_stock_threshold_override,
            current_stock=Decimal("0"),
            version=1,
        )

        try:
            tx = (
                self.session.begin_nested()
                if self.session.in_transaction()
                else self.session.begin()
            )
            async with tx:
                created = await self.repo.create(product)
        except IntegrityError as e:
            error_str = str(e.orig).lower()
            if "sku" in error_str:
                raise ConflictException(
                    details={
                        "field": "sku",
                        "value": product.sku,
                        "message": "A product with this SKU already exists",
                    }
                ) from e
            if "barcode" in error_str:
                raise ConflictException(
                    details={
                        "field": "barcode",
                        "value": product.barcode,
                        "message": "A product with this barcode already exists",
                    }
                ) from e
            raise ConflictException(
                details={"message": "Product creation failed due to a conflict"}
            ) from e
        return _to_read(created)

    async def update_product(self, id: UUID, data: ProductUpdate) -> ProductRead:
        try:
            async with self.session.begin():
                # Step 1: SELECT FOR UPDATE
                product = await self.repo.get_by_id_for_update(id)
                if product is None:
                    raise NotFoundException(
                        message=f"Product with id={id} " f"not found"
                    )

                # Step 2: Optimistic lock check
                if product.version != data.version:
                    raise ConflictException(
                        details={
                            "current_version": product.version,
                            "submitted_version": data.version,
                            "message": "Product was modified "
                            "by another request. "
                            "Fetch the latest "
                            "version and retry.",
                        }
                    )

                # Step 3: Build update from model_fields_set
                update_data: dict = {}
                for field in data.model_fields_set:
                    if field == "version":
                        continue
                    update_data[field] = getattr(data, field)

                # Step 4: Barcode uniqueness check
                if (
                    "barcode" in update_data
                    and update_data["barcode"] is not None
                    and update_data["barcode"] != product.barcode
                ):
                    if await self.repo.barcode_exists(update_data["barcode"]):
                        raise ConflictException(
                            details={
                                "field": "barcode",
                                "value": update_data["barcode"],
                                "message": "Barcode already " "in use",
                            }
                        )

                # Step 5: Increment version
                update_data["version"] = product.version + 1

                # Step 6: Flush updates
                updated = await self.repo.update(product, update_data)
        except IntegrityError as e:
            error_str = str(e.orig).lower()
            if "barcode" in error_str:
                raise ConflictException(
                    details={
                        "field": "barcode",
                        "message": "Barcode already in use due to a concurrent write",
                    }
                ) from e
            raise ConflictException(
                details={"message": "Product update failed due to a conflict"}
            ) from e

        return _to_read(updated)

    async def delete_product(self, id: UUID) -> None:
        product = await self.repo.get_by_id(id)
        if product is None:
            raise NotFoundException(message=f"Product with id={id} not found")
        tx = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        async with tx:
            await self.repo.soft_delete(product)

    async def barcode_lookup(self, barcode: str) -> ProductRead:
        product = await self.repo.get_by_barcode(barcode)
        if product is None:
            raise BarcodeNotFoundException(details={"barcode": barcode})
        return _to_read(product)
