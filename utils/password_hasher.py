import bcrypt
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
        
    Raises:
        ValueError: If password is empty or None
        Exception: If hashing fails
    """
    try:
        if not password or not password.strip():
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise Exception("Failed to hash password")

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): Plain text password
        hashed_password (str): Hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
        
    Raises:
        ValueError: If inputs are invalid
        Exception: If verification fails
    """
    try:
        if not password or not hashed_password:
            raise ValueError("Password and hash cannot be empty")
        
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False
