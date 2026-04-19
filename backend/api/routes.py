from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends, Header

from starlette.responses import JSONResponse

from backend.utils.database.auth import get_current_user
from shared_utils.database.pydantic_schemas import User as PyUser
from shared_utils.database.pydantic_schemas import Item as PyItem
from shared_utils.database import postgres_interface as interface

from shared_utils.database.pydantic_schemas import UserGroup as PyUserGroup


from shared_utils.auth import is_authorised_user, get_user_info
from shared_utils.settings import get_settings, get_logger

router = APIRouter()


models = {
    "user": PyUser,
    "item": PyItem,
    "user-group": PyUserGroup,
}


settings = get_settings()
logger = get_logger(level=settings.LOG_LEVEL)


@router.get("/userinfo")
def user_info(authorization: Annotated[str, Header()]):  # noqa: B008, ARG001
    logger.refresh_context()

    current_user = get_user_info(authorization)
    if not current_user.is_authorised:
        logger.info("User {email} not authorised to access app due to {auth_reason}", email=current_user.email, auth_reason=current_user.auth_reason)
        return JSONResponse(status_code=401, content={"error": f"{current_user.email} not authorised to access this app"})
    
    logger.info("User {email} accessed UserInfo endpoint", email=current_user.email)
    return {"User": f"{current_user.email}"}


@router.get("/")
def read_root(current_user: PyUser = Depends(get_current_user)):  # noqa: B008, ARG001
    logger.refresh_context()
    
    return {"Hello": "World"}


@router.get("/healthcheck")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})


@router.get("/info")
async def info():
    return {"backend": "FastAPI"}
