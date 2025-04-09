import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis

# ✅ Use environment variable for Redis URI
storage_uri = os.getenv("REDIS_URL")

def get_ip():
    from flask import request
    return request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.remote_addr

# 🔧 OPTIONAL: Create Redis client (only if needed elsewhere in your app)
# If you're just using flask-limiter, this isn't strictly necessary.
redis_client = Redis.from_url(storage_uri)

# 🔒 Configure Limiter with Redis storage
limiter = Limiter(
    key_func=get_ip,
    storage_uri=storage_uri,  # ✅ Use your Upstash Redis URI
)
