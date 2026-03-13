import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import enviroment_variables

envs = enviroment_variables()

ALGORITHM = "HS256"

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)

    payload.update({"exp": expire})

    return jwt.encode(payload, envs.SECRET, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, envs.SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None