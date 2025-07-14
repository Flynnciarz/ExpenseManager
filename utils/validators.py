import re
import logging
from typing import Union, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_username(username: str) -> str:
    """
    Validate username format and length.
    
    Args:
        username (str): Username to validate
        
    Returns:
        str: Cleaned username
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username or not isinstance(username, str):
        raise ValidationError("Username is required")
    
    username = username.strip()
    
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")
    
    if len(username) > 50:
        raise ValidationError("Username must be less than 50 characters")
    
    # Allow alphanumeric characters, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
    
    return username

def validate_password(password: str) -> str:
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        str: Password (unchanged)
        
    Raises:
        ValidationError: If password is invalid
    """
    if not password or not isinstance(password, str):
        raise ValidationError("Password is required")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password must be less than 128 characters")
    
    # Check for at least one uppercase, one lowercase, one digit
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")
    
    return password

def validate_expense_name(name: str) -> str:
    """
    Validate expense name.
    
    Args:
        name (str): Expense name to validate
        
    Returns:
        str: Cleaned expense name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Expense name is required")
    
    name = name.strip()
    
    if len(name) < 1:
        raise ValidationError("Expense name cannot be empty")
    
    if len(name) > 100:
        raise ValidationError("Expense name must be less than 100 characters")
    
    # Remove any potentially dangerous characters
    name = re.sub(r'[<>"\']', '', name)
    
    return name

def validate_amount(amount: Union[str, float, int]) -> float:
    """
    Validate and convert amount to float.
    
    Args:
        amount: Amount to validate
        
    Returns:
        float: Validated amount
        
    Raises:
        ValidationError: If amount is invalid
    """
    try:
        if isinstance(amount, str):
            amount = amount.strip()
            if not amount:
                raise ValidationError("Amount is required")
            amount = float(amount)
        elif not isinstance(amount, (int, float)):
            raise ValidationError("Amount must be a number")
        
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        
        if amount > 999999.99:
            raise ValidationError("Amount cannot exceed 999,999.99")
        
        # Round to 2 decimal places
        return round(float(amount), 2)
    
    except ValueError:
        raise ValidationError("Amount must be a valid number")

def validate_category(category: Optional[str]) -> str:
    """
    Validate expense category.
    
    Args:
        category: Category to validate
        
    Returns:
        str: Validated category
    """
    if not category:
        return "General"
    
    if not isinstance(category, str):
        return "General"
    
    category = category.strip()
    
    if len(category) > 50:
        category = category[:50]
    
    # Remove potentially dangerous characters
    category = re.sub(r'[<>"\']', '', category)
    
    return category if category else "General"

def validate_schedule(schedule: Optional[str]) -> Optional[str]:
    """
    Validate recurring schedule.
    
    Args:
        schedule: Schedule to validate
        
    Returns:
        str or None: Validated schedule
    """
    if not schedule:
        return None
    
    if not isinstance(schedule, str):
        return None
    
    schedule = schedule.strip().lower()
    
    valid_schedules = ['daily', 'weekly', 'monthly', 'yearly']
    
    if schedule in valid_schedules:
        return schedule
    
    return None

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str (str): Input string to sanitize
        
    Returns:
        str: Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    
    # Limit length
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized.strip()
