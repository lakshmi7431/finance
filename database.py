import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "finance_dashboard")

# PyMySQL driver — pure Python, no C extensions needed
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Lakshmi123%40@localhost:3306/finance_dashboard"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,   # auto-reconnect if connection dropped
    pool_recycle=3600,    # recycle connections every hour
    echo=False            # set True to log all SQL to console
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection():
    """Verify DB is reachable — called at startup."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Connected to MySQL '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        raise