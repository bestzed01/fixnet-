import sqlite3, os

DB = os.getenv("DB_PATH", "fixnet.db")

def cx():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    db = cx()
    db.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT DEFAULT '',
        full_name TEXT DEFAULT '',
        access_url TEXT NOT NULL,
        plan TEXT DEFAULT 'trial',
        expires_at TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    db.commit(); db.close()

def create_user(telegram_id, username, full_name, access_url, plan, expires_at):
    db = cx()
    db.execute("INSERT INTO users(telegram_id,username,full_name,access_url,plan,expires_at) VALUES(?,?,?,?,?,?)",
               (telegram_id,username,full_name,access_url,plan,expires_at))
    db.commit(); db.close()

def get_user(telegram_id):
    db = cx()
    r = db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    db.close()
    return dict(r) if r else None

def update_subscription(telegram_id, plan, expires_at):
    db = cx()
    db.execute("UPDATE users SET plan=?,expires_at=? WHERE telegram_id=?", (plan,expires_at,telegram_id))
    db.commit(); db.close()

def get_stats():
    db = cx()
    total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    paid  = db.execute("SELECT COUNT(*) FROM users WHERE plan='paid'").fetchone()[0]
    db.close()
    return {"total": total, "paid": paid, "trial": total-paid}
