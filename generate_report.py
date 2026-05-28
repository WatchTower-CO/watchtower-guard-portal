#!/usr/bin/env python3
"""
Watch Tower — Weekly Report Generator
Runs automatically every Monday. Saves a CSV report to your Desktop.
"""

import sqlite3
import csv
import os
from datetime import datetime, timedelta

# ─── Config ────────────────────────────────────────────────────────────────────
# Path to your database (same folder as main.py)
DB_PATH     = os.path.join(os.path.dirname(__file__), "watchtower.db")

# Where to save weekly reports (Desktop folder)
REPORTS_DIR = os.path.expanduser("~/Desktop/Watch Tower Reports")

# ─── Setup ─────────────────────────────────────────────────────────────────────
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_weekly_report():
    today     = datetime.now()
    week_ago  = today - timedelta(days=7)
    date_from = week_ago.strftime("%Y-%m-%d")
    date_to   = today.strftime("%Y-%m-%d")
    week_label= f"{date_from}_to_{date_to}"

    conn = get_db()

    # ── Pull events for the week ──────────────────────────────────────────────
    events = conn.execute("""
        SELECT e.id, f.name as facility, e.event_date, e.event_time,
               e.connection_established_time, e.event_type, e.operator,
               e.status, e.notes, e.resolution_notes, e.created_at
        FROM events e
        LEFT JOIN facilities f ON e.facility_id = f.id
        WHERE e.event_date >= ? AND e.event_date <= ?
        ORDER BY e.event_date DESC, e.event_time DESC
    """, (date_from, date_to)).fetchall()

    # ── Compute summary stats ─────────────────────────────────────────────────
    total    = len(events)
    open_ev  = sum(1 for e in events if e["status"] == "Open")
    resolved = sum(1 for e in events if e["status"] == "Resolved")

    type_counts = {}
    for e in events:
        t = e["event_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # ── Connection time average ───────────────────────────────────────────────
    diffs = []
    for e in events:
        et = e["event_time"]
        ct = e["connection_established_time"]
        if et and ct:
            try:
                eh, em = map(int, et.split(":"))
                ch, cm = map(int, ct.split(":"))
                diff = (ch * 60 + cm) - (eh * 60 + em)
                if 0 <= diff < 60:
                    diffs.append(diff)
            except Exception:
                pass
    avg_conn = (sum(diffs) / len(diffs)) if diffs else None

    conn.close()

    # ── Build filename ────────────────────────────────────────────────────────
    filename = f"WatchTower_Weekly_Report_{week_label}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        # Summary section
        writer.writerow(["WATCH TOWER — WEEKLY REPORT"])
        writer.writerow([f"Period: {date_from} to {date_to}"])
        writer.writerow([f"Generated: {today.strftime('%B %d, %Y at %I:%M %p')}"])
        writer.writerow([])

        writer.writerow(["── SUMMARY ──"])
        writer.writerow(["Total Events", total])
        writer.writerow(["Open",         open_ev])
        writer.writerow(["Resolved",     resolved])
        if avg_conn is not None:
            mins = int(avg_conn)
            secs = int((avg_conn - mins) * 60)
            writer.writerow(["Avg WT Connection Time", f"{mins}m {secs}s" if mins else f"{secs}s"])
        writer.writerow([])

        writer.writerow(["── EVENTS BY TYPE ──"])
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            writer.writerow([t, c])
        writer.writerow([])

        # Events detail
        writer.writerow(["── EVENT LOG ──"])
        writer.writerow(["ID", "Facility", "Date", "Time", "WT Connection Time",
                          "Type", "Operator", "Status", "Notes", "Resolution", "Logged At"])

        if events:
            for e in events:
                writer.writerow([
                    e["id"], e["facility"] or "—", e["event_date"], e["event_time"],
                    e["connection_established_time"] or "—", e["event_type"],
                    e["operator"] or "—", e["status"],
                    e["notes"] or "", e["resolution_notes"] or "", e["created_at"]
                ])
        else:
            writer.writerow(["No events recorded this week."])

    print(f"[Watch Tower] Weekly report saved: {filepath}")
    print(f"  Period  : {date_from} → {date_to}")
    print(f"  Events  : {total} total ({open_ev} open, {resolved} resolved)")
    if avg_conn is not None:
        mins = int(avg_conn)
        secs = int((avg_conn - mins) * 60)
        print(f"  Avg conn: {mins}m {secs}s")
    return filepath

if __name__ == "__main__":
    generate_weekly_report()
