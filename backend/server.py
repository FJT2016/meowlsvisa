"""FastAPI app entrypoint: wires routers and starts the email retry worker."""
import logging

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import client
from routes import admin, applications, auth, notifications, push
from services.email import start_retry_worker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI(title="Meowls e-Visa Portal")

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(applications.router)
api_router.include_router(admin.router)
api_router.include_router(notifications.router)
api_router.include_router(push.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    start_retry_worker()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    client.close()
