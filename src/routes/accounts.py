from datetime import datetime, timezone
from typing import cast

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config.dependencies import get_settings, get_jwt_auth_manager
from config.settings import Settings
from database.postgres_session import get_postgres_db
from exception.security import BaseSecurityError
from models.accounts import UserModel, UserGroupModel, UserGroupEnum, ActivationTokenModel, RefreshTokenModel
from schemas.accounts import UserRequestSchema, UserResponseSchema, MessageResponseSchema, UserActivationRequestSchema, \
    UserLoginResponseSchema, UserLoginRequestSchema, TokenRefreshResponseSchema, TokenRefreshRequestSchema
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager

router = APIRouter()

@router.post(
    "/register/",
    summary="User Registration",
    description="Register a new user with an email and password.",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
            409: {
                "description": "Conflict - User with this email already exists.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "A user with this email test@example.com already exists."
                        }
                    }
                },
            },
            500: {
                "description": "Internal Server Error - An error occurred during user creation.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "An error occurred during user creation."
                        }
                    }
                },
            },
        }
)
async def register_user(
        data_user: UserRequestSchema,
        db: AsyncSession = Depends(get_postgres_db)
) -> UserResponseSchema:
    request = await db.execute(select(UserModel).where(UserModel.email == data_user.email))
    response_user_exist = request.scalar_one_or_none()
    if response_user_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with such email {data_user.email} already exists"
        )

    request_group = await db.execute(select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER))
    group = request_group.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group was not found"
        )

    try:
        user = UserModel.create(
            email=str(data_user.email),
            raw_password=data_user.password,
            group_id=group.id,
        )
        db.add(user)
        await db.flush()

        activation_token = ActivationTokenModel(user_id=user.id)
        db.add(activation_token)

        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during user registration"
        ) from e
    return UserResponseSchema.model_validate(user)


@router.post(
    "/activate/",
    response_model=MessageResponseSchema,
    summary="Activate User Account",
    description="Activate a user's account using their email and activation token.",
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "description": "Bad Request - The activation token is invalid or expired, "
                           "or the user account is already active.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid Token",
                            "value": {
                                "detail": "Invalid or expired activation token."
                            }
                        },
                        "already_active": {
                            "summary": "Account Already Active",
                            "value": {
                                "detail": "User account is already active."
                            }
                        },
                    }
                }
            },
        },
    },
)
async def activate_account(
        activation_data: UserActivationRequestSchema,
        db: AsyncSession = Depends(get_postgres_db)
) -> MessageResponseSchema:
    """
    Endpoint to activate a user's account.

    This endpoint verifies the activation token for a user by checking that the token record exists
    and that it has not expired. If the token is valid and the user's account is not already active,
    the user's account is activated and the activation token is deleted. If the token is invalid, expired,
    or if the account is already active, an HTTP 400 error is raised.

    Args:
        activation_data (UserActivationRequestSchema): Contains the user's email and activation token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageResponseSchema: A response message confirming successful activation.

    Raises:
        HTTPException:
            - 400 Bad Request if the activation token is invalid or expired.
            - 400 Bad Request if the user account is already active.
    """
    stmt = (
        select(ActivationTokenModel)
        .options(joinedload(ActivationTokenModel.user))
        .join(UserModel)
        .where(
            UserModel.email == activation_data.email,
            ActivationTokenModel.token == activation_data.token
        )
    )
    result = await db.execute(stmt)
    token_record = result.scalars().first()

    now_utc = datetime.now(timezone.utc)
    if not token_record or cast(datetime, token_record.expires_at).replace(tzinfo=timezone.utc) < now_utc:
        if token_record:
            await db.delete(token_record)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation token."
        )

    user = token_record.user
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is already active."
        )

    user.is_active = True
    await db.delete(token_record)
    await db.commit()

    return MessageResponseSchema(message="User account activated successfully.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    summary="Login User",
    description="Authenticate user and return access and refresh token",
    status_code=status.HTTP_200_OK,
    responses={
            401: {
                "description": "Unauthorized - Invalid email or password.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "Invalid email or password."
                        }
                    }
                },
            },
            403: {
                "description": "Forbidden - User account is not activated.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "User account is not activated."
                        }
                    }
                },
            },
            500: {
                "description": "Internal Server Error - An error occurred while processing the request.",
                "content": {
                    "application/json": {
                        "example": {
                            "detail": "An error occurred while processing the request."
                        }
                    }
                },
            },
        },
)
async def login_user(
        login_data: UserLoginRequestSchema,
        db: AsyncSession = Depends(get_postgres_db),
        settings: Settings = Depends(get_settings),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    request = await db.execute(select(UserModel).filter_by(email=login_data.email))
    user = request.scalars().one_or_none()

    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated."
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    try:
        refresh_token = RefreshTokenModel.create(
            user_id=user.id,
            days_valid=settings.LOGIN_TIME_DAYS,
            token=jwt_refresh_token
        )
        db.add(refresh_token)
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        )

    jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
    )


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    summary="Refresh access token",
    description="Refresh the access token using valid refresh token",
    responses={
        400: {
            "description": "Bad Request - The Provided refresh token are invalid or expired.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Token has expired"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Refresh token not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Refresh token not found."
                    }
                }
            }
        },
        404: {
            "description": "Not Found = The user associated with the token does not exist.",
            "content": {
                "content_type": {
                    "application/json": {
                        "content": {
                            "detail": "Not found."
                        }
                    }
                }
            }
        }

    }
)
async def refresh_access_token(
        token_data: TokenRefreshRequestSchema,
        db: AsyncSession = Depends(get_postgres_db),
        jwt_manager: JWTAuthManager = Depends(get_jwt_auth_manager),
):
    """
        Endpoint to refresh an access token.

        Validates the provided refresh token, extracts the user ID from it, and issues
        a new access token. If the token is invalid or expired, an error is returned.

        Args:
            token_data (TokenRefreshRequestSchema): Contains the refresh token.
            db (AsyncSession): The asynchronous database session.
            jwt_manager (JWTAuthManagerInterface): JWT authentication manager.

        Returns:
            TokenRefreshResponseSchema: A new access token.

        Raises:
            HTTPException:
                - 400 Bad Request if the token is invalid or expired.
                - 401 Unauthorized if the refresh token is not found.
                - 404 Not Found if the user associated with the token does not exist.
        """

    try:
        decode_refresh_token = jwt_manager.decode_refresh_token(token_data.refresh_token)
        user_id = decode_refresh_token.get("user_id")
    except BaseSecurityError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    request = await db.execute(select(RefreshTokenModel).filter_by(token=token_data.refresh_token))
    refresh_token = request.scalars().one_or_none()

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    request_user = await db.execute(select(UserModel).filter_by(id=user_id))
    user = request_user.scalars().one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    access_token = jwt_manager.create_access_token({"user_id": user.id})
    return TokenRefreshResponseSchema(access_token=access_token)
