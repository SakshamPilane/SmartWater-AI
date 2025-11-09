# login.py
from fastapi import APIRouter, Form, HTTPException
from database import fetch_query

router = APIRouter()  # remove prefix

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
        WHERE u.Username = :username AND u.Password = :password AND u.MC_Code = :mc_code
    """
    result = fetch_query(query, {"username": username, "password": password, "mc_code": mc_code})
    if result:
        return {
            "status": "success",
            "mc_code": mc_code,
            "mc_name": result[0]["MC_Name"],
            "redirect_url": f"/api/dashboard/{mc_code}",
            "message": f"Welcome {result[0]['MC_Name']} Municipal Corporation!"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid username, password, or corporation.")
