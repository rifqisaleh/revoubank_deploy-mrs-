import os
from flask import Flask, request, jsonify
from datetime import timedelta, datetime
from flask_jwt_extended import create_access_token, JWTManager
from config import Config
from app.utils.user import verify_password
from app.database.db import db, SessionLocal
from app.model.models import User
from app.services.email.utils import send_email_async
from app.core.auth import generate_access_token
from app.core.extensions import limiter
from flask_cors import CORS
from contextlib import contextmanager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import swag_from

# Initialize Migrate object
migrate = Migrate()
jwt = JWTManager()


# ✅ Context-managed DB session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Flask app factory
def create_app(test_config=None):
    app = Flask(__name__)
    limiter.init_app(app)
    
    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)
        
    app.config["JWT_SECRET_KEY"] = "1d7b852e9664c5b1178f5cfb314e612d2cf96646e6eaa30a2348193cf9e49559"
    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)   
    
    # ✅ Register blueprints
    from app.routes import users, accounts, transactions, external_transaction, billpayment, bills, budgets, categories, auth
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(users.users_bp, url_prefix="/users")
    app.register_blueprint(accounts.accounts_bp, url_prefix="/accounts")
    app.register_blueprint(transactions.transactions_bp, url_prefix="/transactions")
    app.register_blueprint(external_transaction.external_transaction_bp)
    app.register_blueprint(billpayment.billpayment_bp)
    app.register_blueprint(bills.bills_bp)
    app.register_blueprint(budgets.budgets_bp)
    app.register_blueprint(categories.categories_bp)
    
    return app


    