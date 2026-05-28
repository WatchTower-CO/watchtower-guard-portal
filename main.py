from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import csv
import io
import secrets
from datetime import datetime

app = FastAPI(title="Watch Tower Alarm Tracker")

# ─── Security ──────────────────────────────────────────────────────────────────
# Change these to your own username and password
APP_USERNAME = "watchtower"
APP_PASSWORD = "wt-secure-2024"

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, APP_USERNAME)
    correct_pass = secrets.compare_digest(credentials.password, APP_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Access denied",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ─── Database ──────────────────────────────────────────────────────────────────
# Uses DB_PATH env variable on Render, falls back to local file when running on your Mac
BASE_DIR   = os.path.dirname(__file__)
DB_PATH    = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "watchtower.db"))
STATIC_DIR = BASE_DIR  # index.html and logo live at the repo root

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
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

# ─── Facility Routes ───────────────────────────────────────────────────────────
@app.get("/api/facilities")
def list_facilities(user: str = Depends(authenticate)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM facilities ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/facilities", status_code=201)
def create_facility(facility: FacilityCreate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO facilities (name, address, contact_name, contact_phone, notes) VALUES (?,?,?,?,?)",
        (facility.name, facility.address, facility.contact_name, facility.contact_phone, facility.notes)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM facilities WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)

@app.put("/api/facilities/{facility_id}")
def update_facility(facility_id: int, facility: FacilityUpdate, user: str = Depends(authenticate)):
    conn = get_db()
    existing = conn.execute("SELECT * FROM facilities WHERE id=?", (facility_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Facility not found")
    fields = {k: v for k, v in facility.dict().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE facilities SET {sets} WHERE id=?", (*fields.values(), facility_id))
        conn.commit()
    row = conn.execute("SELECT * FROM facilities WHERE id=?", (facility_id,)).fetchone()
    conn.close()
    return dict(row)

@app.delete("/api/facilities/{facility_id}")
def delete_facility(facility_id: int, user: str = Depends(authenticate)):
    conn = get_db()
    conn.execute("DELETE FROM facilities WHERE id=?", (facility_id,))
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
    query = """
        SELECT e.*, f.name as facility_name
        FROM events e LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE 1=1
    """
    params = []
    if facility_id: query += " AND e.facility_id=?"; params.append(facility_id)
    if event_type:  query += " AND e.event_type=?";  params.append(event_type)
    if status:      query += " AND e.status=?";      params.append(status)
    if date_from:   query += " AND e.event_date>=?"; params.append(date_from)
    if date_to:     query += " AND e.event_date<=?"; params.append(date_to)
    query += " ORDER BY e.event_date DESC, e.event_time DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/events/stats")
def event_stats(user: str = Depends(authenticate)):
    conn = get_db()
    total       = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    open_count  = conn.execute("SELECT COUNT(*) FROM events WHERE status='Open'").fetchone()[0]
    today       = datetime.now().strftime("%Y-%m-%d")
    today_count = conn.execute("SELECT COUNT(*) FROM events WHERE event_date=?", (today,)).fetchone()[0]
    by_type     = conn.execute(
        "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return {
        "total": total, "open": open_count,
        "resolved": total - open_count, "today": today_count,
        "by_type": [dict(r) for r in by_type],
    }

@app.post("/api/events", status_code=201)
def create_event(event: EventCreate, user: str = Depends(authenticate)):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO events
           (facility_id, event_date, event_time, connection_established_time,
            event_type, operator, notes, status, resolution_notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (event.facility_id, event.event_date, event.event_time,
         event.connection_established_time, event.event_type,
         event.operator, event.notes, event.status or "Open", event.resolution_notes)
    )
    conn.commit()
    row = conn.execute(
        "SELECT e.*, f.name as facility_name FROM events e LEFT JOIN facilities f ON e.facility_id=f.id WHERE e.id=?",
        (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(row)

@app.put("/api/events/{event_id}")
def update_event(event_id: int, event: EventUpdate, user: str = Depends(authenticate)):
    conn = get_db()
    existing = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Event not found")
    fields = {k: v for k, v in event.dict().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE events SET {sets} WHERE id=?", (*fields.values(), event_id))
        conn.commit()
    row = conn.execute(
        "SELECT e.*, f.name as facility_name FROM events e LEFT JOIN facilities f ON e.facility_id=f.id WHERE e.id=?",
        (event_id,)
    ).fetchone()
    conn.close()
    return dict(row)

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, user: str = Depends(authenticate)):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id=?", (event_id,))
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
    query = """
        SELECT e.id, f.name as facility, e.event_date, e.event_time,
               e.connection_established_time, e.event_type, e.operator,
               e.status, e.notes, e.resolution_notes, e.created_at
        FROM events e LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE 1=1
    """
    params = []
    if facility_id: query += " AND e.facility_id=?"; params.append(facility_id)
    if date_from:   query += " AND e.event_date>=?"; params.append(date_from)
    if date_to:     query += " AND e.event_date<=?"; params.append(date_to)
    query += " ORDER BY e.event_date DESC, e.event_time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Facility","Event Date","Event Time","WT Connection Time",
                     "Event Type","Operator","Status","Notes","Resolution Notes","Logged At"])
    for row in rows:
        writer.writerow(list(row))
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
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path) as f:
        return f.read()
