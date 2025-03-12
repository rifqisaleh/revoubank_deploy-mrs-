import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from app.routes.transactions import router as transactions_router
from app.routes.users import router as users_router
from app.routes.accounts import router as accounts_router  
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from app.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils.user import verify_password, create_access_token
from app.mock_database import get_mock_db
from app.services.email.utils import send_email_async
from app.routes.billpayment import router as billpayment_router
from app.routes.external_transaction import router as external_transaction_router

app = FastAPI()

LOCK_DURATION = timedelta(minutes=15)
MAX_FAILED_ATTEMPTS = 5

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
app.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])  
app.include_router(billpayment_router, prefix="/billpayment", tags=["Bill Payment"])
app.include_router(external_transaction_router, prefix="/api", tags=["External Transactions"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/")
def home():
    return {"message": "Welcome to RevouBank API"}


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), background_tasks: BackgroundTasks = None):
    username = form_data.username
    password = form_data.password

    user = next((user for user in get_mock_db()["users"].values() if user["username"] == username), None)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password.")

    if user["is_locked"]:
        locked_time = user.get("locked_time")
        if locked_time and datetime.utcnow() > locked_time + LOCK_DURATION:
            user["is_locked"] = False
            user["failed_attempts"] = 0
        else:
            raise HTTPException(status_code=403, detail="Account is locked due to multiple failed login attempts. Please try again later.")

    if not verify_password(password, user["password"]):
        user["failed_attempts"] += 1

        if user["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
            user["is_locked"] = True
            user["locked_time"] = datetime.utcnow()
            raise HTTPException(status_code=403, detail="Account locked due to multiple failed attempts. Please wait 15 minutes.")
        
        raise HTTPException(status_code=400, detail=f"Incorrect password. Attempts left: {MAX_FAILED_ATTEMPTS - user['failed_attempts']}")

    # Reset login attempts after successful login
    user["failed_attempts"] = 0
    user["is_locked"] = False
    user["locked_time"] = None

    # Create JWT token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)

    # Send Email Notification Asynchronously
    user_email = "testuser@example.com" 

    email_subject = "Successful Login Notification"
    email_body = f"""
        <p>Hello {username},</p>
        <p>You have successfully logged into your RevouBank account.</p>
        <p>If you didn't authorize this login, please contact support immediately.</p>
        """

    background_tasks.add_task(
        send_email_async,
        subject=email_subject,
        recipient=user_email,
        body=email_body
    )

    return {"access_token": access_token, "token_type": "bearer"}