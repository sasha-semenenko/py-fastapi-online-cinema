from datetime import timezone, datetime

import pytest

from sqlalchemy import select

from src.models.accounts import UserModel, ActivationTokenModel, UserGroupModel, UserGroupEnum, RefreshTokenModel, \
    PasswordResetTokenModel
from sqlalchemy.orm import joinedload

@pytest.mark.asyncio
async def test_user_register_success(client, db_session):
    """
    Test successful user registration.

    Validates that a new user and an activation token are created in the database.
    """
    payloads = {
        "email": "test@example.com",
        "password": "Pass123q!"
    }
    response = await client.post("/accounts/register/", json=payloads)
    assert response.status_code == 201, "Expected status code 201 Created"
    response_data = response.json()
    assert response_data["email"] == payloads["email"], "Expected that email are equal"
    assert "id" not in response_data, "Expected that id not in response"

    user = select(UserModel).where(UserModel.email == payloads["email"])
    response_user = await db_session.execute(user)
    current_user = response_user.scalar_one_or_none()
    assert current_user is not None, "Expected user are created in the database"
    assert current_user.email == payloads["email"], "Expected that emails are equal"

    token = select(ActivationTokenModel).where(ActivationTokenModel.user_id == current_user.id)
    response_token = await db_session.execute(token)
    activation_token = response_token.scalar_one_or_none()
    assert activation_token is not None, "Activation token was not created in the database."
    assert activation_token.user_id == current_user.id, "Activation token's user_id does not match."
    assert activation_token.token is not None, "Activation token has no token value."

    expires_at = activation_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    assert expires_at > datetime.now(timezone.utc), "Activation token is already expired."


@pytest.mark.asyncio
async def test_account_activation_success(client, db_session):
    """
    Test account user activation success
    """

    data = {
        "email": "admin@example.com",
        "password": "Pass123q!"
    }
    response = await client.post("/accounts/register/", json=data)
    assert response.status_code == 201, "Expected status code 201 for user activation account"

    request = select(UserModel).options(joinedload(UserModel.activation_token)).where(UserModel.email == data["email"])
    result = await db_session.execute(request)
    user = result.scalar_one_or_none()

    assert user is not None, "Expected user are created in the database"
    assert not user.is_active, "Expected user are not active"
    assert user.activation_token is not None and user.activation_token.token is not None, \
        "Activation token was not created in the database."

    activation_data = {
        "email": data["email"],
        "token": user.activation_token.token,
    }

    activation_response = await client.post("/accounts/activate/", json=activation_data)
    assert activation_response.status_code == 200, "Successfully activated user account"
    assert activation_response.json()["message"] == "User account activated successfully."

    request = select(UserModel).options(joinedload(UserModel.activation_token)).where(UserModel.email == data["email"])
    result = await db_session.execute(request)
    user = result.scalar_one_or_none()
    await db_session.refresh(user)
    assert user.is_active, "User should be active after successful activation."

    request_token = select(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id)
    response = await db_session.execute(request_token)
    token = response.scalar_one_or_none()
    assert token is None, "Token should be deleted from database after successful activation."


