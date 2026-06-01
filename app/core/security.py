import hashlib
import base64
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prehash(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).digest()  
    s = base64.b64encode(digest).decode("ascii")                
    return s[:72]                                               

def hash_password(password: str) -> str:
    return pwd_context.hash(_prehash(password))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(_prehash(plain_password), hashed_password)
    except Exception:
        return False


def verify_password_with_upgrade(plain_password: str, hashed_password: str) -> tuple[bool, bool]:
    if verify_password(plain_password, hashed_password):
        return True, False

    # Older accounts may have been stored before prehashing was added.
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True, True
    except Exception:
        pass

    legacy_sha256 = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    if hashed_password == legacy_sha256:
        return True, True

    return False, False
