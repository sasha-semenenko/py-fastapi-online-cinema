from pydantic import BaseModel, EmailStr, field_validator
from validators import validate_password


class BaseUserSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "from_attributes": True
    }


    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password_(cls, value: str):
        return validate_password(value)


class UserResponseSchema(BaseModel):
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class UserRequestSchema(BaseUserSchema):
   pass


class UserActivationRequestSchema(BaseModel):
    email: EmailStr
    token: str


class MessageResponseSchema(BaseModel):
    message: str


class UserLoginRequestSchema(BaseUserSchema):
    pass


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
