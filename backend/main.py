import os, base64, httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, get_user, create_user, update_subscription, get_stats

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUTLINE_API  = os.getenv("OUTLINE_API_URL")
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "./frontend")
BACKEND_URL  = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")
DNS          = os.getenv("WG_DNS", "1.1.1.1")

@app.on_event("startup")
async def startup():
    init_db()

class UserIn(BaseModel):
    telegram_id: int
    username: str = ""
    full_name: str = ""

class PaymentIn(BaseModel):
    telegram_id: int
    stars_amount: int

# ── Serve Mini App ────────────────────────────────────────────────────────────

@app.get("/app", response_class=HTMLResponse)
def mini_app():
    path = os.path.join(FRONTEND_DIR, "app.html")
    html = open(path, encoding="utf-8").read()
    # Inject the backend URL so frontend knows where to call
    html = html.replace("%%BACKEND_URL%%", BACKEND_URL)
    return HTMLResponse(html)

# ── Outline helper ────────────────────────────────────────────────────────────

async def outline_create_key(telegram_id: int) -> str:
    """Creates an Outline access key and returns the ss:// URL."""
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        r = await client.post(f"{OUTLINE_API}/access-keys")
        r.raise_for_status()
        key = r.json()
        # Name the key by telegram_id for easy management
        await client.put(f"{OUTLINE_API}/access-keys/{key['id']}/name",
                         json={"name": f"user_{telegram_id}"})
        return key["accessUrl"]  # ss://xxxx link

# ── API ───────────────────────────────────────────────────────────────────────

@app.post("/user")
async def register(user: UserIn):
    existing = get_user(user.telegram_id)
    if existing:
        return existing

    try:
        access_url = await outline_create_key(user.telegram_id)
    except Exception as e:
        raise HTTPException(500, f"Outline error: {e}")

    from datetime import datetime, timedelta
    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

    create_user(
        telegram_id=user.telegram_id,
        username=user.username,
        full_name=user.full_name,
        access_url=access_url,
        plan="trial",
        expires_at=expires_at,
    )
    return get_user(user.telegram_id)


@app.get("/user/{telegram_id}")
def user_info(telegram_id: int):
    u = get_user(telegram_id)
    if not u:
        raise HTTPException(404, "not found")
    return u


@app.post("/payment/confirm")
def confirm_payment(p: PaymentIn):
    from datetime import datetime, timedelta
    u = get_user(p.telegram_id)
    if not u:
        raise HTTPException(404, "not found")
    months = max(1, p.stars_amount // 150)
    expires_at = (datetime.utcnow() + timedelta(days=30*months)).isoformat()
    update_subscription(p.telegram_id, "paid", expires_at)
    return {"ok": True, "expires_at": expires_at}


@app.get("/admin/stats")
def admin_stats(secret: str = ""):
    if secret != ADMIN_SECRET:
        raise HTTPException(403, "forbidden")
    return get_stats()


@app.get("/health")
def health():
    return {"ok": True}
