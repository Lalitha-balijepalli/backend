from pydantic import BaseModel


class Interview(BaseModel):
    id: int | None = None
    user_id: int
    title: str
    status: str = "pending"
