"""
Custom exceptions for the application.
"""
from fastapi import HTTPException, status


class LMSException(HTTPException):
    # Base exception dùng chung cho toàn hệ thống.
    """Base exception for LMS application."""
    pass


class NotFoundException(LMSException):
    # Tài nguyên không tồn tại.
    """Resource not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedException(LMSException):
    # Chưa xác thực hoặc token không hợp lệ.
    """Authentication required."""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(LMSException):
    # Không đủ quyền truy cập.
    """Access denied."""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(LMSException):
    # Dữ liệu đầu vào không hợp lệ.
    """Bad request."""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictException(LMSException):
    # Xung đột dữ liệu (ví dụ trùng email).
    """Resource conflict (e.g., duplicate)."""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationException(LMSException):
    # Lỗi validate dữ liệu.
    """Validation error."""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
