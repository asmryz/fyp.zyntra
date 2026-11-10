# ZYNTRA

Agentic AI-powered admission assistance system for SZABIST (Final Year Project).

- `backend/` – FastAPI + SQLAlchemy + PostgreSQL (Neon), Alembic migrations
- `frontend/` – React (Vite), React Router, React Three Fiber

ZYNTRA provides guidance only. It does not make admission decisions, accept applications or take payments.

## Run on Windows (VS Code terminal, PowerShell)

### Backend

```powershell
cd D:\FYP\ZYNTRA\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend (second terminal)

```powershell
cd D:\FYP\ZYNTRA\frontend
npm install
npm run dev
```

Website: http://localhost:5173 (requests to `/api` are proxied to the backend).

### Create the root admin (once)

```powershell
cd D:\FYP\ZYNTRA\backend
.\venv\Scripts\Activate.ps1
python create_root_admin.py
```

Then log in at http://localhost:5173/login.

### Placeholder content

```powershell
python seed_placeholders.py            # add labelled sample content
python seed_placeholders.py --remove   # delete placeholders that were not edited
```

### Tests

```powershell
cd D:\FYP\ZYNTRA\backend
.\venv\Scripts\Activate.ps1
python tests\run_api_tests.py
```

The test script starts its own backend on port 8765 with emails saved to `backend/dev_outbox/` instead of being sent, runs against the Neon database, and deletes everything it creates.

## Roles

| Role | How the account is created | Area |
|---|---|---|
| Root admin | `python create_root_admin.py` | `/root` |
| Staff | Invitation from the root admin | `/staff` |
| Student | Public registration + email code | `/student` |

Staff permissions are set per content module: **Read** (view all), **Write** (create, and edit/delete own records), **Read + Write** (view and edit all). They are enforced in `backend/app/core/permissions.py`.

## Environment

Copy `backend/.env.example` to `backend/.env` and fill in real values. Never commit `.env`.
