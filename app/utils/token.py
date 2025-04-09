from itsdangerous import URLSafeTimedSerializer
from config import Config

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    return serializer.dumps(email, salt="email-confirmation")

def confirm_verification_token(token, expiration=3600):  # 1 hour expiration
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    try:
        return serializer.loads(token, salt="email-confirmation", max_age=expiration)
    except Exception:
        return None
