from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.transactions import router as transactions_router
from app.routes.users import router as users_router
from app.routes.accounts import router as accounts_router  

app = FastAPI()

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
app.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
