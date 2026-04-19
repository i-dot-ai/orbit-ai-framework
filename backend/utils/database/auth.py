

from shared_utils.database.pydantic_schemas import User as PyUser
from shared_utils.database.pydantic_schemas import UserFilter
from shared_utils.database.pydantic_schemas import UserUpdate
from shared_utils.database.pydantic_schemas import UserCreate
from shared_utils.database import postgres_interface as interface

from shared_utils.auth import get_user_info
from typing import Annotated
from fastapi import Header
from fastapi import HTTPException


from shared_utils.settings import (
    get_settings,
    get_logger
)
from shared_utils.exceptions import MissingAuthTokenError
from i_dot_ai_utilities.auth.auth_api import UserAuthorisationResult
from typing import Annotated
from fastapi import Header
from fastapi import HTTPException


settings = get_settings()
logger = get_logger(level=settings.LOG_LEVEL)


def get_current_user(x_amzn_oidc_data: Annotated[str, Header()] = None) -> PyUser | None:  # noqa: RUF013, PLR0912, C901
    """
    Called on every endpoint to retrieve user information in the JWT passed under the "Authorization" header.
    Gets the user details, and creates them in a DB if there is one and the user doesn't exist.
    Args:
        x_amzn_oidc_data: The incoming JWT on the AWS auth header, passed via the frontend app
    Returns:
        User: The user matching the username in the token
    """
    authorisation_token: str | None = x_amzn_oidc_data

    try:
        user_auth_info = get_user_info(authorisation_token)

        if not user_auth_info.is_authorised:
            logger.info("User {email} does not have the required permissions", email=user_auth_info.email)
            raise HTTPException(
                status_code=401,
                detail="User does not have the required permissions to access this resource",
            )

        users: list[PyUser] = interface.filter_items(UserFilter(email=user_auth_info.email))
        user = users[0] if len(users) > 0 else None

        
    
        if not user:
            logger.info("User not found with email {email}, creating", email=user.email)
            user: PyUser = interface.get_or_create_item(UserCreate(email=user.email))
        else:
            user = interface.update_item(UserUpdate(id=user.id, email=user.email))

        return user

        
    except MissingAuthTokenError as e:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except HTTPException as e:
        logger.exception("Unhandled HTTP exception")
        raise e
    except Exception as e:
        logger.exception("Unhandled exception when getting user")
        raise HTTPException(
            status_code=500,
            detail="Unhandled Authorisation Error",
        ) from e
