from app.__init__ import create_app
from config import Config
from flask import request, jsonify, redirect
from flasgger import Swagger

app = create_app()

# ✅ Register Swagger immediately (this is the key!)
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
    "security": [{"Bearer": []}]
}

Swagger(app, template=swagger_template)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to RevouBank API"})

@app.route("/docs")
def docs_redirect():
    return redirect("/apidocs")

@app.route("/swagger-inject.js")
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

@app.route("/apidocs/")
def custom_swagger_ui():
    return redirect('/apidocs/?configUrl=/apispec_1.json&customJs=/swagger-inject.js')

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print("\n✅ Flask app is running on http://127.0.0.1:5000")
    print("📜 Swagger Docs: http://127.0.0.1:5000/apidocs\n")
    app.run(host="0.0.0.0", port=port, debug=debug_mode, threaded=False)
