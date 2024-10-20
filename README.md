# Expense Splitter API

A FastAPI-based expense splitting application that helps users manage and split expenses within groups. The application supports multiple splitting methods including equal splits, exact amounts, and percentage-based splits.

## Features

- User Management
  - Create new users
  - Retrieve user details

- Expense Management
  - Add new expenses with different splitting methods
    - Equal split
    - Exact amount split
    - Percentage-based split
  - View expenses by user
  - View all expenses

- Balance Sheet
  - Get current balances for all users
  - Download balance sheet as CSV

## Technical Stack

- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

## Setup and Installation

1. Clone the repository
```bash
git clone [repository-url]
cd expense-splitter
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the application
```bash
uvicorn main:app --reload
```

## API Endpoints

### Users
- `POST /users/` - Create a new user
- `GET /users/{user_id}` - Get user details

### Expenses
- `POST /expenses/` - Add a new expense
- `GET /expenses/` - Get all expenses
- `GET /expenses/user/{user_id}` - Get expenses for a specific user

### Balance Sheet
- `GET /balance-sheet/` - Get current balance sheet
- `GET /balance-sheet/download/` - Download balance sheet as CSV

## API Usage Examples

### Creating a User
```bash
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "mobile": "1234567890"
}'
```

### Adding an Expense (Equal Split)
```bash
curl -X POST "http://localhost:8000/expenses/" -H "Content-Type: application/json" -d '{
    "amount": 100.00,
    "description": "Dinner",
    "split_method": "equal",
    "payer_id": 1,
    "splits": [
        {"user_id": 1},
        {"user_id": 2}
    ]
}'
```

## Database Schema

- Users
  - id: Integer (Primary Key)
  - email: String (Unique)
  - name: String
  - mobile: String

- Expenses
  - id: Integer (Primary Key)
  - amount: Float
  - description: String
  - split_method: String
  - payer_id: Integer (Foreign Key)

- Splits
  - id: Integer (Primary Key)
  - expense_id: Integer (Foreign Key)
  - user_id: Integer (Foreign Key)
  - amount: Float
  - percentage: Float (Optional)
