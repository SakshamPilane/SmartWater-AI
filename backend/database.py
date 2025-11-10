# database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# 🌍 Load environment variables
load_dotenv()

# ==========================================
# 🔹 MySQL Database Configuration
# ==========================================
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "water_project")

# ✅ Construct SQLAlchemy Connection URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# ✅ Create Engine with automatic connection test (ping)
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"✅ Database engine initialized for '{DB_NAME}' at {DB_HOST}")
except Exception as e:
    print(f"❌ Failed to initialize database engine: {e}")
    engine = None


# ==========================================
# 🔹 Execute Query (INSERT / UPDATE / DELETE)
# ==========================================
def execute_query(query: str, params: dict = None) -> bool:
    """
    Executes INSERT, UPDATE, or DELETE queries safely.
    Returns True if successful, False otherwise.
    """
    if not engine:
        print("⚠️ Database engine is not initialized.")
        return False
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
    """
    Executes SELECT queries and returns results as a list of dictionaries.
    Returns an empty list if query fails or no records found.
    """
    if not engine:
        print("⚠️ Database engine is not initialized.")
        return []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result]
            return rows
    except SQLAlchemyError as e:
        print("❌ Database Error (fetch_query):", e)
        return []


# ==========================================
# 🔹 Health Check Utility (Optional)
# ==========================================
def test_connection():
    """Tests if the database connection works."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT NOW() AS current_time")).fetchone()
            print("✅ Database connection OK:", result["current_time"])
            return True
    except Exception as e:
        print("❌ Database connection failed:", e)
        return False


# Run quick test when this file is executed directly
if __name__ == "__main__":
    print("🔍 Testing database connection...")
    test_connection()
