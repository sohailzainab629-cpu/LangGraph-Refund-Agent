from typing import Literal, Optional
from pydantic import BaseModel


class CustomerRequest(BaseModel):
    message: str
    thread_id: str


class ReviewRequest(BaseModel):
    approved: bool


class Classification(BaseModel):
    intent: Literal['refund', 'tracking', 'cancellation', 'complaint', 'general']
    order_id: Optional[str] = None
