import os
import time
from typing import Annotated
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import jwt
import bcrypt
from uuid import uuid4
from dotenv import load_dotenv

from models import Base, User, Token
from schemas import UserCreate, UserLogin, UserUpdate, PasswordChange
from database import engine, SessionLocal

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sso_database.db")
JWT_SECRET = os.getenv("JWT_SECRET", "fallback-secret-key-change-me")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Identity Provider (IdP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rp.test:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# --- КРИПТОГРАФИЯ ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- API ЭНДПОИНТЫ ---
@app.post("/api/register")
async def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email уже занят")
    new_user = User(
        login=data.email,
        email=data.email,
        password_hash=hash_password(data.password),
        profile={"name": data.name}
    )
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/api/login")
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверные данные")
    
    session_token = Token(user_guid=user.guid, type="user_token", ts=int(time.time()))
    db.add(session_token)
    
    refresh_token = Token(user_guid=user.guid, type="refresh_token", ts=int(time.time()))
    db.add(refresh_token)
    
    db.commit()

    response.set_cookie(
        key="sessionId", value=session_token.key,
        httponly=True, secure=True, samesite="none", path="/"
    )
    
    response.set_cookie(
        key="refreshToken", value=refresh_token.key,
        httponly=True, secure=True, samesite="none", path="/api/refresh"
    )
    
    response.headers["Set-Login"] = "logged-in"
    return {"status": "success", "user": {"name": user.profile.get("name")}}

@app.get("/api/session-check")
async def check(request: Request, db: Session = Depends(get_db)):
    sid = request.cookies.get("sessionId")
    t = db.query(Token).filter(Token.key == sid).first() if sid else None
    if t:
        user = db.query(User).filter(User.guid == t.user_guid).first()
        return {"status": "logged-in", "user": {"name": user.profile.get("name")}}
    return {"status": "logged-out"}

@app.get("/api/get-redirect-token", tags=["Classic SSO"])
async def get_redirect_token(request: Request, db: Session = Depends(get_db)):
    sid = request.cookies.get("sessionId")
    if not sid:
        raise HTTPException(status_code=401, detail="Не авторизован")
        
    token_record = db.query(Token).filter(Token.key == sid).first()
    if not token_record:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
        
    user = db.query(User).filter(User.guid == token_record.user_guid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    base_url = str(request.base_url).rstrip("/")
    payload = {
        "sub": user.guid,
        "email": user.email,
        "name": user.profile.get("name", ""),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return {"token": jwt_token}

# --- Вспомогательная функция проверки авторизации ---
def get_current_user(request: Request, db: Session = Depends(get_db)):
    sid = request.cookies.get("sessionId")
    if not sid:
        raise HTTPException(status_code=401, detail="Не авторизован")
    token = db.query(Token).filter(Token.key == sid).first()
    if not token:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    user = db.query(User).filter(User.guid == token.user_guid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@app.get("/api/profile", tags=["User Profile"])
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.profile.get("name", "")
    }

@app.put("/api/profile", tags=["User Profile"])
async def update_profile(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Этот Email уже занят другим пользователем")
        current_user.email = data.email
        current_user.login = data.email

    profile_data = dict(current_user.profile)
    profile_data["name"] = data.name
    current_user.profile = profile_data
    
    db.commit()
    return {"status": "success", "message": "Профиль обновлен"}

@app.post("/api/change-password", tags=["User Profile"])
async def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный старый пароль")
    
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"status": "success", "message": "Пароль успешно изменен"}

@app.post("/api/refresh", tags=["Classic SSO"])
async def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    old_refresh_key = request.cookies.get("refreshToken")
    if not old_refresh_key:
        raise HTTPException(status_code=401, detail="Refresh token отсутствует")
        
    token_record = db.query(Token).filter(Token.key == old_refresh_key, Token.type == "refresh_token").first()
    if not token_record:
        raise HTTPException(status_code=401, detail="Недействительный refresh token")
        
    user = db.query(User).filter(User.guid == token_record.user_guid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    db.delete(token_record)
    
    new_refresh_token = Token(user_guid=user.guid, type="refresh_token", ts=int(time.time()))
    db.add(new_refresh_token)
    db.commit()
    
    payload = {
        "sub": user.guid,
        "email": user.email,
        "name": user.profile.get("name", ""),
        "iat": int(time.time()),
        "exp": int(time.time()) + 900
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    response.set_cookie(
        key="refreshToken", value=new_refresh_token.key,
        httponly=True, secure=True, samesite="none", path="/api/refresh"
    )
    
    return {"token": jwt_token}

# --- FEDCM ЭНДПОИНТЫ ---
@app.get("/.well-known/web-identity")
async def web_identity():
    return {"provider_urls":["https://idp.test/fedcm.json"]}

@app.get("/fedcm.json")
async def fedcm_config():
    base_url = "https://idp.test"
    return {
        "accounts_endpoint": f"{base_url}/accounts",
        "client_metadata_endpoint": f"{base_url}/client_metadata",
        "id_assertion_endpoint": f"{base_url}/token",
        "login_url": f"{base_url}/login"
    }

@app.get("/login", tags=["FedCM"])
async def login_redirect():
    return RedirectResponse(url="https://rp.test:5173/login")

@app.get("/client_metadata")
async def metadata():
    return {
        "privacy_policy_url": "https://rp.test:5173/privacy",
        "terms_of_service_url": "https://rp.test:5173/terms"
    }

@app.get("/accounts")
async def accounts(request: Request, response: Response, db: Session = Depends(get_db)):
    sid = request.cookies.get("sessionId")
    t = db.query(Token).filter(Token.key == sid).first() if sid else None
    if not t:
        response.headers["Set-Login"] = "logged-out"
        return {"accounts":[]}
    user = db.query(User).filter(User.guid == t.user_guid).first()
    response.headers["Set-Login"] = "logged-in"
    return {"accounts":[{
        "id": user.guid, "name": user.profile.get("name"), "email": user.email,
        "picture": "https://www.gravatar.com/avatar/?d=mp",
        "approved_clients": ["client1234"]
    }]}

@app.post("/token")
async def token(request: Request, account_id: Annotated[str, Form()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.guid == account_id).first()
    if not user: raise HTTPException(404)
    
    base_url = str(request.base_url).rstrip("/")
    payload = {
        "iss": base_url,
        "sub": user.guid,
        "email": user.email,
        "name": user.profile.get("name", ""),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token}

@app.get("/mark-login", tags=["FedCM System"])

async def mark_login(redirect_url: str):
    response = RedirectResponse(url=redirect_url)
    response.headers["Set-Login"] = "logged-in"
    return response