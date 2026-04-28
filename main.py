from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import jwt
import bcrypt
import uuid
import time

from models import Base, User, Token
from schemas import UserCreate, UserLogin

# Настройка БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./sso_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FedCM SSO Identity Provider", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Функция-зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Криптография) ---
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- ЭНДПОИНТЫ КЛАССИЧЕСКОГО OIDC ---

@app.post("/register", tags=["Classic SSO"])
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, нет ли уже такого email
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    # Создаем пользователя
    new_user = User(
        login=user_data.email.split("@")[0], # Генерируем логин из email
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        profile={"name": user_data.name}
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "message": "Пользователь успешно зарегистрирован"}

@app.post("/login", tags=["Classic SSO"])
def login_user(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    # Ищем пользователя
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Создаем сессионный токен в БД
    session_token = Token(
        user_guid=user.guid,
        type="user_token",
        ts=int(time.time())
    )
    db.add(session_token)
    db.commit()

    # Устанавливаем Cookie (SameSite="none" и Secure=True нужны для FedCM)
    response.set_cookie(
        key="sessionId",
        value=session_token.key,
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )
    return {"status": "success", "message": "Вы успешно вошли в систему"}

@app.get("/session-check", tags=["Classic SSO"])
def check_session(request: Request, db: Session = Depends(get_db)):
    """Эндпоинт для клиента: проверять, залогинен ли юзер"""
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return {"status": "logged-out"}
    
    token = db.query(Token).filter(Token.key == session_id, Token.type == "user_token").first()
    if token:
        return {"status": "logged-in"}
    return {"status": "logged-out"}

# --- ЭНДПОИНТЫ FEDCM API ---

@app.get("/.well-known/web-identity", tags=["FedCM"])
def get_web_identity():
    return {"provider_urls": ["/fedcm.json"]}

@app.get("/fedcm.json", tags=["FedCM"])
def get_fedcm_config(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return {
        "accounts_endpoint": f"{base_url}/accounts",
        "client_metadata_endpoint": f"{base_url}/client_metadata",
        "id_assertion_endpoint": f"{base_url}/token",
        "login_url": f"{base_url}/login"
    }

@app.get("/accounts", tags=["FedCM"])
def get_accounts(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = request.cookies.get("sessionId")
    if not session_id:
        response.headers["Set-Login"] = "logged-out"
        return {"accounts":[]}
    
    # Ищем сессию и пользователя
    token = db.query(Token).filter(Token.key == session_id).first()
    if not token:
        response.headers["Set-Login"] = "logged-out"
        return {"accounts":[]}
        
    user = db.query(User).filter(User.guid == token.user_guid).first()
    if not user:
        response.headers["Set-Login"] = "logged-out"
        return {"accounts":[]}

    # FedCM требует этот заголовок для подтверждения сессии
    response.headers["Set-Login"] = "logged-in"
    
    # Возвращаем данные аккаунта в формате FedCM
    return {
        "accounts":[{
            "id": user.guid,
            "name": user.profile.get("name", "Пользователь"),
            "email": user.email,
            "picture": "https://www.gravatar.com/avatar/?d=mp", # Стандартная аватарка
            "approved_clients": ["client1234"]
        }]
    }

@app.get("/client_metadata", tags=["FedCM"])
def get_client_metadata(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return {
        "privacy_policy_url": f"{base_url}/privacy",
        "terms_of_service_url": f"{base_url}/terms"
    }

@app.post("/token", tags=["FedCM"])
def issue_token(request: Request, account_id: str = Form(None), db: Session = Depends(get_db)):
    """Финальный этап: выдача JWT токена браузеру"""
    # Если запрос пришел от FedCM, ID пользователя будет в account_id
    if not account_id:
        raise HTTPException(status_code=400, detail="Missing account_id")
        
    user = db.query(User).filter(User.guid == account_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    base_url = str(request.base_url).rstrip("/")
    
    # Генерируем JWT токен
    payload = {
        "iss": base_url, # Кто выдал (наш IdP)
        "sub": user.guid, # Кому выдан (ID юзера)
        "email": user.email,
        "name": user.profile.get("name", ""),
        "exp": int(time.time()) + 3600 # Срок жизни токена (1 час)
    }
    
    # JWT_SECRET определен в начале файла
    token = jwt.encode(payload, "my-super-secret-for-prototype-only", algorithm="HS256")
    
    return {"token": token}