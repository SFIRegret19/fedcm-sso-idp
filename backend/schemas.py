from pydantic import BaseModel, EmailStr

# Схема данных, которые мы ждем при регистрации
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# Схема данных, которые мы ждем при входе
class UserLogin(BaseModel):
    email: EmailStr
    password: str