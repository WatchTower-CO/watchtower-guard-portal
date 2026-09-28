#!/usr/bin/env python3
"""
Watch Tower — Weekly Report Generator
Runs automatically every Monday. Pulls live data from Render and saves
a CSV report to your Desktop.
"""

import csv
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import json
import base64
from datetime import datetime, timedelta

# ─── Config ────────────────────────────────────────────────────────────────────
RENDER_URL   = "https://wt-portal.onrender.com"
APP_USERNAME = "watchtower"
APP_PASSWORD = "wt-secure-2024"

# Where to save weekly reports (Desktop folder)
REPORTS_DIR  = os.path.expanduser("~/Desktop/Watch Tower Reports")

# ─── Setup ─────────────────────────────────────────────────────────────────────
os.makedirs(REPORTS_DIR, exist_ok=True)

def api_get(path, params=None):
    """Make an authenticated GET request to the Render app."""
    url = RENDER_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    credentials = base64.b64encode(
        f"{APP_USERNAME}:{APP_PASSWORD}".encode()
    ).decode()

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {credentials}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[Watch Tower] API error {e.code}: {e.reason}")
        print("  Check that the Render app is running and your credentials are correct.")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[Watch Tower] Could not reach {RENDER_URL}")
        print(f"  Reason: {e.reason}")
        print("  Make sure you have an internet connection and Render is live.")
        sys.exit(1)

def generate_weekly_report():
    today      = datetime.now()
    week_ago   = today - timedelta(days=7)
    date_from  = week_ago.strftime("%Y-%m-%d")
    date_to    = today.strftime("%Y-%m-%d")
    week_label = f"{date_from}_to_{date_to}"

    print(f"[Watch Tower] Fetching events from {RENDER_URL} ...")

    # ── Pull events from live Render API ──────────────────────────────────────
    events = api_get("/api/events", {
        "date_from": date_from,
        "date_to":   date_to,
    })

    # ── Compute summary stats ─────────────────────────────────────────────────
    total    = len(events)
    open_ev  = sum(1 for e in events if e.get("status") == "Open")
    resolved = sum(1 for e in events if e.get("status") == "Resolved")

    type_counts = {}
    for e in events:
        t = e.get("event_type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    # ── Connection time average ───────────────────────────────────────────────
    diffs = []
    for e in events:
        et = e.get("event_time")
        ct = e.get("connection_established_time")
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

    # ── Build filename ────────────────────────────────────────────────────────
    filename = f"WatchTower_Weekly_Report_{week_label}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["WATCH TOWER — WEEKLY REPORT"])
        writer.writerow([f"Period: {date_from} to {date_to}"])
        writer.writerow([f"Generated: {today.strftime('%B %d, %Y at %I:%M %p')}"])
        writer.writerow([f"Source: {RENDER_URL}"])
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

        writer.writerow(["── EVENT LOG ──"])
        writer.writerow(["ID", "Facility", "Date", "Time", "WT Connection Time",
                          "Type", "Operator", "Status", "Notes", "Resolution", "Logged At"])

        if events:
            for row_num, e in enumerate(events, start=1):
                writer.writerow([
                    row_num,
                    e.get("facility_name") or e.get("facility") or "—",
                    e.get("event_date"),
                    e.get("event_time"),
                    e.get("connection_established_time") or "—",
                    e.get("event_type"),
                    e.get("operator") or "—",
                    e.get("status"),
                    e.get("notes") or "",
                    e.get("resolution_notes") or "",
                    e.get("created_at"),
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
