from enum import Enum
from typing import Optional, List

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    access_token: str
    token_type: str


class User(UserBase):
    username: str
    fullname: str
    email: str
    disabled: Optional[bool] = None
    scopes: List[str] = []


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
