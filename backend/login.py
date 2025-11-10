# login.py
from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import fetch_query
import os

router = APIRouter()

# ==========================================
# 🔹 Security Configuration
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # fallback
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# ==========================================
# 🔹 Utility Functions
# ==========================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================================
# 🔹 Municipal List Endpoint
# ==========================================
@router.get("/municipal-list")
def get_municipal_list():
    query = "SELECT MC_Code, MC_Name FROM municipal_data ORDER BY MC_Name ASC"
    result = fetch_query(query)
    if not result:
        raise HTTPException(status_code=404, detail="No municipal data found.")
    return {
        "Total_Municipals": len(result),
        "Municipals": result
    }

# ==========================================
# 🔹 Secure Login Endpoint (JWT Auth)
# ==========================================
@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    mc_code: str = Form(...)
):
    query = """
        SELECT u.Username, u.Password, m.MC_Name 
        FROM mc_users u
        JOIN municipal_data m ON u.MC_Code = m.MC_Code
        WHERE u.Username = :username AND u.MC_Code = :mc_code
    """
    result = fetch_query(query, {"username": username, "mc_code": mc_code})

    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or municipal code.")

    user = result[0]

    # 🔐 Password verification
    if not verify_password(password, user["Password"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # 🎟️ Generate JWT token
    token_data = {
        "sub": username,
        "mc_code": mc_code,
        "mc_name": user["MC_Name"],
    }
    access_token = create_access_token(data=token_data)

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "mc_code": mc_code,
        "mc_name": user["MC_Name"],
        "redirect_url": f"/api/dashboard/{mc_code}",
        "message": f"Welcome {user['MC_Name']} Municipal Corporation!"
    }

# ==========================================
# 🔹 Verify Token (for internal endpoints)
# ==========================================
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        mc_code: str = payload.get("mc_code")
        if username is None or mc_code is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
        return {"username": username, "mc_code": mc_code}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
