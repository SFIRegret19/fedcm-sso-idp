from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    guid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    login: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    admin_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)

class Client(Base):
    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(String, primary_key=True)
    client_name: Mapped[str] = mapped_column(String)
    redirect_uri: Mapped[str] = mapped_column(String)

class Token(Base):
    __tablename__ = "tokens"

    key: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_guid: Mapped[str] = mapped_column(ForeignKey("users.guid"))
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.client_id"), nullable=True)
    type: Mapped[str] = mapped_column(String)  # 'access', 'auth', 'user'
    ts: Mapped[int] = mapped_column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    data: Mapped[dict] = mapped_column(JSON, default=dict)