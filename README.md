# RevouBank API

## Overview
RevouBank API is a RESTful banking system that provides user management, account management, and transaction management functionalities. It is designed to simulate real-world banking operations with security enhancements such as account locking after failed login attempts, email notifications, and invoice generation. 

Note: Due to mailtrap limit, the email and invoice generator are in mock.

To access api docs using Swagger/Flask, visit this link:
<br> https://final-jacklyn-mrifqiprojects-728a1fab.koyeb.app/docs
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

<br> <br>

## Installation and Setup

### Prerequisites
- Python 3.12
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

### Configure Environment Variables
Create a `.env` file in the project root and add the following:
```env
MOCK_EMAIL=True
MAIL_SERVER=smtp.elasticemail.com
MAIL_PORT=2525
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=revoubank@mail.com # currently inactive
MAIL_PASSWORD= # currently inactive
MAIL_DEFAULT_SENDER=revoubank@mail.com # currently inactive
SECRET_KEY=your-secret-key
DATABASE_URL=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Start the Server
```sh
python -m app.app  /  uv python -m app.app (if using uv)
```
Or
```sh
FLASK_APP=app/app.py flask run --debug
```

<br> <br>

## API Access Rundown

Before using any protected endpoints in this API, authentication is **required**. Follow the steps below to get started:



### 1. Register a New User

- Navigate to the `users` section.
- Use the `POST /users/` endpoint to register a new user.
- Example request body (feel free to edit as needed):

```json
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_secure_password"
}
```


### 2. Login to Obtain Token

- Go to the `auth` section.
- Use the `POST /token` endpoint with the registered username and password.



### 3. Copy the Access Token

- If login is successful (HTTP 200), the response will look like this:

```json
{
  "access_token": "your.jwt.access.token.here",
  "token_type": "bearer"
}
```

- Copy the value of `access_token`.



### 4. Authorize with the Token

- Scroll to the top-right corner of the Swagger page.
- Click on the **Authorize** button.
- Paste the token in the following format:

```
Bearer your.jwt.access.token.here
```

- Click **Authorize** to apply the token to all secured endpoints.


### 5. You're Ready!

You can now access and test all authorized endpoints in the API.

<br> <br>


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

