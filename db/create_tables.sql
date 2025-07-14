-- Initialize the expense management database
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = memory;
PRAGMA mmap_size = 268435456; -- 256MB

BEGIN TRANSACTION;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS expense_history;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS users;

-- Users table with additional security fields
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME,
    is_active BOOLEAN DEFAULT 1
);

-- Expenses table with validation constraints
CREATE TABLE expenses (
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

-- Expense history for audit trail
CREATE TABLE expense_history (
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

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_expense_history_user_id ON expense_history(user_id);
CREATE INDEX idx_expense_history_date ON expense_history(date);

COMMIT;
