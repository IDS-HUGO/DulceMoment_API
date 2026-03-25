from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.db.models import OrderStatus, PaymentStatus, UserRole


class UserCreate(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.customer


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserRead
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class CloudinaryUploadRequest(BaseModel):
    source_url: str = Field(min_length=10)


class CloudinaryUploadResponse(BaseModel):
    image_url: str
    public_id: str


class ProductOptionRead(BaseModel):
    id: int
    category: str
    value: str
    price_delta: float

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    base_price: float = Field(gt=0)
    stock: int = Field(ge=0)
    image_url: str = ""


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    base_price: float
    stock: int
    is_active: bool
    image_url: str
    options: list[ProductOptionRead] = []

    class Config:
        from_attributes = True


class ProductOptionCreate(BaseModel):
    category: Literal["ingredient", "size", "shape", "flavor", "color"]
    value: str
    price_delta: float


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    custom_ingredients: str = ""
    custom_size: str = ""
    custom_shape: str = ""
    custom_flavor: str = ""
    custom_color: str = ""


class OrderCreate(BaseModel):
    customer_id: int
    delivery_address: str
    notes: str = ""
    items: list[OrderItemCreate]


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    custom_ingredients: str
    custom_size: str
    custom_shape: str
    custom_flavor: str
    custom_color: str

    class Config:
        from_attributes = True


class OrderTrackingEventRead(BaseModel):
    id: int
    status: OrderStatus
    message: str
    eta_minutes: int
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentRead(BaseModel):
    id: int
    amount: float
    provider: str
    provider_reference: str
    status: PaymentStatus

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    customer_id: int
    status: OrderStatus
    total: float
    delivery_address: str
    notes: str
    created_at: datetime
    items: list[OrderItemRead]
    events: list[OrderTrackingEventRead]
    payment: PaymentRead | None

    class Config:
        from_attributes = True


class UpdateOrderStatus(BaseModel):
    status: OrderStatus
    message: str
    eta_minutes: int = Field(default=0, ge=0)
    latitude: float = 0.0
    longitude: float = 0.0


class DeviceTokenCreate(BaseModel):
    user_id: int
    token: str
    platform: str = "android"


class CreatePaymentIntentRequest(BaseModel):
    order_id: int


class CreatePaymentIntentResponse(BaseModel):
    payment_id: int
    provider: str
    client_secret: str
    amount: float
    currency: str


class CardPaymentRequest(BaseModel):
    order_id: int
    card_number: str = Field(min_length=13)
    holder_name: str = Field(min_length=2)
    security_code: str = Field(min_length=3, max_length=4)
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=2024, le=2100)
