import os
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import requests as http_requests

load_dotenv()

app = Flask(__name__)

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_KEY = os.getenv("API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Riyadh")

scheduler = BackgroundScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone=TIMEZONE,
)
scheduler.start()


def send_whatsapp_message(to: str, message: str, job_id: str):
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    resp = http_requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    app.logger.info("Message sent to %s (job %s): %s", to, job_id, resp.json())


def require_api_key(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not key or key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "scheduled_jobs": len(scheduler.get_jobs())})


@app.route("/schedule", methods=["POST"])
@require_api_key
def schedule_message():
    data = request.get_json(force=True)

    to = data.get("to", "").strip()
    message = data.get("message", "").strip()
    send_at = data.get("send_at", "").strip()

    if not to or not message or not send_at:
        return jsonify({"error": "Missing required fields: to, message, send_at"}), 400

    to = to.lstrip("+").replace(" ", "").replace("-", "")
    if not to.isdigit() or len(to) < 10:
        return jsonify({"error": "Invalid phone number"}), 400

    try:
        scheduled_time = datetime.fromisoformat(send_at)
    except ValueError:
        return jsonify({"error": "Invalid send_at format. Use ISO 8601: YYYY-MM-DDTHH:MM:SS"}), 400

    if scheduled_time.tzinfo is None:
        from zoneinfo import ZoneInfo
        scheduled_time = scheduled_time.replace(tzinfo=ZoneInfo(TIMEZONE))

    now = datetime.now(timezone.utc)
    if scheduled_time <= now:
        return jsonify({"error": "send_at must be in the future"}), 400

    job_id = str(uuid.uuid4())[:8]
    scheduler.add_job(
        send_whatsapp_message,
        "date",
        run_date=scheduled_time,
        args=[to, message, job_id],
        id=job_id,
        replace_existing=True,
    )

    return jsonify({
        "success": True,
        "job_id": job_id,
        "to": to,
        "message": message,
        "send_at": scheduled_time.isoformat(),
    }), 201


@app.route("/jobs", methods=["GET"])
@require_api_key
def list_jobs():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "job_id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "args": {"to": job.args[0], "message": job.args[1]},
        })
    return jsonify({"jobs": jobs})


@app.route("/jobs/<job_id>", methods=["DELETE"])
@require_api_key
def cancel_job(job_id):
    try:
        scheduler.remove_job(job_id)
        return jsonify({"success": True, "cancelled": job_id})
    except Exception:
        return jsonify({"error": "Job not found"}), 404


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5050))
    app.run(host=host, port=port, debug=True)
