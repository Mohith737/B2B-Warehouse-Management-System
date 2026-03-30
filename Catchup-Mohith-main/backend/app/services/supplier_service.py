# backend/app/services/supplier_service.py
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PageLimitExceededException,
)
from backend.app.models.supplier import Supplier
from backend.app.repositories.supplier_metrics_history_repository import (
    SupplierMetricsHistoryRepository,
)
from backend.app.repositories.supplier_repository import SupplierRepository
from backend.app.schemas.common import ListResponse, make_pagination_meta
from backend.app.schemas.supplier import (
    SupplierCreate,
    SupplierListParams,
    SupplierMetricsHistoryRead,
    SupplierRead,
    SupplierUpdate,
)


class SupplierService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SupplierRepository(session)
        self.metrics_repo = SupplierMetricsHistoryRepository(session)

    async def get_supplier(self, id: UUID) -> SupplierRead:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        return SupplierRead.model_validate(supplier)

    async def list_suppliers(
        self, params: SupplierListParams
    ) -> ListResponse[SupplierRead]:
        if params.page_size > 50:
            raise PageLimitExceededException(
                details={"max": 50, "requested": params.page_size}
            )
        skip = (params.page - 1) * params.page_size
        items, total = await self.repo.list_with_filters(
            search=params.search,
            tier=params.tier,
            is_active=params.is_active,
            skip=skip,
            limit=params.page_size,
        )
        return ListResponse(
            data=[SupplierRead.model_validate(s) for s in items],
            meta=make_pagination_meta(
                total=total,
                page=params.page,
                page_size=params.page_size,
            ),
        )

    async def create_supplier(self, data: SupplierCreate) -> SupplierRead:
        if await self.repo.email_exists(data.email):
            raise ConflictException(
                details={
                    "field": "email",
                    "value": data.email,
                    "message": "A supplier with this email already exists",
                }
            )
        supplier = Supplier(
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
            payment_terms_days=data.payment_terms_days,
            lead_time_days=data.lead_time_days,
            credit_limit=data.credit_limit,
        )
        try:
            tx = (
                self.session.begin_nested()
                if self.session.in_transaction()
                else self.session.begin()
            )
            async with tx:
                created = await self.repo.create(supplier)
        except IntegrityError as e:
            error_str = str(e.orig).lower()
            if "email" in error_str:
                raise ConflictException(
                    details={
                        "field": "email",
                        "value": data.email,
                        "message": "A supplier with this email already exists",
                    }
                ) from e
            raise ConflictException(
                details={"message": "Supplier creation failed due to a conflict"}
            ) from e
        return SupplierRead.model_validate(created)

    async def update_supplier(self, id: UUID, data: SupplierUpdate) -> SupplierRead:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        update_data = {
            k: v
            for k, v in data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        if "email" in update_data and update_data["email"] != supplier.email:
            if await self.repo.email_exists(update_data["email"]):
                raise ConflictException(
                    details={
                        "field": "email",
                        "value": update_data["email"],
                        "message": "Email already in use",
                    }
                )
        try:
            async with self.session.begin():
                updated = await self.repo.update(supplier, update_data)
        except IntegrityError as e:
            error_str = str(e.orig).lower()
            if "email" in error_str:
                raise ConflictException(details={"field": "email"}) from e
            raise ConflictException(details={"message": "Update conflict"}) from e
        return SupplierRead.model_validate(updated)

    async def delete_supplier(self, id: UUID) -> None:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        async with self.session.begin():
            await self.repo.soft_delete(supplier)

    async def deactivate_supplier(self, id: UUID) -> SupplierRead:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        async with self.session.begin():
            updated = await self.repo.update(supplier, {"is_active": False})
        return SupplierRead.model_validate(updated)

    async def activate_supplier(self, id: UUID) -> SupplierRead:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        async with self.session.begin():
            updated = await self.repo.update(supplier, {"is_active": True})
        return SupplierRead.model_validate(updated)

    async def set_tier_lock(self, id: UUID, tier_locked: bool) -> SupplierRead:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        async with self.session.begin():
            updated = await self.repo.update(supplier, {"tier_locked": tier_locked})
        return SupplierRead.model_validate(updated)

    async def get_metrics(self, id: UUID) -> list[SupplierMetricsHistoryRead]:
        supplier = await self.repo.get_by_id(id)
        if supplier is None:
            raise NotFoundException(message=f"Supplier with id={id} not found")
        metrics = await self.metrics_repo.get_last_n_months(supplier_id=id, n=12)
        return [SupplierMetricsHistoryRead.model_validate(m) for m in metrics]
