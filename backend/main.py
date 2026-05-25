import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.db import store
from backend.routes import applications, auth, cron, gmail, health, suggested_jobs
from backend.services import gmail_service
from backend.services.notifier import run_scheduled_digest

load_dotenv()
logging.basicConfig(level=logging.INFO)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
scheduler = BackgroundScheduler()


def _digest_job_sync() -> None:
    asyncio.run(run_scheduled_digest(store.get_all))


def _gmail_fetch_sync() -> None:
    from backend.routes.gmail import run_fetch_and_classify
    try:
        asyncio.run(run_fetch_and_classify())
    except Exception:
        logging.getLogger(__name__).exception("[scheduler] Gmail fetch cycle failed")


def _renew_watch_sync() -> None:
    try:
        gmail_service.start_watch()
        logging.info("[scheduler] Gmail Pub/Sub watch renewed")
    except Exception:
        logging.getLogger(__name__).exception("[scheduler] Gmail watch renewal failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    on_vercel = os.getenv("VERCEL") == "1"
    digest_enabled = os.getenv("DIGEST_ENABLED", "true").lower() != "false"

    if not on_vercel:
        if digest_enabled:
            scheduler.add_job(_digest_job_sync, "cron", hour=21, minute=0, id="digest")
            print("[server] Discord digest scheduled for 9:00 PM daily")

        if gmail_service.is_authenticated():
            scheduler.add_job(
                _gmail_fetch_sync, "interval", minutes=15, id="gmail_fetch"
            )
            print("[server] Gmail fetch scheduled every 15 minutes")

            if os.getenv("GOOGLE_CLOUD_PROJECT_ID"):
                scheduler.add_job(
                    _renew_watch_sync, "interval", days=6, id="gmail_watch"
                )
                print("[server] Gmail Pub/Sub watch renewal scheduled every 6 days")

        if scheduler.get_jobs():
            scheduler.start()

    yield

    if scheduler.running:
        scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Game of Throne",
        description="Automated job pipeline dashboard",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "https://game-of-throne-seven.vercel.app",
            "https://game-of-throne-pmvxa56vy-kenneth-vemagiris-projects.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(applications.router)
    app.include_router(suggested_jobs.router)
    app.include_router(cron.router)
    app.include_router(auth.router)
    print("[startup] AUTH ROUTES LOADED")
    app.include_router(gmail.router)

    print("[startup] ALL REGISTERED ROUTES:")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"  {','.join(route.methods):10s} {route.path}")
        else:
            print(f"  {'MOUNT':10s} {route.path}")

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
