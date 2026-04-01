from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use an absolute path for SQLite to ensure it works in production environments
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'url_shortener.db')}"

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Fix for Render/Heroku PostgreSQL URLs: SQLAlchemy requires 'postgresql://' instead of 'postgres://'
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
# For some Render configurations, an empty host or database name might prevent proper parsing if not explicit
# This line ensures explicit schema: //user:pass@host:port/dbname
elif SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    # Ensure any query parameters like ?sslmode=disable are handled correctly
    if '?' not in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL += '?sslmode=require' # Render often requires SSL, add if not present

# SQLite requires check_same_thread: False, but Postgres will error if it's included
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
