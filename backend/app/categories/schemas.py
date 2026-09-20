from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str
    category_type: str
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_type: str
    parent_id: int | None
    is_active: bool
