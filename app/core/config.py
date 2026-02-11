import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    value = value.strip()
    if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
        return int(value)

    raise ValueError(f"Invalid integer for {name}: {value!r}")


class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = _get_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 7)


settings = Settings()

