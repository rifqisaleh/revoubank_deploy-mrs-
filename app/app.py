import os
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from datetime import timedelta, datetime
from flasgger import Swagger
from app.core.auth import authenticate_user, create_access_token
from app.utils.user import verify_password
from app.database.mock_database import get_mock_db
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
    return redirect("/apidocs")

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
    form_data = request.form
    username = form_data.get("username")
    password = form_data.get("password")

    user = next((user for user in get_mock_db()["users"].values() if user["username"] == username), None)
    if not user:
        return jsonify({"detail": "Incorrect username or password."}), 400

    if user["is_locked"]:
        locked_time = user.get("locked_time")
        if locked_time and datetime.utcnow() > locked_time + LOCK_DURATION:
            user["is_locked"] = False
            user["failed_attempts"] = 5  # Reset failed attempts after lock period expires
        else:
            return jsonify({"detail": "Account is locked due to multiple failed login attempts. Please try again later."}), 403

    if not verify_password(password, user["password"]):
        user["failed_attempts"] += 1

        if user["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
            user["is_locked"] = True
            user["locked_time"] = datetime.utcnow()

            # 🔹 Send Email Notification on Lock
            email_subject = "Your RevouBank Account is Locked"
            email_body = (
                f"Dear {username},\n\n"
                "Your RevouBank account has been locked due to multiple failed login attempts.\n"
                "Please wait 15 minutes before trying again or contact support if you need assistance.\n\n"
                "Best regards,\nRevouBank Support"
            )
            send_email_async(user["email"], email_subject, email_body)  # Send the email

            print(f"📧 Lock notification sent to {user['email']}")  # Debugging

            return jsonify({"detail": "Account locked due to multiple failed attempts. Please wait 15 minutes."}), 403
        
        attempts_left = MAX_FAILED_ATTEMPTS - user["failed_attempts"]
        return jsonify({"detail": f"Incorrect password. Attempts left: {attempts_left}"}), 400

    # Reset login attempts after successful login
    user["failed_attempts"] = 0
    user["is_locked"] = False
    user["locked_time"] = None

    # Create JWT token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)

    return jsonify({"access_token": access_token, "token_type": "bearer"})


# Run the Flask app
if __name__ == '__main__':
    print("\n✅ Flask app is running on http://127.0.0.1:5000")
    print("📜 Swagger Docs: http://127.0.0.1:5000/apidocs\n")
    app.run(debug=True)
