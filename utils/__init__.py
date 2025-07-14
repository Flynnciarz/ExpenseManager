"""
Utilities package for the Secure Expense Management System.

This package contains utility modules for password hashing, input validation,
and other security-related functions.
"""

from .password_hasher import hash_password, verify_password
from .validators import (
    ValidationError,
    validate_username,
    validate_password,
    validate_expense_name,
    validate_amount,
    validate_category,
    validate_schedule,
    sanitize_input
)

__all__ = [
    'hash_password',
    'verify_password',
    'ValidationError',
    'validate_username',
    'validate_password',
    'validate_expense_name',
    'validate_amount',
    'validate_category',
    'validate_schedule',
    'sanitize_input'
]

__version__ = '1.0.0'
__author__ = 'Expense Management System'
