# /home/mohith/Catchup-Mohith/backend/app/schemas/common.py
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(frozen=True)


class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta


class SingleResponse(BaseModel, Generic[T]):
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}

    model_config = ConfigDict(frozen=True)


class ErrorResponse(BaseModel):
    error: ErrorDetail


def make_pagination_meta(total: int, page: int, page_size: int) -> PaginationMeta:
    import math

    return PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
    )
