#!/usr/bin/env python3
"""
Test script for the Secure Expense Management System.

This script performs basic functionality tests to ensure the application
is working correctly.
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from main import ExpenseManager
    from utils.validators import ValidationError
    from utils.password_hasher import hash_password, verify_password
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def test_password_hashing():
    """Test password hashing functionality."""
    print("Testing password hashing...")
    
    password = "TestPassword123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("WrongPassword", hashed), "Wrong password should not verify"
    
    print("✓ Password hashing tests passed")

def test_database_operations():
    """Test database operations."""
    print("Testing database operations...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        manager = ExpenseManager(db_path)
        
        # Test user creation
        user_id = manager.create_user("testuser", "TestPassword123")
        assert user_id > 0, "User creation failed"
        
        # Test login
        assert manager.login_user("testuser", "TestPassword123"), "Login failed"
        
        # Test expense operations
        expense_id = manager.add_expense("Test Expense", 50.00, "Food")
        assert expense_id > 0, "Expense creation failed"
        
        expenses = manager.get_expenses()
        assert len(expenses) == 1, "Expense retrieval failed"
        assert expenses[0]['name'] == "Test Expense", "Expense data incorrect"
        
        # Test expense update
        assert manager.update_expense(expense_id, "Updated Expense", 75.00), "Expense update failed"
        
        # Test expense removal
        assert manager.remove_expense(expense_id), "Expense removal failed"
        
        # Verify soft delete
        expenses = manager.get_expenses()
        assert len(expenses) == 0, "Expense should be soft deleted"
        
        print("✓ Database operations tests passed")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_validation():
    """Test input validation."""
    print("Testing input validation...")
    
    from utils.validators import (
        validate_username, validate_password, validate_expense_name,
        validate_amount, ValidationError
    )
    
    # Test username validation
    try:
        validate_username("ab")  # Too short
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Test password validation
    try:
        validate_password("weak")  # Too weak
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Test amount validation
    try:
        validate_amount(-10)  # Negative amount
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    
    # Test valid inputs
    assert validate_username("validuser") == "validuser"
    assert validate_password("ValidPass123") == "ValidPass123"
    assert validate_expense_name("Valid Expense") == "Valid Expense"
    assert validate_amount("50.00") == 50.00
    
    print("✓ Input validation tests passed")

def test_security_features():
    """Test security features."""
    print("Testing security features...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        manager = ExpenseManager(db_path)
        
        # Create user
        manager.create_user("securitytest", "TestPassword123")
        
        # Test account lockout (simulate failed attempts)
        for i in range(6):  # Exceed max attempts
            try:
                manager.login_user("securitytest", "wrongpassword")
            except:
                pass
        
        # Account should be locked now
        try:
            manager.login_user("securitytest", "TestPassword123")
            assert False, "Account should be locked"
        except Exception as e:
            assert "locked" in str(e).lower(), "Should indicate account is locked"
        
        print("✓ Security features tests passed")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

def main():
    """Run all tests."""
    print("=" * 50)
    print("    EXPENSE MANAGER TEST SUITE")
    print("=" * 50)
    print()
    
    try:
        test_password_hashing()
        test_validation()
        test_database_operations()
        test_security_features()
        
        print()
        print("=" * 50)
        print("    ALL TESTS PASSED! ✓")
        print("=" * 50)
        print()
        print("The application is ready to use.")
        print("Run 'python main.py' or 'python run.py' to start the application.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
