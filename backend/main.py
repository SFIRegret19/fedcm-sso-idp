import os
import time
from typing import Annotated
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse  # <--- Добавили импорт для редиректа
from sqlalchemy.orm import Session
import jwt
import bcrypt
from uuid import uuid4
from dotenv import load_dotenv

from models import Base, User, Token
from schemas import UserCreate, UserLogin
from database import engine, SessionLocal

load_dotenv()

# Если переменная не найдена, используем запасной вариант (только для локальной разработки)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sso_database.db")
JWT_SECRET = os.getenv("JWT_SECRET", "fallback-secret-key-change-me")

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Identity Provider (IdP)")

# Настройка CORS (Разрешаем нашему React-домену)
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
    db.commit()

    response.set_cookie(
        key="sessionId", value=session_token.key,
        httponly=True, secure=True, samesite="none", path="/"
    )
    # Сигнал браузеру для FedCM
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


# --- FEDCM ЭНДПОИНТЫ ---
@app.get("/.well-known/web-identity")
async def web_identity():
    return {"provider_urls":["https://idp.test/fedcm.json"]}

@app.get("/fedcm.json")
async def fedcm_config():
    # Все URL внутри должны быть абсолютными и вести на https://idp.test
    base_url = "https://idp.test"
    return {
        "accounts_endpoint": f"{base_url}/accounts",
        "client_metadata_endpoint": f"{base_url}/client_metadata",
        "id_assertion_endpoint": f"{base_url}/token",
        "login_url": f"{base_url}/login"
    }

@app.get("/login", tags=["FedCM"])
async def login_redirect():
    """
    Мост для FedCM: Браузер открывает этот эндпоинт в попапе, 
    а мы сразу перекидываем его на наш React.
    """
    return RedirectResponse(url="https://rp.test:5173/login")

@app.get("/client_metadata")
async def metadata():
    # Эти ссылки Chrome показывает внизу окна FedCM
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
async def token(account_id: Annotated[str, Form()], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.guid == account_id).first()
    payload = {"sub": user.guid, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    # В дипломном варианте используем наш секрет
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"token": token}