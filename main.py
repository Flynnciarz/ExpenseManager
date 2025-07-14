import sqlite3
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.password_hasher import hash_password, verify_password
from utils.validators import (
    validate_username, validate_password, validate_expense_name,
    validate_amount, validate_category, validate_schedule,
    sanitize_input, ValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expense_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

class ExpenseManager:
    """
    Secure expense management system with comprehensive error handling.
    """
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    
    def __init__(self, db_path: str = 'expenses.db'):
        """
        Initialize the ExpenseManager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.current_user_id = None
        self.current_username = None
        self._initialize_database()
        logger.info("ExpenseManager initialized")
    
    def _initialize_database(self):
        """Initialize the database with proper schema."""
        try:
            with self._get_db_connection() as conn:
                # Read and execute schema
                schema_path = os.path.join(os.path.dirname(__file__), 'db', 'schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        conn.executescript(f.read())
                else:
                    # Fallback schema if file doesn't exist
                    self._create_fallback_schema(conn)
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    def _create_fallback_schema(self, conn: sqlite3.Connection):
        """Create fallback schema if schema.sql is not found."""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until DATETIME,
            is_active BOOLEAN DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL CHECK(length(name) > 0),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT DEFAULT 'General',
            recurring BOOLEAN DEFAULT 0,
            schedule TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS expense_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            expense_id INTEGER NOT NULL,
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            amount REAL NOT NULL CHECK(amount > 0),
            action TEXT NOT NULL CHECK(action IN ('CREATE', 'UPDATE', 'DELETE')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
        );
        """
        conn.executescript(schema)
    
    @contextmanager
    def _get_db_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _log_expense_history(self, conn: sqlite3.Connection, user_id: int, 
                           expense_id: int, action: str, amount: float):
        """Log expense changes for audit trail."""
        try:
            conn.execute(
                "INSERT INTO expense_history (user_id, expense_id, action, amount) VALUES (?, ?, ?, ?)",
                (user_id, expense_id, action, amount)
            )
        except Exception as e:
            logger.warning(f"Failed to log expense history: {e}")
    
    def _is_user_locked(self, username: str) -> bool:
        """Check if user account is locked due to failed login attempts."""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT failed_login_attempts, locked_until FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                failed_attempts, locked_until = row
                
                if locked_until:
                    locked_until_dt = datetime.fromisoformat(locked_until)
                    if datetime.now() < locked_until_dt:
                        return True
                    else:
                        # Unlock the account
                        conn.execute(
                            "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = ?",
                            (username,)
                        )
                        conn.commit()
                
                return False
        except Exception as e:
            logger.error(f"Error checking user lock status: {e}")
            return False
    
    def _handle_failed_login(self, username: str):
        """Handle failed login attempt."""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT failed_login_attempts FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                
                if row:
                    failed_attempts = row[0] + 1
                    locked_until = None
                    
                    if failed_attempts >= self.MAX_LOGIN_ATTEMPTS:
                        locked_until = (datetime.now() + self.LOCKOUT_DURATION).isoformat()
                    
                    conn.execute(
                        "UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE username = ?",
                        (failed_attempts, locked_until, username)
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error handling failed login: {e}")
    
    def _reset_failed_login_attempts(self, username: str):
        """Reset failed login attempts on successful login."""
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    "UPDATE users SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP WHERE username = ?",
                    (username,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error resetting failed login attempts: {e}")
    
    def create_user(self, username: str, password: str) -> int:
        """
        Create a new user account.
        
        Args:
            username (str): Username for the new account
            password (str): Password for the new account
            
        Returns:
            int: User ID of the created user
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Validate inputs
            username = validate_username(sanitize_input(username))
            password = validate_password(password)
            
            # Hash password
            password_hash = hash_password(password)
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"User created successfully: {username} (ID: {user_id})")
                return user_id
                
        except ValidationError:
            raise
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValidationError("Username already exists")
            raise DatabaseError(f"Failed to create user: {e}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise DatabaseError(f"Failed to create user: {e}")
    
    def login_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            bool: True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If input validation fails
        """
        try:
            # Validate inputs
            username = validate_username(sanitize_input(username))
            
            # Check if account is locked
            if self._is_user_locked(username):
                raise AuthenticationError("Account is temporarily locked due to too many failed login attempts")
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, password_hash, is_active FROM users WHERE username = ?",
                    (username,)
                )
                row = cursor.fetchone()
                
                if not row:
                    self._handle_failed_login(username)
                    raise AuthenticationError("Invalid username or password")
                
                user_id, stored_hash, is_active = row
                
                if not is_active:
                    raise AuthenticationError("Account is deactivated")
                
                if verify_password(password, stored_hash):
                    self._reset_failed_login_attempts(username)
                    self.current_user_id = user_id
                    self.current_username = username
                    logger.info(f"User logged in successfully: {username}")
                    return True
                else:
                    self._handle_failed_login(username)
                    raise AuthenticationError("Invalid username or password")
                    
        except (ValidationError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise AuthenticationError("Login failed due to system error")
    
    def logout(self):
        """Logout the current user."""
        if self.current_username:
            logger.info(f"User logged out: {self.current_username}")
        self.current_user_id = None
        self.current_username = None
    
    def add_expense(self, name: str, amount: float, category: str = "General", 
                   recurring: bool = False, schedule: Optional[str] = None) -> int:
        """
        Add a new expense.
        
        Args:
            name (str): Expense name
            amount (float): Expense amount
            category (str): Expense category
            recurring (bool): Whether expense is recurring
            schedule (str, optional): Recurring schedule
            
        Returns:
            int: Expense ID
            
        Raises:
            AuthenticationError: If user not logged in
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        if not self.current_user_id:
            raise AuthenticationError("Must be logged in to add expenses")
        
        try:
            # Validate inputs
            name = validate_expense_name(sanitize_input(name))
            amount = validate_amount(amount)
            category = validate_category(sanitize_input(category))
            schedule = validate_schedule(sanitize_input(schedule)) if schedule else None
            
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO expenses (user_id, name, amount, category, recurring, schedule) VALUES (?, ?, ?, ?, ?, ?)",
                    (self.current_user_id, name, amount, category, recurring, schedule)
                )
                expense_id = cursor.lastrowid
                
                # Log to history
                self._log_expense_history(conn, self.current_user_id, expense_id, 'CREATE', amount)
                
                conn.commit()
                logger.info(f"Expense added: {name} (${amount}) for user {self.current_username}")
                return expense_id
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            raise DatabaseError(f"Failed to add expense: {e}")
    
    def remove_expense(self, expense_id: int) -> bool:
        """
        Remove an expense.
        
        Args:
            expense_id (int): ID of expense to remove
            
        Returns:
            bool: True if expense was removed
            
        Raises:
            AuthenticationError: If user not logged in
            ValidationError: If expense doesn't exist or doesn't belong to user
            DatabaseError: If database operation fails
        """
        if not self.current_user_id:
            raise AuthenticationError("Must be logged in to remove expenses")
        
        try:
            with self._get_db_connection() as conn:
                # Check if expense exists and belongs to user
                cursor = conn.execute(
                    "SELECT amount FROM expenses WHERE id = ? AND user_id = ? AND is_active = 1",
                    (expense_id, self.current_user_id)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise ValidationError("Expense not found or access denied")
                
                amount = row[0]
                
                # Soft delete
                conn.execute(
                    "UPDATE expenses SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (expense_id,)
                )
                
                # Log to history
                self._log_expense_history(conn, self.current_user_id, expense_id, 'DELETE', amount)
                
                conn.commit()
                logger.info(f"Expense removed: ID {expense_id} for user {self.current_username}")
                return True
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error removing expense: {e}")
            raise DatabaseError(f"Failed to remove expense: {e}")
    
    def get_expenses(self) -> List[Dict[str, Any]]:
        """
        Get all active expenses for the current user.
        
        Returns:
            List[Dict]: List of expense dictionaries
            
        Raises:
            AuthenticationError: If user not logged in
            DatabaseError: If database operation fails
        """
        if not self.current_user_id:
            raise AuthenticationError("Must be logged in to view expenses")
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, name, amount, category, recurring, schedule, created_at FROM expenses WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
                    (self.current_user_id,)
                )
                
                expenses = []
                for row in cursor.fetchall():
                    expenses.append({
                        'id': row[0],
                        'name': row[1],
                        'amount': row[2],
                        'category': row[3],
                        'recurring': bool(row[4]),
                        'schedule': row[5],
                        'created_at': row[6]
                    })
                
                return expenses
                
        except Exception as e:
            logger.error(f"Error getting expenses: {e}")
            raise DatabaseError(f"Failed to get expenses: {e}")
    
    def update_expense(self, expense_id: int, name: str, amount: float, 
                      category: str = "General", recurring: bool = False, 
                      schedule: Optional[str] = None) -> bool:
        """
        Update an existing expense.
        
        Args:
            expense_id (int): ID of expense to update
            name (str): New expense name
            amount (float): New expense amount
            category (str): New expense category
            recurring (bool): Whether expense is recurring
            schedule (str, optional): New recurring schedule
            
        Returns:
            bool: True if expense was updated
            
        Raises:
            AuthenticationError: If user not logged in
            ValidationError: If input validation fails or expense doesn't exist
            DatabaseError: If database operation fails
        """
        if not self.current_user_id:
            raise AuthenticationError("Must be logged in to update expenses")
        
        try:
            # Validate inputs
            name = validate_expense_name(sanitize_input(name))
            amount = validate_amount(amount)
            category = validate_category(sanitize_input(category))
            schedule = validate_schedule(sanitize_input(schedule)) if schedule else None
            
            with self._get_db_connection() as conn:
                # Check if expense exists and belongs to user
                cursor = conn.execute(
                    "SELECT id FROM expenses WHERE id = ? AND user_id = ? AND is_active = 1",
                    (expense_id, self.current_user_id)
                )
                
                if not cursor.fetchone():
                    raise ValidationError("Expense not found or access denied")
                
                # Update expense
                conn.execute(
                    "UPDATE expenses SET name = ?, amount = ?, category = ?, recurring = ?, schedule = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (name, amount, category, recurring, schedule, expense_id)
                )
                
                # Log to history
                self._log_expense_history(conn, self.current_user_id, expense_id, 'UPDATE', amount)
                
                conn.commit()
                logger.info(f"Expense updated: ID {expense_id} for user {self.current_username}")
                return True
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating expense: {e}")
            raise DatabaseError(f"Failed to update expense: {e}")

def main():
    """Main application loop with improved error handling."""
    manager = ExpenseManager()
    
    print("=" * 50)
    print("    SECURE EXPENSE MANAGEMENT SYSTEM")
    print("=" * 50)
    print()
    
    while True:
        try:
            if not manager.current_user_id:
                print("\n--- Authentication Required ---")
                print("1. Login")
                print("2. Register")
                print("3. Quit")
                
                choice = input("\nChoose an option (1-3): ").strip()
                
                if choice == "1":
                    username = input("Enter username: ").strip()
                    password = input("Enter password: ").strip()
                    
                    try:
                        if manager.login_user(username, password):
                            print(f"\n✓ Welcome back, {username}!")
                    except (AuthenticationError, ValidationError) as e:
                        print(f"\n✗ Login failed: {e}")
                
                elif choice == "2":
                    print("\n--- Create New Account ---")
                    print("Password requirements:")
                    print("- At least 8 characters")
                    print("- At least one uppercase letter")
                    print("- At least one lowercase letter")
                    print("- At least one digit")
                    print()
                    
                    username = input("Enter username: ").strip()
                    password = input("Enter password: ").strip()
                    
                    try:
                        user_id = manager.create_user(username, password)
                        print(f"\n✓ Account created successfully! User ID: {user_id}")
                        print("You can now login with your credentials.")
                    except (ValidationError, DatabaseError) as e:
                        print(f"\n✗ Registration failed: {e}")
                
                elif choice == "3":
                    print("\nGoodbye!")
                    break
                
                else:
                    print("\n✗ Invalid choice. Please select 1, 2, or 3.")
            
            else:
                print(f"\n--- Logged in as: {manager.current_username} ---")
                print("1. Add Expense")
                print("2. View Expenses")
                print("3. Update Expense")
                print("4. Remove Expense")
                print("5. Logout")
                print("6. Quit")
                
                choice = input("\nChoose an option (1-6): ").strip()
                
                if choice == "1":
                    print("\n--- Add New Expense ---")
                    try:
                        name = input("Expense name: ").strip()
                        amount = input("Amount ($): ").strip()
                        category = input("Category (optional): ").strip() or "General"
                        recurring_input = input("Is this recurring? (y/n): ").strip().lower()
                        recurring = recurring_input in ['y', 'yes']
                        schedule = None
                        
                        if recurring:
                            schedule = input("Schedule (daily/weekly/monthly/yearly): ").strip()
                        
                        expense_id = manager.add_expense(name, amount, category, recurring, schedule)
                        print(f"\n✓ Expense added successfully! ID: {expense_id}")
                        
                    except (ValidationError, DatabaseError) as e:
                        print(f"\n✗ Failed to add expense: {e}")
                
                elif choice == "2":
                    print("\n--- Your Expenses ---")
                    try:
                        expenses = manager.get_expenses()
                        if not expenses:
                            print("No expenses found.")
                        else:
                            print(f"{'ID':<5} {'Name':<20} {'Amount':<10} {'Category':<15} {'Recurring':<10} {'Schedule':<10}")
                            print("-" * 80)
                            for expense in expenses:
                                recurring_text = "Yes" if expense['recurring'] else "No"
                                schedule_text = expense['schedule'] or "-"
                                print(f"{expense['id']:<5} {expense['name'][:19]:<20} ${expense['amount']:<9.2f} {expense['category']:<15} {recurring_text:<10} {schedule_text:<10}")
                    
                    except DatabaseError as e:
                        print(f"\n✗ Failed to get expenses: {e}")
                
                elif choice == "3":
                    print("\n--- Update Expense ---")
                    try:
                        expense_id = int(input("Enter expense ID to update: ").strip())
                        name = input("New expense name: ").strip()
                        amount = input("New amount ($): ").strip()
                        category = input("New category (optional): ").strip() or "General"
                        recurring_input = input("Is this recurring? (y/n): ").strip().lower()
                        recurring = recurring_input in ['y', 'yes']
                        schedule = None
                        
                        if recurring:
                            schedule = input("New schedule (daily/weekly/monthly/yearly): ").strip()
                        
                        if manager.update_expense(expense_id, name, amount, category, recurring, schedule):
                            print(f"\n✓ Expense updated successfully!")
                        
                    except ValueError:
                        print("\n✗ Invalid expense ID. Please enter a number.")
                    except (ValidationError, DatabaseError) as e:
                        print(f"\n✗ Failed to update expense: {e}")
                
                elif choice == "4":
                    print("\n--- Remove Expense ---")
                    try:
                        expense_id = int(input("Enter expense ID to remove: ").strip())
                        confirm = input(f"Are you sure you want to remove expense ID {expense_id}? (y/n): ").strip().lower()
                        
                        if confirm in ['y', 'yes']:
                            if manager.remove_expense(expense_id):
                                print(f"\n✓ Expense removed successfully!")
                        else:
                            print("\n✗ Operation cancelled.")
                        
                    except ValueError:
                        print("\n✗ Invalid expense ID. Please enter a number.")
                    except (ValidationError, DatabaseError) as e:
                        print(f"\n✗ Failed to remove expense: {e}")
                
                elif choice == "5":
                    manager.logout()
                    print("\n✓ Logged out successfully!")
                
                elif choice == "6":
                    manager.logout()
                    print("\nGoodbye!")
                    break
                
                else:
                    print("\n✗ Invalid choice. Please select 1-6.")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            manager.logout()
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            print(f"\n✗ An unexpected error occurred: {e}")
            print("Please try again or contact support if the problem persists.")

if __name__ == "__main__":
    main()
