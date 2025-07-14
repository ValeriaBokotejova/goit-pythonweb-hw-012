## goit-pythonweb-hw-012

# Contacts API

A **FastAPI**‑powered contact management service featuring:

- ✅ **User authentication** with JWT access & refresh tokens
- 📧 **Email verification** & **password reset** flows
- 📇 **CRUD** operations for contacts, plus search & upcoming birthdays
- 🛡️ **Rate limiting** via Redis
- ⚡ **Async** SQLAlchemy + PostgreSQL + Alembic migrations
- 🧹 **Redis caching** of contact lists
- 🖼️ **Avatar uploads** to Cloudinary
- 🧪 **Unit & integration tests** (pytest & pytest‑asyncio)
- 📄 **Auto‑generated OpenAPI** (Swagger & ReDoc) docs
- 📚 **Sphinx** technical documentation

---

## 🚀 Quickstart

### 1. Clone & configure

```bash
git clone https://github.com/ValeriaBokotejova/goit-pythonweb-hw-012.git
cd your-repo
cp .env.example .env
# Edit .env with your secrets (DATABASE_URL, SECRET_KEY, MAIL_*, CLOUDINARY_*)
```

### 2. Run with Docker Compose

```bash
docker-compose up -d --build
```

- PostgreSQL: localhost:5432
- Redis: localhost:6379
- API: http://localhost:8000

**Apply migrations:**

```bash
docker-compose exec web alembic upgrade head
```

### 3. Run locally without Docker

```bash
python -m venv .venv
# Activate:
#   source .venv/bin/activate    (Linux/macOS)
#   .venv\Scripts\activate       (Windows)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
### 🔧 Usage & Testing

- Swagger UI: GET /docs
- ReDoc: GET /redoc
- Sphinx HTML: mount under /docs-html (already configured)

```bash
# Run all tests with coverage
pytest --cov

# Lint & format
pre-commit run --all-files
flake8
black .
isort .
```
### 🛠️ Common Commands

| Action               | Command                                                         |
| -------------------- | --------------------------------------------------------------- |
| Install dependencies | `pip install -r requirements.txt`                               |
| Run migrations       | `alembic upgrade head`                                          |
| Start server (dev)   | `uvicorn app.main:app --reload`                                 |
| Docker Compose up    | `docker-compose up --build`                                     |
| Run tests            | `pytest --cov`                                                  |
| Lint & format        | `pre-commit run --all-files` / `flake8` / `black .` / `isort .` |
| Build Sphinx docs    | `sphinx-build -b html docs/source docs/build/html`              |
