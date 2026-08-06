from pydantic import BaseModel


class Report(BaseModel):
    id: int | None = None
    interview_id: int
    summary: str
