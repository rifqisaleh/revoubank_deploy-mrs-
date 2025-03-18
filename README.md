# RevouBank API

## Overview
RevouBank API is a RESTful banking system that provides user management, account management, and transaction management functionalities. It is designed to simulate real-world banking operations with security enhancements such as account locking after failed login attempts, email notifications, and invoice generation. 

Note: Due to mailtrap limit, the email and invoice generator are in mock.

To access api docs using Swagger/Flask, visit this link:
<br> https://curious-sher-mrifqiprojects-d23b26ed.koyeb.app/docs
<br> http://127.0.0.1:5000/docs (Local)

## Features Implemented
- **User Management**: User registration, login, and authentication.
- **Account Management**: Create, retrieve, update, and delete bank accounts.
- **Transaction Management**: Perform deposits, withdrawals, and transfers.
- **Security Enhancements**:
  - Account locking after multiple failed login attempts
  - Email notifications for authentication and transactions
  - Invoice generation for transactions
- **Testing**: Unit tests using pytest.
- **CI/CD**: GitHub Actions for automated deployment on Koyeb.

## Installation and Setup

### Prerequisites
- Python 3.11
- `uv` package manager (or `pip` if preferred)
- WSL (for Windows users)

### Clone the Repository
```sh
git clone https://github.com/rifqisaleh/revoubank_deploy-mrs-.git
cd revoubank-api
```

### Set Up Virtual Environment
```sh
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install Dependencies
```sh
uv pip install -r requirements.txt
```

### Synchronize Dependencies
```sh
uv sync
```

### Configure Environment Variables
Create a `.env` file in the project root and add the following:
```env
MOCK_EMAIL=True
MAIL_SERVER=smtp.elasticemail.com
MAIL_PORT=2525
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=revoubank@mail.com # currently inactive
MAIL_PASSWORD=868F26B2C069F91114EF706D672C49582F25 # currently inactive
MAIL_DEFAULT_SENDER=revoubank@mail.com # currently inactive
SECRET_KEY=your-secret-key
DATABASE_URL=mock
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Start the Server
```sh
python -m app.app 
```
Or
```sh
FLASK_APP=app/app.py flask run --debug
```

## API Usage

### Authentication
#### Register User
**Endpoint:** `POST /auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

#### Login
**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

### Account Management
#### Create Bank Account
**Endpoint:** `POST /accounts`

**Request:**
```json
{
  "account_type": "savings",
  "initial_deposit": 1000.00
}
```

**Response:**
```json
{
  "account_id": 1,
  "balance": 1000.00
}
```

### Transactions
#### Deposit Money
**Endpoint:** `POST /transactions/deposit`

**Request:**
```json
{
  "account_id": 1,
  "amount": 500.00
}
```

**Response:**
```json
{
  "message": "Deposit successful",
  "new_balance": 1500.00
}
```

### Running Tests
To run unit tests using pytest:
```sh
pytest
```

### Deployment
The RevouBank API is deployed on **Koyeb**.

---

For further inquiries, contact [mrifqisaleh@gmail.com] or check out the project repository.

