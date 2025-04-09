import os
from dotenv import load_dotenv
import redis

# Load the .env file
load_dotenv()

# Test Redis connection
redis_url = os.getenv("REDIS_URL")

if redis_url is None:
    print("REDIS_URL is not set in the environment variables.")
else:
    redis_client = redis.Redis.from_url(redis_url)

    # Check Redis connection by setting and getting a test value
    try:
        redis_client.set('test_key', '1')
        print(f"Redis connection test: {redis_client.get('test_key')}")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
