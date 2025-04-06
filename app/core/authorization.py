from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from app.core.logger import logger

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
            except Exception:
                logger.warning(f"🔒 Missing or invalid JWT for: {request.method} {request.path}")
                return {"detail": "Missing or invalid token"}, 401

            if claims.get("role") not in roles:
                logger.warning(f"⛔ Forbidden: {claims.get('role')} tried to access {request.method} {request.path}")
                return {"detail": "Forbidden: insufficient role"}, 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
