"""
escalation_scheduler.py
=======================
Standalone background scheduler for auto-escalation.
Run this SEPARATELY alongside app.py:

    python escalation_scheduler.py

It checks every 15 minutes for unresolved Level 1 grievances
older than ESCALATION_HOURS and escalates them automatically —
completely independent of whether anyone has the app open.
"""

import time
import logging
from datetime import datetime, timezone
from supabase_client import get_client

# ── Config ────────────────────────────────────────────────────────────────────
ESCALATION_HOURS   = 24      # hours before auto-escalation
CHECK_INTERVAL_SEC = 900     # check every 15 minutes (900 seconds)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [ESCALATOR]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("escalation.log"),   # logs to file
        logging.StreamHandler(),                  # also prints to terminal
    ]
)
log = logging.getLogger(__name__)

# ── DB ────────────────────────────────────────────────────────────────────────
def db():
    return get_client()

def parse_timestamp(raw: str) -> datetime | None:
    """Parse Supabase timestamp in any format → UTC-aware datetime."""
    if not raw:
        return None
    try:
        clean = raw.replace(" ", "T")
        if "." in clean:
            dot = clean.index(".")
            clean = clean[:dot] + clean[dot+7:]
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None

# ── Core Escalation Logic ─────────────────────────────────────────────────────
def run_escalation_check():
    log.info("Running escalation check...")
    try:
        res = db().table("grievances").select("*") \
                  .eq("escalation_level", 1) \
                  .execute()
        all_g = res.data or []
    except Exception as e:
        log.error(f"Failed to fetch grievances: {e}")
        return

    now   = datetime.now(timezone.utc)
    count = 0

    for g in all_g:
        # Only act on unresolved grievances
        if g["status"] not in ("Pending", "In Progress"):
            continue

        created = parse_timestamp(g.get("created_at", ""))
        if not created:
            log.warning(f"Could not parse created_at for grievance {g['id'][:8]}")
            continue

        age_hours = (now - created).total_seconds() / 3600

        if age_hours >= ESCALATION_HOURS:
            existing = g.get("admin_notes") or ""
            note = (
                f"⚡ Auto-escalated by system: No HR action within {ESCALATION_HOURS}h. "
                f"Age at escalation: {age_hours:.1f}h. "
                f"Forwarded to Department Head."
            )
            final = f"{existing}\n{note}".strip() if existing else note

            try:
                db().table("grievances").update({
                    "status":           "Escalated",
                    "escalation_level": 2,
                    "admin_notes":      final,
                }).eq("id", g["id"]).execute()

                log.info(
                    f"  ✅ Escalated: #{g['id'][:8].upper()} "
                    f"| {g['owner_email']} "
                    f"| {g['priority']} priority "
                    f"| Age: {age_hours:.1f}h"
                )
                count += 1
            except Exception as e:
                log.error(f"  ❌ Failed to escalate {g['id'][:8]}: {e}")

    if count == 0:
        log.info(f"  No grievances needed escalation. "
                 f"(checked {len([g for g in all_g if g['status'] in ('Pending','In Progress')])} active)")
    else:
        log.info(f"  Total escalated this run: {count}")

# ── Main Loop ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("=" * 55)
    log.info(f"  Auto-Escalation Scheduler started")
    log.info(f"  Escalation threshold : {ESCALATION_HOURS} hours")
    log.info(f"  Check interval       : {CHECK_INTERVAL_SEC // 60} minutes")
    log.info("=" * 55)

    while True:
        run_escalation_check()
        log.info(f"Next check in {CHECK_INTERVAL_SEC // 60} minutes...")
        time.sleep(CHECK_INTERVAL_SEC)