from pydantic import BaseModel, EmailStr

# Схема данных, которые ждем при регистрации
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# Схема данных, которые ждем при входе
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схема данных, которые ждем при обновлении профиля
class UserUpdate(BaseModel):
    name: str
    email: EmailStr

# Схема данных, которые ждем при изменении пароля
class PasswordChange(BaseModel):
    old_password: str
    new_password: str