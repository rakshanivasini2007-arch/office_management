from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import JWTError

import models
from database import engine, SessionLocal

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# JWT CONFIG
SECRET_KEY = "office_secret_123"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =========================
# JWT FUNCTIONS
# =========================

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        return None


# =========================
# HOME PAGE
# =========================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# =========================
# LOGIN (JWT GENERATION)
# =========================
@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):


    # SIMPLE LOGIN CHECK
    if username == "raksha" and password == "1234":

        token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=30)
        )

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "username": username,
                "token": token,
                "checkin": "",
                "checkout": ""
            }
        )

    return HTMLResponse("<h1>Invalid Username or Password</h1>")


# =========================
# CHECK CURRENT USER FROM TOKEN
# =========================
def get_current_user(token: str):
    user = verify_token(token)
    return user


# =========================
# CHECKIN (PROTECTED)
# =========================
@app.post("/checkin", response_class=HTMLResponse)
def checkin(
    request: Request,
    token: str = Form(...)
):

    username = get_current_user(token)

    if not username:
        return HTMLResponse("<h1>Unauthorized</h1>")

    db = SessionLocal()

    current_time = datetime.now().strftime("%I:%M %p")

    new_employee = models.Employee(
        name=username,
        login_time=current_time,
        logout_time=""
    )

    db.add(new_employee)
    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "username": username,
            "token": token,
            "checkin": current_time,
            "checkout": ""
        }
    )


# =========================
# CHECKOUT (PROTECTED)
# =========================
@app.post("/checkout", response_class=HTMLResponse)
def checkout(
    request: Request,
    token: str = Form(...)
):

    username = get_current_user(token)

    if not username:
        return HTMLResponse("<h1>Unauthorized</h1>")

    db = SessionLocal()

    employee = db.query(models.Employee).filter(
        models.Employee.name == username,
        models.Employee.logout_time == ""
    ).first()

    current_time = datetime.now().strftime("%I:%M %p")

    if employee:
        employee.logout_time = current_time
        db.commit()

        login_time = employee.login_time
    else:
        login_time = ""

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "username": username,
            "token": token,
            "checkin": login_time,
            "checkout": current_time
        }
    )