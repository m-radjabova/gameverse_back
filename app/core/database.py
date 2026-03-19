import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()


def get_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value is not None else None


def get_database_url() -> str:
    database_url = get_env("DATABASE_URL")
    if database_url:
        return database_url

    required_env_vars = ["DB_USER", "DB_PASS", "DB_HOST", "DB_PORT", "DB_NAME"]
    env_values = {name: get_env(name) for name in required_env_vars}
    missing_env_vars = [name for name, value in env_values.items() if not value]
    if missing_env_vars:
        missing = ", ".join(missing_env_vars)
        raise ValueError(
            f"Database configuration is incomplete. Set DATABASE_URL or these env vars: {missing}"
        )

    return (
        f"postgresql://{env_values['DB_USER']}:{env_values['DB_PASS']}"
        f"@{env_values['DB_HOST']}:{env_values['DB_PORT']}/{env_values['DB_NAME']}"
    )


SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
