# FedCM SSO Identity Provider

Программный прототип сервиса единого входа (Single Sign-On), реализующий функции провайдера идентификации (IdP). Проект разработан с фокусом на современные требования веб-безопасности и отказ браузеров от сторонних файлов cookie (Privacy Sandbox).

Система использует **гибридный подход** для обеспечения бесшовного пользовательского опыта:
1. **FedCM (Federated Credential Management API)** — новейший W3C стандарт для безопасной и приватной авторизации через нативные диалоговые окна браузера (без использования 3rd party cookies).
2. **Classic Redirect Flow (OIDC)** — резервный (fallback) механизм авторизации для браузеров, не поддерживающих FedCM (Safari, Firefox, устаревшие версии).

## Технологический стек

**Backend:**
* [Python 3.13+](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/) — высокопроизводительный асинхронный веб-фреймворк.
* [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — ORM для работы с базой данных.
* **SQLite** — легковесная БД для прототипирования (с возможностью миграции на PostgreSQL).
* **PyJWT, bcrypt** — криптография, хэширование паролей и выпуск JWT-токенов.

**Frontend (Relying Party):**
* Vanilla JavaScript (ES6+), HTML5, CSS3.
* Взаимодействие с `navigator.credentials.get()`.

## Ключевые возможности

* **Управление пользователями:** Регистрация, безопасное хранение паролей (хэширование bcrypt).
* **Управление сессиями:** Генерация HTTP-only, Secure, SameSite=None cookie-файлов.
* **Выдача токенов:** Формирование криптографически подписанных JSON Web Tokens (JWT).
* **API Эндпоинты:**
  * Реализация OIDC-маршрутов (`/login`, `/register`).
  * Полная реализация спецификации FedCM (`/.well-known/web-identity`, `/fedcm.json`, `/accounts`, `/client_metadata`, `/token`).
* **Автодокументация API:** Встроенный Swagger UI.

## Быстрый запуск (Локально)

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/ВАШ_ЛОГИН/fedcm-sso-idp.git
   cd fedcm-sso-idp