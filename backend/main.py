import logging
from contextlib import asynccontextmanager
from functools import lru_cache

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer


from alembic import command
from alembic.config import Config

import sentry_sdk
from backend.api.routes import router as api_router
from shared_utils.settings import (
    get_settings,
    get_logger
)

settings = get_settings()
logger = get_logger(level="info")



def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):  # noqa: ARG001
    logger.info("Starting up...")
    
    if settings.RUN_MIGRATIONS:
        logger.info("Run alembic upgrade head...")
        run_migrations()
        logger.info("Migrations completed...")
    
    yield
    logger.info("Shutting down...")

if settings.SENTRY_DSN and settings.ENVIRONMENT in ["dev", "preprod", "prod"]:  # noqa: SIM102
    # Placeholder check added because of default value in SSM/secrets.tf
    if settings.SENTRY_DSN != "placeholder":
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            # Reduce these sample rates in busy environments, as quota gets eaten up fast
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure CORS

origins = [settings.APP_URL]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)  # noqa: S104
