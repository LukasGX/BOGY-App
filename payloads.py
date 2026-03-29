from typing import Optional

from pydantic import BaseModel, Field

class CreateUserRequest(BaseModel):
    username: str = Field(..., max_length=50)
    firstname: Optional[str] = Field(..., max_length=50)
    lastname: Optional[str] = Field(..., max_length=50)
    password: str = Field(..., max_length=50)
    role: str = Field(..., max_length=15)
    class_id: Optional[int] = Field(None, alias="class", ge=0, le=9999)

class CreateClassRequest(BaseModel):
    name: str = Field(..., max_length=50, alias="className")

class PushSubscription(BaseModel):
    endpoint: str = Field(..., max_length=500)
    keys: dict[str, str]