import os
from flask import Flask, request, jsonify
from datetime import timedelta
from app.core.auth import authenticate_user, create_access_token
from config import Config
from app.utils.user import verify_password
from app.database.db import db, get_db
from app.model.models import User
from app.services.email.utils import send_email_async
from flask_cors import CORS
from datetime import timedelta, datetime
from config import Config


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config.from_object(Config)
    db.init_app(app)
    CORS(app)
    
    # ✅ REGISTER BLUEPRINTS HERE
    from app.routes import users, accounts, transactions, external_transaction, billpayment
    app.register_blueprint(users.users_bp, url_prefix="/users")
    app.register_blueprint(accounts.accounts_bp, url_prefix="/accounts")
    app.register_blueprint(transactions.transactions_bp, url_prefix="/transactions")
    app.register_blueprint(external_transaction.external_transaction_bp)
    app.register_blueprint(billpayment.billpayment_bp)

    # ✅ ADD LOGIN ENDPOINT
    @app.route("/token", methods=["POST"])
    def login():
        """
        Authenticate user and generate JWT token
        ---
        parameters:
          - name: username
            in: formData
            type: string
            required: true
          - name: password
            in: formData
            type: string
            required: true
        responses:
          200:
            description: Returns access token
          400:
            description: Incorrect username or password
          403:
            description: Account is locked
        """
        db = next(get_db())
        form_data = request.form
        username = form_data.get("username")
        password = form_data.get("password")

        user = db.query(User).filter_by(username=username).first()

        if not user:
            return jsonify({"detail": "Incorrect username or password."}), 400

        # Check if account is locked
        if user.is_locked:
            if user.locked_time and datetime.utcnow() > user.locked_time + Config.LOCK_DURATION:
                user.is_locked = False
                user.failed_attempts = 0
                db.commit()
            else:
                return jsonify({"detail": "Account is locked due to multiple failed login attempts. Please try again later."}), 403

        if not verify_password(password, user.password):
            user.failed_attempts += 1

            if user.failed_attempts >= Config.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                user.locked_time = datetime.utcnow()

                # Send lock email
                send_email_async(
                    subject="Your RevouBank Account is Locked",
                    recipient=user.email,
                    body=f"""
                    Dear {username},

                    Your RevouBank account has been locked due to multiple failed login attempts.
                    Please wait 15 minutes before trying again.

                    - RevouBank Support
                    """
                )

            db.commit()

            attempts_left = Config.MAX_FAILED_ATTEMPTS - user.failed_attempts
            return jsonify({"detail": f"Incorrect password. Attempts left: {attempts_left}"}), 400

        # Successful login
        user.failed_attempts = 0
        user.is_locked = False
        user.locked_time = None
        db.commit()

        # Generate JWT token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

        return jsonify({"access_token": access_token, "token_type": "bearer"})

    return app