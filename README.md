# RevouBank API




## Directory

- [🔹 Overview](#overview)
- [🔹 Features Implemented](#features-implemented)
- [🔹 Installation and Setup](#installation-and-setup)
- [🔹 API Access Rundown](#api-access-rundown)
- [🔹 API Usage](#api-usage)
  - [Authentication](#authentication)
  - [Account Management](#account-management)
  - [Transactions](#transactions)
- [🔹 Testing Setup & Safety Notes](#testing-setup--safety-notes)
- [🔹 Deployment](#deployment)



## Overview
RevouBank API is a RESTful banking system that provides user management, account management, and transaction management functionalities. It is designed to simulate real-world banking operations with security enhancements such as account locking after failed login attempts, email notifications, and invoice generation. 

Note: Due to mailtrap limit, the email and invoice generator are in mock.

To access api docs using Swagger/Flask, visit this link:
<br> 
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
or

```
uv sync
```

### Configure Environment Variables

*Note: Delete all MAIL_ if you decide not to use SMTP (email). Only keep MOCK_EMAIL*

Create a `.env` file in the project root and add the following:
```env
MOCK_EMAIL=True
MAIL_SERVER=
MAIL_PORT=
MAIL_USE_TLS=
MAIL_USE_SSL=
MAIL_USERNAME=
MAIL_PASSWORD= 
MAIL_DEFAULT_SENDER=
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
<br> <br>

##  Testing Setup & Safety Notes

To ensure tests do **not affect the production database**, a dedicated test environment is configured using an in-memory SQLite database. Below are the key points regarding testing and isolation.

<br>

###  1. `.env.test` is available for safe testing

A `.env.test` file is provided in the project root, which sets the test environment:

```env
FLASK_ENV=test
TESTING=True
DATABASE_URL=sqlite:///:memory:
```

This configuration ensures that all tests use an **in-memory SQLite database**, which is created fresh on every test run and discarded afterward.

<br>

### 2. Safety Assertion in `conftest.py`

The test configuration includes a fail-safe in `conftest.py`:

```python
assert "sqlite" in db_url, f"❌ NOT using a test database! Current DATABASE_URL: {db_url}"
```

This stops the test immediately if the app is connected to a non-test database (e.g., Supabase), preventing unintended changes to production data.

<br>

### 3. Running tests safely

#### First-time test run with override (recommended for safety):

```bash
DATABASE_URL=sqlite:///:memory: pytest --maxfail=1
```

This command forces the test database to use SQLite and stops at the first failure, allowing you to verify the setup without running the full test suite.

#### If the assertion passes or you've fixed the config:

You can safely run the full suite with either:

```bash
DATABASE_URL=sqlite:///:memory: pytest
```

or simply:

```bash
pytest
```

(as long as `.env.test` is loaded properly and no conflicting `DATABASE_URL` is active in your shell)


<br> <br>

## Deployment
The RevouBank API is deployed on **Koyeb**.

<br> https://final-jacklyn-mrifqiprojects-728a1fab.koyeb.app/docs

---

For further inquiries, contact [mrifqisaleh@gmail.com] or check out the project repository.

