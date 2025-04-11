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
<br> https://artistic-aardwolf-mrifqiprojects-222ae619.koyeb.app/
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

```bash
curl -X POST http://localhost:5000/users/   -H "Content-Type: application/json"   -d '{
    "email": "<add_email>",
    "full_name": "<add_full_name>",
    "password": "<add_password>",
    "phone_number": "<add_phone_number>",
    "username": "<add_username>"
  }'
```

This will trigger a **mock verification email** in your terminal output (if `MOCK_EMAIL=True`).



### 2. Login to Obtain Token

```bash
curl -X POST http://localhost:5000/login   -H "Content-Type: application/json"   -d '{
    "username": "<add_username>",
    "password": "<add_password>"
  }'
```

Successful login will return a token like:

```json
{
  "access_token": "your.jwt.access.token.here",
  "token_type": "bearer"
}
```


### 3. Authorize with the Token

Once you have the access token, use it with your preferred tool:

- **Swagger Docs** (`/docs`)  
  → Click **Authorize** and paste: `Bearer <your_access_token>`

- **Postman**  
  → Set Authorization type to **Bearer Token** and paste the token

- **Curl**  
  → Add header: `-H "Authorization: Bearer <your_access_token>"`

You’re now ready to hit all protected endpoints!

<br>

### Available Endpoints

#### Users

- `POST /users/`  
  Register a new user.

- `POST /login`  
  Authenticate and receive a JWT token.

- `GET /users/`  
  Retrieve a list of users (admin access required).

- `GET /users/<id>`  
  Retrieve details of a specific user.

- `PUT /users/<id>`  
  Update user information.

- `DELETE /users/<id>`  
  Delete a user (admin access required).

#### Accounts

- `GET /accounts/`  
  Retrieve a list of accounts for the authenticated user.

- `GET /accounts/<id>`  
  Retrieve details of a specific account.

- `POST /accounts/`  
  Create a new account.

- `PUT /accounts/<id>`  
  Update account information.

- `DELETE /accounts/<id>`  
  Delete an account.

#### Transactions

- `GET /transactions/`  
  Retrieve a list of transactions for the authenticated user.

- `GET /transactions/<id>`  
  Retrieve details of a specific transaction.

- `POST /transactions/deposit`  
  Deposit funds into an account.

- `POST /transactions/withdraw`  
  Withdraw funds from an account.

- `POST /transactions/transfer`  
  Transfer funds between accounts.

  <br>

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

<br> https://artistic-aardwolf-mrifqiprojects-222ae619.koyeb.app/

---

For further inquiries, contact [mrifqisaleh@gmail.com] or check out the project repository.