@pytest.mark.asyncio
async def test_login_user_success(client, db_session, jwt_manager):
    """
    Test login user and obtaining activation and refresh token success
    """
    payload = {
        "email": "user@example.com",
        "password": "Pass123q!"
    }

    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result = await db_session.execute(stmt)
    user_group = result.scalars().first()
    assert user_group is not None, "Default user group should exist."

    user = UserModel.create(
        email=payload["email"],
        raw_password=payload["password"],
        group_id=user_group.id
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()

    login_payload = {
        "email": payload["email"],
        "password": payload["password"]
    }

    response = await client.post("/accounts/login/", json=login_payload)
    assert response.status_code == 200, "Expected status code 200 for successfully login."

    response_json = response.json()
    assert "access_token" in response_json
    assert "refresh_token" in response_json
    assert response_json["access_token"], "Check access token"
    assert response_json["refresh_token"], "Check refresh token"

    access_token_data = jwt_manager.decode_access_token(response_json["access_token"])
    assert access_token_data["user_id"] == user.id, "Access token contain correct user ID."

    refresh_token_data = jwt_manager.decode_refresh_token(response_json["refresh_token"])
    assert refresh_token_data["user_id"] == user.id, "Refresh token contain correct user ID."

    response_refresh_token = select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    response = await db_session.execute(response_refresh_token)
    refresh_token = response.scalar_one_or_none()
    assert refresh_token is not None, "Refresh token was not stored in the database."
    assert refresh_token.token == response_json["refresh_token"], "Stored refresh token does not match."

    expires_at = refresh_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    assert expires_at > datetime.now(timezone.utc), "Refresh token is already expired."


@pytest.mark.asyncio
async def test_refresh_access_token_success(client, db_session, jwt_manager):
    """
    Test obtaining access token by refreshing refresh token
    """
    # create user in the database
    user_payload = {
        "email": "regular@example.com",
        "password": "Pass123q!"
    }

    request_group = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    response_group = await db_session.execute(request_group)
    group = response_group.scalar_one_or_none()
    assert group is not None, "Default user group should exist."

    user = UserModel.create(
        email=user_payload["email"],
        raw_password=user_payload["password"],
        group_id=group.id
    )

    user.is_active = True
    db_session.add(user)
    await db_session.commit()

    # log in the user for obtaining refresh token
    login_payload = {
        "email": user_payload["email"],
        "password": user_payload["password"]
    }
    request_login = await client.post("accounts/login/", json=login_payload)
    assert request_login.status_code == 200, "Expected status code 200 for successfully login."

    # using refresh token for obtain new access token
    response = request_login.json()
    refresh_token = response["refresh_token"]
    refresh_payload = {"refresh_token": refresh_token}

    request_refresh = await client.post("accounts/refresh/", json=refresh_payload)
    assert request_refresh.status_code == 200, "Expected status code 200 for successfully refresh."
    access_token = request_refresh.json()
    assert "access_token" in access_token, "Access token stored in the database."

    decode_access_token = jwt_manager.decode_access_token(access_token["access_token"])
    assert decode_access_token["user_id"] == user.id, "Access token contain correct user ID."


@pytest.mark.asyncio
async def test_reset_password_complete(client, db_session):
    """
    Test successful password reset token request
    """
    # register new user and make this user active
    register_payload = {
        "email": "ben@example.com",
        "password": "Pass123q!"
    }

    request_register = await client.post("/accounts/register/", json=register_payload)
    assert request_register.status_code == 201, "Expected status code 201 for successfully register."

    # mark user active
    request_user = select(UserModel).where(UserModel.email == register_payload["email"])
    response = await db_session.execute(request_user)
    user = response.scalar_one_or_none()
    assert user is not None, "User should exist in the database."
    user.is_active = True
    await db_session.commit()

    # # Verify that the endpoint returns status 200 and the expected success message.
    reset_payload = {"email": register_payload["email"]}
    reset_request = await client.post("/accounts/reset_token/request", json=reset_payload)
    assert reset_request.status_code == 200, "Expected status code 200 for successfully reset password."
    assert reset_request.json()["message"] == "If you are registered, you will receive an email with instructions."

    # Query the database to confirm that a PasswordResetTokenModel record was created.
    request_db = select(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id)
    response = await db_session.execute(request_db)
    token = response.scalar_one_or_none()
    assert token is not None, "Token should exist in the database."

    # Verify that the token's expiration date is in the future.
    expired_at = token.expires_at
    if expired_at.tzinfo is None:
        expired_at = expired_at.replace(tzinfo=timezone.utc)
    assert expired_at > datetime.now(timezone.utc), "Password reset token should have a future expiration date."


@pytest.mark.asyncio
async def test_reset_password_success(client, db_session, jwt_manager):
    """
        Test the complete password reset flow.

        Steps:
        - Register a user.
        - Activate the user.
        - Request a password reset token.
        - Use the token to reset the password.
        - Verify the password is updated in the database.
    """
    register_payload = {
        "email": "active@example.com",
        "password": "Pass123q!"
    }
    request_register = await client.post("/accounts/register/", json=register_payload)
    assert request_register.status_code == 201, "Expected status code 201 for successfully register."

    request_user = select(UserModel).where(UserModel.email == register_payload["email"])
    response = await db_session.execute(request_user)
    user = response.scalar_one_or_none()
    assert user is not None, "User should exist in the database."

    request_activation_token = select(ActivationTokenModel).where(ActivationTokenModel.user_id == user.id)
    response = await db_session.execute(request_activation_token)
    activation_token = response.scalar_one_or_none()
    assert activation_token is not None, "Activation token should exist in the database."

    activation_payload = {
        "email": register_payload["email"],
        "token": activation_token.token
    }

    request_activation = await client.post("/accounts/activate/", json=activation_payload)
    assert request_activation.status_code == 200, "Expected status code 200 for successfully activate account."

    await db_session.refresh(user)
    assert user.is_active, "User should be active after successfully activation"

    reset_request_payload = {"email": register_payload["email"]}
    request_reset = await client.post("accounts/reset_token/request", json=reset_request_payload)
    assert request_reset.status_code, "Expected status code 200 for password reset complete"

    request = select(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user.id)
    response = await db_session.execute(request)
    reset_response = response.scalar_one_or_none()
    assert reset_response is not None, "Reset token should exist in the database."

    reset_payload = {
        "email": register_payload["email"],
        "password": "NewPass123q!",
        "token": reset_response.token

    }

    reset_response = await client.post("accounts/password_reset/complete", json=reset_payload)
    assert reset_response.status_code == 200, "Expected status code 200 for successful password reset."
    assert reset_response.json()["message"] == "Password reset successfully.", (
        "Unexpected response message for password reset."
    )
