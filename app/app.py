import os
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from datetime import timedelta, datetime
from flasgger import Swagger
from app.core.auth import authenticate_user, create_access_token
from app.utils.user import verify_password
from app.database.base import get_db
from app.database.models import User
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import update
from app.services.email.utils import send_email_async
from app.config import Config

# Import Blueprints (Routes)
from app.routes.invoice_routes import invoice_bp
from app.routes.transactions import transactions_bp
from app.routes.users import users_bp
from app.routes.accounts import accounts_bp
from app.routes.billpayment import billpayment_bp
from app.routes.external_transaction import external_transaction_bp

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app)

# Swagger Security Definition for Bearer Authentication
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "RevouBank API",
        "description": "API documentation for RevouBank",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter: **Bearer &lt;your_token&gt;**"
        }
    },
    "security": [{"Bearer": []}]  # Apply Bearer security globally
}

swagger = Swagger(app, template=swagger_template)

@app.route('/swagger-inject.js')
def swagger_custom_js():
    return """window.onload = function() {
        setTimeout(() => {
            if (window.ui) {
                window.ui.getConfigs().requestInterceptor = function(req) {
                    req.headers['Content-Type'] = 'application/json';
                    return req;
                };
            }
        }, 1000);
    };""", 200, {'Content-Type': 'application/javascript'}

@app.route('/apidocs/')
def custom_swagger_ui():
    return redirect('/apidocs/?configUrl=/apispec_1.json&customJs=/swagger-inject.js')

# Security Config
LOCK_DURATION = timedelta(minutes=15)
MAX_FAILED_ATTEMPTS = 5

# Register Blueprints (Routes)
app.register_blueprint(invoice_bp, url_prefix='/api/invoices')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
app.register_blueprint(billpayment_bp, url_prefix='/api/billpayment')
app.register_blueprint(external_transaction_bp, url_prefix='/api/external')

@app.route("/")
def home():
    """
    Welcome endpoint
    ---
    responses:
      200:
        description: API is running successfully
    """
    return jsonify({"message": "Welcome to RevouBank API"})

@app.route("/docs")
def docs_redirect():
    """ Redirects to Swagger UI """
    return redirect(request.host_url + "apidocs")


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
        if user.locked_time and datetime.utcnow() > user.locked_time + LOCK_DURATION:
            user.is_locked = False
            user.failed_attempts = 0
            db.commit()
        else:
            return jsonify({"detail": "Account is locked due to multiple failed login attempts. Please try again later."}), 403

    if not verify_password(password, user.password):
        user.failed_attempts += 1

        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
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

        attempts_left = MAX_FAILED_ATTEMPTS - user.failed_attempts
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

# Run the Flask app
if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print("\n✅ Flask app is running on http://127.0.0.1:5000")
    print("📜 Swagger Docs: http://127.0.0.1:5000/apidocs\n")
    port = int(os.getenv("PORT", 5000))  # Default to port 5000 if not specified
    app.run(host="0.0.0.0", port=port, debug=debug_mode)


