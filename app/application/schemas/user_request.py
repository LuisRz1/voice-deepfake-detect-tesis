from pydantic import BaseModel, EmailStr, Field

class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordInput(BaseModel):
    email: EmailStr

class ResetPasswordInput(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)

class ChangePasswordInput(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)
