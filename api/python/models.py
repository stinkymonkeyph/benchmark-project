from typing import Optional
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    created_at: str


class EchoRequest(BaseModel):
    message: str
    data: Optional[dict] = None


class EchoResponse(BaseModel):
    message: str
    data: Optional[dict]
    timestamp: str
    processing_time_ms: float
