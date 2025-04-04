from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_ip():
    from flask import request
    return request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.remote_addr

limiter = Limiter(key_func=get_ip)
