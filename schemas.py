from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    price: float


class ItemResponse(ItemCreate):
    id: int
