from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int | None = None
    name: str
    email: EmailStr
