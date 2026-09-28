from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import os
import csv
import io
import secrets
from datetime import datetime

app = FastAPI(title="Watch Tower Alarm Tracker")

# ─── Security ──────────────────────────────────────────────────────────────────
APP_USERNAME = "watchtower"
APP_PASSWORD = "wt-secure-2024"

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, APP_USERNAME)
    correct_pass = secrets.compare_digest(credentials.password, APP_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401, detail="Access denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ─── Database ──────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(__file__)
DATABASE_URL = os.environ.get("DATABASE_URL")          # Set on Render → PostgreSQL
STATIC_DIR   = BASE_DIR
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras

    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def rows_to_dicts(cur):
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def row_to_dict(cur):
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    PH = "%s"   # PostgreSQL placeholder

else:
    import sqlite3

    def get_db():
        conn = sqlite3.connect(os.environ.get("DB_PATH", os.path.join(BASE_DIR, "watchtower.db")))
        conn.row_factory = sqlite3.Row
        return conn

    def rows_to_dicts(cur):
        return [dict(r) for r in cur.fetchall()]

    def row_to_dict(cur):
        row = cur.fetchone()
        return dict(row) if row else None

    PH = "?"    # SQLite placeholder


def q(sql):
    """Replace ? with the correct placeholder for the active database."""
    return sql.replace("?", PH)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    if USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS facilities (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                contact_name TEXT,
                contact_phone TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                facility_id INTEGER REFERENCES facilities(id),
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                connection_established_time TEXT,
                event_type TEXT NOT NULL,
                operator TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Open',
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                contact_name TEXT,
                contact_phone TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                connection_established_time TEXT,
                event_type TEXT NOT NULL,
                operator TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Open',
                resolution_notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            )
        """)
    # Migrate: add new contact/response columns if they don't exist yet
    new_cols = [
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS contacted_name TEXT",
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS contact_phone TEXT",
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS contact_attempts INTEGER",
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS time_first_contact TEXT",
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS police_dispatched TEXT DEFAULT 'No'",
    ] if USE_PG else [
        "ALTER TABLE events ADD COLUMN contacted_name TEXT",
        "ALTER TABLE events ADD COLUMN contact_phone TEXT",
        "ALTER TABLE events ADD COLUMN contact_attempts INTEGER",
        "ALTER TABLE events ADD COLUMN time_first_contact TEXT",
        "ALTER TABLE events ADD COLUMN police_dispatched TEXT DEFAULT 'No'",
    ]
    for col_sql in new_cols:
        try:
            cur.execute(col_sql)
        except Exception:
            pass
    conn.commit()
    conn.close()

init_db()

# ─── Models ────────────────────────────────────────────────────────────────────
class FacilityCreate(BaseModel):
    name: str
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    notes: Optional[str] = None

class EventCreate(BaseModel):
    facility_id: Optional[int] = None
    event_date: str
    event_time: str
    connection_established_time: Optional[str] = None
    event_type: str
    operator: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "Open"
    resolution_notes: Optional[str] = None
    contacted_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_attempts: Optional[int] = None
    time_first_contact: Optional[str] = None
    police_dispatched: Optional[str] = "No"

class EventUpdate(BaseModel):
    facility_id: Optional[int] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    connection_established_time: Optional[str] = None
    event_type: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    contacted_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_attempts: Optional[int] = None
    time_first_contact: Optional[str] = None
    police_dispatched: Optional[str] = None

# ─── Facility Routes ───────────────────────────────────────────────────────────
@app.get("/api/facilities")
def list_facilities(user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM facilities ORDER BY name ASC")
    result = rows_to_dicts(cur)
    conn.close()
    return result

@app.post("/api/facilities", status_code=201)
def create_facility(facility: FacilityCreate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    if USE_PG:
        cur.execute(q(
            "INSERT INTO facilities (name, address, contact_name, contact_phone, notes) "
            "VALUES (?,?,?,?,?) RETURNING id"
        ), (facility.name, facility.address, facility.contact_name, facility.contact_phone, facility.notes))
        new_id = cur.fetchone()[0]
    else:
        cur.execute(q(
            "INSERT INTO facilities (name, address, contact_name, contact_phone, notes) VALUES (?,?,?,?,?)"
        ), (facility.name, facility.address, facility.contact_name, facility.contact_phone, facility.notes))
        new_id = cur.lastrowid
    conn.commit()
    cur.execute(q("SELECT * FROM facilities WHERE id=?"), (new_id,))
    result = row_to_dict(cur)
    conn.close()
    return result

@app.put("/api/facilities/{facility_id}")
def update_facility(facility_id: int, facility: FacilityUpdate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(q("SELECT * FROM facilities WHERE id=?"), (facility_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Facility not found")
    fields = {k: v for k, v in facility.dict().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}={PH}" for k in fields)
        cur.execute(f"UPDATE facilities SET {sets} WHERE id={PH}", (*fields.values(), facility_id))
        conn.commit()
    cur.execute(q("SELECT * FROM facilities WHERE id=?"), (facility_id,))
    result = row_to_dict(cur)
    conn.close()
    return result

@app.delete("/api/facilities/{facility_id}")
def delete_facility(facility_id: int, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(q("DELETE FROM facilities WHERE id=?"), (facility_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Event Routes ──────────────────────────────────────────────────────────────
@app.get("/api/events")
def list_events(
    facility_id: Optional[int] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    user: str = Depends(authenticate),
):
    conn = get_db()
    cur = conn.cursor()
    sql = """
        SELECT e.*, f.name as facility_name
        FROM events e LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE 1=1
    """
    params = []
    if facility_id: sql += f" AND e.facility_id={PH}"; params.append(facility_id)
    if event_type:  sql += f" AND e.event_type={PH}";  params.append(event_type)
    if status:      sql += f" AND e.status={PH}";      params.append(status)
    if date_from:   sql += f" AND e.event_date>={PH}"; params.append(date_from)
    if date_to:     sql += f" AND e.event_date<={PH}"; params.append(date_to)
    sql += f" ORDER BY e.event_date DESC, e.event_time DESC LIMIT {PH} OFFSET {PH}"
    params += [limit, offset]
    cur.execute(sql, params)
    result = rows_to_dicts(cur)
    conn.close()
    return result

@app.get("/api/events/stats")
def event_stats(user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM events"); total = cur.fetchone()[0]
    cur.execute(q("SELECT COUNT(*) FROM events WHERE status={PH}".replace("{PH}", PH)), ("Open",))
    open_count = cur.fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute(q("SELECT COUNT(*) FROM events WHERE event_date=?"), (today,))
    today_count = cur.fetchone()[0]
    cur.execute("SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type ORDER BY count DESC")
    by_type = rows_to_dicts(cur)
    conn.close()
    return {
        "total": total, "open": open_count,
        "resolved": total - open_count, "today": today_count,
        "by_type": by_type,
    }

@app.post("/api/events", status_code=201)
def create_event(event: EventCreate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    if USE_PG:
        cur.execute(q(
            "INSERT INTO events (facility_id, event_date, event_time, connection_established_time, "
            "event_type, operator, notes, status, resolution_notes, contacted_name, contact_phone, "
            "contact_attempts, time_first_contact, police_dispatched) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id"
        ), (event.facility_id, event.event_date, event.event_time,
            event.connection_established_time, event.event_type,
            event.operator, event.notes, event.status or "Open", event.resolution_notes,
            event.contacted_name, event.contact_phone, event.contact_attempts,
            event.time_first_contact, event.police_dispatched or "No"))
        new_id = cur.fetchone()[0]
    else:
        cur.execute(q(
            "INSERT INTO events (facility_id, event_date, event_time, connection_established_time, "
            "event_type, operator, notes, status, resolution_notes, contacted_name, contact_phone, "
            "contact_attempts, time_first_contact, police_dispatched) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        ), (event.facility_id, event.event_date, event.event_time,
            event.connection_established_time, event.event_type,
            event.operator, event.notes, event.status or "Open", event.resolution_notes,
            event.contacted_name, event.contact_phone, event.contact_attempts,
            event.time_first_contact, event.police_dispatched or "No"))
        new_id = cur.lastrowid
    conn.commit()
    cur.execute(q(
        "SELECT e.*, f.name as facility_name FROM events e "
        "LEFT JOIN facilities f ON e.facility_id=f.id WHERE e.id=?"
    ), (new_id,))
    result = row_to_dict(cur)
    conn.close()
    return result

@app.put("/api/events/{event_id}")
def update_event(event_id: int, event: EventUpdate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(q("SELECT * FROM events WHERE id=?"), (event_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
    fields = {k: v for k, v in event.dict().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}={PH}" for k in fields)
        cur.execute(f"UPDATE events SET {sets} WHERE id={PH}", (*fields.values(), event_id))
        conn.commit()
    cur.execute(q(
        "SELECT e.*, f.name as facility_name FROM events e "
        "LEFT JOIN facilities f ON e.facility_id=f.id WHERE e.id=?"
    ), (event_id,))
    result = row_to_dict(cur)
    conn.close()
    return result

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(q("DELETE FROM events WHERE id=?"), (event_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/events/export")
def export_events(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    facility_id: Optional[int] = None,
    user: str = Depends(authenticate),
):
    conn = get_db()
    cur = conn.cursor()
    sql = """
        SELECT e.id, f.name as facility, e.event_date, e.event_time,
               e.connection_established_time, e.event_type, e.operator,
               e.status, e.notes, e.resolution_notes, e.created_at
        FROM events e LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE 1=1
    """
    params = []
    if facility_id: sql += f" AND e.facility_id={PH}"; params.append(facility_id)
    if date_from:   sql += f" AND e.event_date>={PH}"; params.append(date_from)
    if date_to:     sql += f" AND e.event_date<={PH}"; params.append(date_to)
    sql += " ORDER BY e.event_date DESC, e.event_time DESC"
    cur.execute(sql, params)
    rows = rows_to_dicts(cur)
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Facility","Event Date","Event Time","WT Connection Time",
                     "Event Type","Operator","Status","Notes","Resolution Notes","Logged At"])
    for row in rows:
        writer.writerow(list(row.values()))
    output.seek(0)
    filename = f"watchtower_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ─── Frontend ──────────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_frontend(user: str = Depends(authenticate)):
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()
