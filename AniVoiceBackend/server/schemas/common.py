from datetime import datetime

from pydantic import BaseModel, Field


class MetaResponse(BaseModel):
    code: str = "1"
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
