# Secure Expense Management System

A robust, secure command-line expense management application built with Python, SQLite, and Docker. This application features comprehensive error handling, security measures, and user authentication.

## Features

### Security Features
- **Strong Password Requirements**: Minimum 8 characters with uppercase, lowercase, and digits
- **Account Lockout Protection**: Automatic account lockout after 5 failed login attempts
- **Password Hashing**: Secure bcrypt hashing with salt
- **Input Validation**: Comprehensive validation and sanitization of all user inputs
- **SQL Injection Protection**: Parameterized queries and input sanitization
- **Audit Trail**: Complete expense history logging for all operations

### Core Functionality
- **User Management**: Secure user registration and authentication
- **Expense Tracking**: Add, view, update, and remove expenses
- **Categories**: Organize expenses by category
- **Recurring Expenses**: Support for daily, weekly, monthly, and yearly recurring expenses
- **Soft Delete**: Expenses are marked as inactive rather than permanently deleted
- **Comprehensive Logging**: Application and error logging to files

### Data Validation
- Username: 3-50 characters, alphanumeric with underscores and hyphens
- Password: 8-128 characters with complexity requirements
- Expense amounts: Positive numbers up to $999,999.99
- Expense names: 1-100 characters with dangerous character filtering
- Categories: Up to 50 characters with sanitization

## Project Structure

```
expense_manager/
├── main.py                 # Main application with ExpenseManager class
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── README.md              # This documentation
├── db/
│   ├── schema.sql         # Database schema definition
│   └── create_tables.sql  # Database initialization script
└── utils/
    ├── password_hasher.py # Secure password hashing utilities
    └── validators.py      # Input validation and sanitization
```

## Installation and Setup

### Option 1: Direct Python Installation

1. **Clone or download the project**
   ```bash
   cd expense_manager
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Option 2: Docker Installation

1. **Build the Docker image**
   ```bash
   docker build -t expense-manager .
   ```

2. **Run the container**
   ```bash
   docker run -it --name expense-app expense-manager
   ```

3. **Run with persistent data (recommended)**
   ```bash
   docker run -it -v $(pwd)/data:/app/data --name expense-app expense-manager
   ```

## Usage Guide

### First Time Setup

1. **Start the application**
   - The application will automatically create the database on first run
   - You'll see the main authentication menu

2. **Create an account**
   - Select option "2. Register"
   - Choose a username (3-50 characters, alphanumeric with _ and -)
   - Create a strong password meeting the requirements:
     - At least 8 characters
     - At least one uppercase letter
     - At least one lowercase letter
     - At least one digit

3. **Login**
   - Select option "1. Login"
   - Enter your credentials

### Managing Expenses

Once logged in, you can:

#### Add Expenses
- Select "1. Add Expense"
- Enter expense details:
  - Name: Descriptive name for the expense
  - Amount: Positive dollar amount
  - Category: Optional category (defaults to "General")
  - Recurring: Whether this is a recurring expense
  - Schedule: If recurring, specify frequency (daily/weekly/monthly/yearly)

#### View Expenses
- Select "2. View Expenses"
- See all your active expenses in a formatted table
- Displays ID, name, amount, category, recurring status, and schedule

#### Update Expenses
- Select "3. Update Expense"
- Enter the expense ID to modify
- Provide new values for all fields

#### Remove Expenses
- Select "4. Remove Expense"
- Enter the expense ID to remove
- Confirm the deletion (expenses are soft-deleted, not permanently removed)

### Security Features in Action

#### Account Lockout
- After 5 failed login attempts, accounts are locked for 30 minutes
- Lockout is automatically lifted after the timeout period
- Successful login resets the failed attempt counter

#### Input Validation
- All inputs are validated and sanitized before processing
- Invalid inputs result in clear error messages
- Dangerous characters are filtered from text inputs

#### Audit Trail
- All expense operations (create, update, delete) are logged
- History includes user ID, expense ID, action type, amount, and timestamp
- Logs are stored in the `expense_history` table

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Bcrypt hashed password
- `created_at`: Account creation timestamp
- `last_login`: Last successful login
- `failed_login_attempts`: Failed login counter
- `locked_until`: Account lockout expiration
- `is_active`: Account status flag

### Expenses Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `name`: Expense name
- `amount`: Expense amount (positive)
- `category`: Expense category
- `recurring`: Boolean for recurring expenses
- `schedule`: Recurring schedule (daily/weekly/monthly/yearly)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp
- `is_active`: Soft delete flag

### Expense History Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `expense_id`: Foreign key to expenses table
- `date`: Transaction date
- `amount`: Transaction amount
- `action`: Action type (CREATE/UPDATE/DELETE)
- `created_at`: History entry timestamp

## Error Handling

The application includes comprehensive error handling for:

### Database Errors
- Connection failures
- Constraint violations
- Transaction rollbacks
- Timeout handling

### Validation Errors
- Invalid input formats
- Out-of-range values
- Missing required fields
- Dangerous input patterns

### Authentication Errors
- Invalid credentials
- Account lockouts
- Inactive accounts
- Session management

### System Errors
- File system issues
- Memory constraints
- Unexpected exceptions

## Logging

The application maintains detailed logs:

### Log Files
- `expense_manager.log`: Application events and errors
- Console output: Real-time feedback to users

### Log Levels
- **INFO**: Normal operations (login, expense operations)
- **WARNING**: Non-critical issues (audit trail failures)
- **ERROR**: Serious errors (database failures, authentication issues)

### Log Format
```
YYYY-MM-DD HH:MM:SS - module_name - LEVEL - message
```

## Security Best Practices

### Implemented Security Measures
1. **Password Security**
   - Bcrypt hashing with salt
   - Strong password requirements
   - No password storage in plain text

2. **Input Security**
   - Comprehensive input validation
   - SQL injection prevention
   - XSS prevention through input sanitization

3. **Access Control**
   - User-based data isolation
   - Authentication required for all operations
   - Account lockout protection

4. **Audit Security**
   - Complete operation logging
   - Tamper-evident audit trail
   - User action tracking

### Additional Recommendations
1. **Environment Security**
   - Run in isolated containers
   - Use non-root users
   - Implement file system permissions

2. **Network Security**
   - Use HTTPS for any web interfaces
   - Implement rate limiting
   - Monitor for suspicious activity

3. **Data Security**
   - Regular database backups
   - Encrypt sensitive data at rest
   - Implement data retention policies

## Troubleshooting

### Common Issues

#### Database Connection Errors
```
DatabaseError: Database operation failed
```
**Solution**: Ensure the application has write permissions in the current directory

#### Import Errors
```
ModuleNotFoundError: No module named 'bcrypt'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

#### Permission Errors (Docker)
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Ensure proper volume mounting and user permissions

#### Account Lockout
```
AuthenticationError: Account is temporarily locked
```
**Solution**: Wait 30 minutes or check the `locked_until` field in the database

### Debug Mode

To enable debug logging, modify the logging configuration in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### Database Recovery

If the database becomes corrupted:
1. Stop the application
2. Delete the `expenses.db` file
3. Restart the application (will recreate the database)
4. Restore from backup if available

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Include comprehensive docstrings
- Maintain test coverage

### Security Considerations
- Validate all inputs
- Use parameterized queries
- Implement proper error handling
- Follow principle of least privilege

## License

This project is provided as-is for educational and personal use. Please ensure compliance with applicable laws and regulations when using this software.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the application logs
3. Verify your environment setup
4. Ensure all dependencies are installed correctly
