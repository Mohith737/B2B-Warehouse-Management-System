# backend/app/core/exceptions.py
class StockBridgeException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class CreditLimitExceededException(StockBridgeException):
    def __init__(
        self,
        message: str = "Order total exceeds supplier credit limit",
        details: dict | None = None,
    ):
        super().__init__("CREDIT_LIMIT_EXCEEDED", message, details)


class InvalidStateTransitionException(StockBridgeException):
    def __init__(
        self,
        message: str = "This state transition is not permitted",
        details: dict | None = None,
    ):
        super().__init__("INVALID_STATE_TRANSITION", message, details)


class ConflictException(StockBridgeException):
    def __init__(
        self,
        message: str = "Resource was modified by another request",
        details: dict | None = None,
    ):
        super().__init__("CONFLICT", message, details)


class InsufficientStockException(StockBridgeException):
    def __init__(
        self,
        message: str = "Insufficient stock to complete this operation",
        details: dict | None = None,
    ):
        super().__init__("INSUFFICIENT_STOCK", message, details)


class OverReceiptException(StockBridgeException):
    def __init__(
        self,
        message: str = "Received quantity exceeds ordered quantity",
        details: dict | None = None,
    ):
        super().__init__("OVER_RECEIPT", message, details)


class InsufficientDataException(StockBridgeException):
    def __init__(
        self,
        message: str = "Insufficient data to complete this operation",
        details: dict | None = None,
    ):
        super().__init__("INSUFFICIENT_DATA", message, details)


class SupplierInactiveException(StockBridgeException):
    def __init__(
        self,
        message: str = "Supplier is inactive",
        details: dict | None = None,
    ):
        super().__init__("SUPPLIER_INACTIVE", message, details)


class PermissionDeniedException(StockBridgeException):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        details: dict | None = None,
    ):
        super().__init__("PERMISSION_DENIED", message, details)


class BarcodeNotFoundException(StockBridgeException):
    def __init__(
        self,
        message: str = "No product found for this barcode",
        details: dict | None = None,
    ):
        super().__init__("BARCODE_NOT_FOUND", message, details)


class BarcodeMismatchException(StockBridgeException):
    def __init__(
        self,
        message: str = "Barcode does not match product on PO line",
        details: dict | None = None,
    ):
        super().__init__(
            code="BARCODE_MISMATCH",
            message=message,
            details=details or {},
        )


class ProductNotOnPOException(StockBridgeException):
    def __init__(
        self,
        message: str = "This product is not on the purchase order",
        details: dict | None = None,
    ):
        super().__init__("PRODUCT_NOT_ON_PO", message, details)


class NegativeStockNotAllowedException(StockBridgeException):
    def __init__(
        self,
        message: str = "Stock level cannot go below zero",
        details: dict | None = None,
    ):
        super().__init__("NEGATIVE_STOCK_NOT_ALLOWED", message, details)


class AdjustmentNotesRequiredException(StockBridgeException):
    def __init__(
        self,
        message: str = "Notes are required for manual stock adjustments",
        details: dict | None = None,
    ):
        super().__init__("ADJUSTMENT_NOTES_REQUIRED", message, details)


class DuplicateLineInRequestException(StockBridgeException):
    def __init__(
        self,
        message: str = "Duplicate product line in request",
        details: dict | None = None,
    ):
        super().__init__("DUPLICATE_LINE_IN_REQUEST", message, details)


class LineAlreadyFulfilledException(StockBridgeException):
    def __init__(
        self,
        message: str = "This purchase order line is already fulfilled",
        details: dict | None = None,
    ):
        super().__init__("LINE_ALREADY_FULFILLED", message, details)


class PageLimitExceededException(StockBridgeException):
    def __init__(
        self,
        message: str = "Requested page size exceeds the maximum allowed",
        details: dict | None = None,
    ):
        super().__init__("PAGE_LIMIT_EXCEEDED", message, details)


class InvalidCursorException(StockBridgeException):
    def __init__(
        self,
        message: str = "Invalid pagination cursor",
        details: dict | None = None,
    ):
        super().__init__(
            code="INVALID_CURSOR",
            message=message,
            details=details or {},
        )


class InvalidParameterException(StockBridgeException):
    def __init__(
        self,
        message: str = "Invalid parameter value",
        details: dict | None = None,
    ):
        super().__init__("INVALID_PARAMETER", message, details)


class DateRangeTooLargeException(StockBridgeException):
    def __init__(
        self,
        message: str = "Date range exceeds the maximum allowed period",
        details: dict | None = None,
    ):
        super().__init__("DATE_RANGE_TOO_LARGE", message, details)


class ReportGenerationFailedException(StockBridgeException):
    def __init__(
        self,
        message: str = "Failed to generate the requested report",
        details: dict | None = None,
    ):
        super().__init__("REPORT_GENERATION_FAILED", message, details)


class ServiceUnavailableException(StockBridgeException):
    def __init__(
        self,
        message: str = "Service is temporarily unavailable",
        details: dict | None = None,
    ):
        super().__init__("SERVICE_UNAVAILABLE", message, details)


class NotFoundException(StockBridgeException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict | None = None,
    ):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            details=details or {},
        )


class InvalidCredentialsException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "INVALID_CREDENTIALS",
            "Invalid email or password",
            details,
        )


class AccountInactiveException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "ACCOUNT_INACTIVE",
            "This account is inactive",
            details,
        )


class AuthRateLimitedException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "AUTH_RATE_LIMITED",
            "Too many login attempts. Try again later.",
            details,
        )


class TokenRevokedException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "TOKEN_REVOKED",
            "This token has been revoked",
            details,
        )


class TokenExpiredException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "TOKEN_EXPIRED",
            "This token has expired",
            details,
        )


class SessionInvalidatedException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "SESSION_INVALIDATED",
            "Your session has been invalidated. Please log in again.",
            details,
        )


class AuthenticationRequiredException(StockBridgeException):
    def __init__(self, details: dict | None = None):
        super().__init__(
            "AUTHENTICATION_REQUIRED",
            "Authentication is required to access this resource",
            details,
        )
