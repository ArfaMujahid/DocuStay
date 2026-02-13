"""DocuStay Demo – FastAPI application."""
# Load .env before any app code that might read config
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
# Import models so Base.metadata has all tables before create_all (schema source of truth)
from app.models import (  # noqa: F401
    User, OwnerProfile, Property, GuestProfile, Stay, RegionRule,
    Invitation, GuestPendingInvite, AgreementSignature, ReferenceOption,
    AuditLog, OwnerPOASignature, PendingRegistration,
)
from app.routers import auth, owners, guests, stays, region_rules, jle, dashboard, notifications, agreements

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(owners.router)
app.include_router(guests.router)
app.include_router(stays.router)
app.include_router(region_rules.router)
app.include_router(jle.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(agreements.router)


@app.on_event("startup")
def startup():
    if settings.mailgun_api_key and settings.mailgun_domain:
        from_addr = getattr(settings, "mailgun_from_email", "") or ""
        from_domain = from_addr.split("@")[-1].lower() if "@" in from_addr else ""
        send_domain = (settings.mailgun_domain or "").strip().lower()
        if from_domain and send_domain and from_domain != send_domain:
            print(f"[Mailgun] WARNING: from={from_addr} does not match domain={settings.mailgun_domain}. Emails may not be delivered!")
            print(f"[Mailgun] Fix: in .env set MAILGUN_FROM_EMAIL=noreply@{settings.mailgun_domain} then restart")
        else:
            print(f"[Mailgun] App using domain={settings.mailgun_domain} from={from_addr or '(none)'} (verification & all emails use this)")
    else:
        print("[Mailgun] Not configured - verification emails will be skipped; set MAILGUN_API_KEY and MAILGUN_DOMAIN in .env and restart")
    try:
        Base.metadata.create_all(bind=engine)
        from app.database import SessionLocal
        from app.seed import seed_region_rules
        db = SessionLocal()
        try:
            seed_region_rules(db)
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").warning("Database startup failed (tables/seed skipped). Check DATABASE_URL and network. Error: %s", e)

    # Scheduler: optional stay notifications (invitation cleanup removed; expired invites are labeled, not deleted)
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        if settings.notification_cron_enabled:
            from app.services.stay_timer import run_stay_notification_job
            scheduler.add_job(run_stay_notification_job, "cron", hour=9, minute=0)
        scheduler.start()
    except Exception:
        pass


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/db-setup")
def db_setup():
    """Dev/demo only: create tables and seed region rules if DB is now available."""
    import logging
    from fastapi.responses import JSONResponse
    log = logging.getLogger("uvicorn.error")
    try:
        Base.metadata.create_all(bind=engine)
        from app.database import SessionLocal
        from app.seed import seed_region_rules
        db = SessionLocal()
        try:
            seed_region_rules(db)
        finally:
            db.close()
        return {"status": "ok", "message": "Tables created and region rules seeded."}
    except Exception as e:
        log.exception("db-setup failed")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)},
        )
