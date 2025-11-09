# database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# 🌍 Load environment variables
load_dotenv()

# 💾 MySQL Database Configuration (from .env)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# ⚙️ Construct SQLAlchemy Connection URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# 🔌 Create SQLAlchemy Engine (connection pool + ping)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# ==========================================
# 🔹 Execute Query (INSERT / UPDATE / DELETE)
# ==========================================
def execute_query(query: str, params: dict = None):
    """Executes INSERT, UPDATE, DELETE queries safely."""
    try:
        with engine.connect() as conn:
            conn.execute(text(query), params or {})
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print("❌ Database Error (execute_query):", e)
        return False


# ==========================================
# 🔹 Fetch Query (SELECT)
# ==========================================
def fetch_query(query: str, params: dict = None):
    """Fetches rows from SELECT queries as a list of dicts."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result]
            return rows
    except SQLAlchemyError as e:
        print("❌ Database Error (fetch_query):", e)
        return []
