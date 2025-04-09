from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis

def get_ip():
    from flask import request
    return request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.remote_addr

# 🔧 Create Redis client
redis_client = Redis(host="redis", port=6379)

# 🔒 Configure Limiter with Redis storage
limiter = Limiter(
    key_func=get_ip,
    storage_uri="redis://redis:6379",  
)
