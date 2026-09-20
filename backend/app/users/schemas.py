from pydantic import BaseModel, ConfigDict, Field


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_currency: str
    timezone: str


class ProfileUpdate(BaseModel):
    name: str | None = None
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    timezone: str | None = None
