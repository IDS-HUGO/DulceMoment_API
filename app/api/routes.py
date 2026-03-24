from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.db.database import get_db
from app.db.models import (
    DeviceToken,
    Order,
    OrderItem,
    OrderStatus,
    OrderTrackingEvent,
    Payment,
    PaymentStatus,
    Product,
    ProductOption,
    RevokedToken,
    User,
    UserRole,
)
from app.schemas.schemas import (
    AuthResponse,
    CardPaymentRequest,
    CloudinaryUploadRequest,
    CloudinaryUploadResponse,
    CreatePaymentIntentRequest,
    CreatePaymentIntentResponse,
    DeviceTokenCreate,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    OrderCreate,
    OrderRead,
    ProductCreate,
    ProductOptionCreate,
    ProductRead,
    ProductUpdate,
    UpdateOrderStatus,
    UserCreate,
    UserRead,
)
from app.services.auth import hash_password, verify_password
from app.services.cloudinary_media import is_cloudinary_configured, upload_image_file, upload_image_from_url
from app.services.jwt import create_access_token, create_refresh_token, decode_access_token
from app.services.notifications import send_push_to_tokens, tokens_for_user_ids
from app.services.payments import create_payment_intent
from app.services.pricing import calculate_custom_price

router = APIRouter()
security = HTTPBearer(auto_error=False)


def _get_existing_store(db: Session) -> User | None:
    """Retorna el vendedor existente si existe."""
    return db.query(User).filter(User.role == UserRole.store).first()


@router.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Si intenta crear un vendedor y ya existe uno, retorna el existente
    if payload.role == UserRole.store:
        existing_store = _get_existing_store(db)
        if existing_store:
            return existing_store
    
    # Si el email ya existe para otro rol, rechaza
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/register", response_model=AuthResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Si intenta crear un vendedor y ya existe uno, retorna el existente con tokens nuevos
    if payload.role == UserRole.store:
        existing_store = _get_existing_store(db)
        if existing_store:
            token = create_access_token(existing_store.id, existing_store.role.value, existing_store.email, existing_store.token_version)
            refresh_token = create_refresh_token(existing_store.id, existing_store.role.value, existing_store.email, existing_store.token_version)
            return AuthResponse(user=existing_store, access_token=token, refresh_token=refresh_token)
    
    # Si el email ya existe para otro rol, rechaza
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role.value, user.email, user.token_version)
    refresh_token = create_refresh_token(user.id, user.role.value, user.email, user.token_version)
    return AuthResponse(user=user, access_token=token, refresh_token=refresh_token)


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user.id, user.role.value, user.email, user.token_version)
    refresh_token = create_refresh_token(user.id, user.role.value, user.email, user.token_version)
    return AuthResponse(user=user, access_token=token, refresh_token=refresh_token)


def _is_token_revoked(db: Session, jti: str | None) -> bool:
    if not jti:
        return True
    return db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None


def _revoke_token_payload(db: Session, token_payload: dict, expected_user_id: int, expected_type: str):
    if token_payload.get("token_type") != expected_type:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = int(token_payload.get("sub", "0"))
    if user_id != expected_user_id:
        raise HTTPException(status_code=403, detail="Token no pertenece al usuario")

    jti = token_payload.get("jti")
    if _is_token_revoked(db, jti):
        return

    exp_timestamp = int(token_payload.get("exp", 0))
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    revoked = RevokedToken(
        jti=jti,
        user_id=expected_user_id,
        token_type=expected_type,
        expires_at=expires_at,
    )
    db.add(revoked)


@router.post("/auth/refresh", response_model=AuthResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_access_token(payload.refresh_token)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    if token_payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user_id = int(token_payload.get("sub", "0"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inválido")
    if _is_token_revoked(db, token_payload.get("jti")):
        raise HTTPException(status_code=401, detail="Refresh token revocado")
    if int(token_payload.get("tv", -1)) != user.token_version:
        raise HTTPException(status_code=401, detail="Sesión expirada, vuelve a iniciar sesión")

    _revoke_token_payload(db, token_payload, expected_user_id=user.id, expected_type="refresh")

    access_token = create_access_token(user.id, user.role.value, user.email, user.token_version)
    new_refresh_token = create_refresh_token(user.id, user.role.value, user.email, user.token_version)
    db.commit()
    return AuthResponse(user=user, access_token=access_token, refresh_token=new_refresh_token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user_id = int(payload.get("sub", "0"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario inválido")
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="Access token inválido")
    if _is_token_revoked(db, payload.get("jti")):
        raise HTTPException(status_code=401, detail="Token revocado")
    if int(payload.get("tv", -1)) != user.token_version:
        raise HTTPException(status_code=401, detail="Sesión expirada, vuelve a iniciar sesión")
    return user


def _require_store_user(current_user: User) -> User:
    if current_user.role.value != "store":
        raise HTTPException(status_code=403, detail="Acceso solo para tienda")
    return current_user


def _require_customer_user(current_user: User) -> User:
    if current_user.role.value != "customer":
        raise HTTPException(status_code=403, detail="Acceso solo para cliente")
    return current_user


@router.get("/auth/me", response_model=UserRead)
def auth_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/auth/logout")
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        refresh_payload = decode_access_token(payload.refresh_token)
        access_payload = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    _revoke_token_payload(db, refresh_payload, expected_user_id=current_user.id, expected_type="refresh")
    _revoke_token_payload(db, access_payload, expected_user_id=current_user.id, expected_type="access")
    db.commit()
    return {"ok": True}


@router.post("/auth/logout-all")
def logout_all_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.token_version += 1
    db.commit()
    return {"ok": True}


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/products", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    product = Product(
        name=payload.name,
        description=payload.description,
        base_price=payload.base_price,
        stock=payload.stock,
        image_url=payload.image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductRead])
def list_products(only_active: bool = Query(default=True), db: Session = Depends(get_db)):
    query = db.query(Product).options(joinedload(Product.options))
    if only_active:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.id.desc()).all()


@router.post("/products/{product_id}/options", response_model=ProductRead)
def add_product_option(
    product_id: int,
    payload: ProductOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    option = ProductOption(
        product_id=product.id,
        category=payload.category,
        value=payload.value,
        price_delta=payload.price_delta,
    )
    db.add(option)
    db.commit()
    db.refresh(product)
    return product


@router.post("/orders", response_model=OrderRead)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_customer_user(current_user)
    if payload.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes crear pedidos para otro usuario")
    customer = db.query(User).filter(User.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if customer.role.value != "customer":
        raise HTTPException(status_code=400, detail="Solo clientes pueden crear pedidos")

    order = Order(
        customer_id=payload.customer_id,
        delivery_address=payload.delivery_address,
        notes=payload.notes,
        status=OrderStatus.created,
        total=0,
    )
    db.add(order)
    db.flush()

    total = 0.0

    for item_payload in payload.items:
        product = db.query(Product).filter(Product.id == item_payload.product_id).first()
        if not product or not product.is_active:
            raise HTTPException(status_code=400, detail=f"Producto inválido: {item_payload.product_id}")

        if product.stock < item_payload.quantity:
            raise HTTPException(status_code=400, detail=f"Producto agotado: {product.name}")

        custom_map = {
            "size": item_payload.custom_size,
            "shape": item_payload.custom_shape,
            "flavor": item_payload.custom_flavor,
            "color": item_payload.custom_color,
        }
        unit_price = calculate_custom_price(db, product, custom_map)

        ingredients_total = 0.0
        if item_payload.custom_ingredients:
            ingredients = [value.strip() for value in item_payload.custom_ingredients.split(",") if value.strip()]
            for ingredient in ingredients:
                option = (
                    db.query(ProductOption)
                    .filter(
                        ProductOption.product_id == product.id,
                        ProductOption.category == "ingredient",
                        ProductOption.value == ingredient,
                    )
                    .first()
                )
                if option:
                    ingredients_total += option.price_delta
            unit_price += ingredients_total

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_payload.quantity,
            unit_price=round(unit_price, 2),
            custom_ingredients=item_payload.custom_ingredients,
            custom_size=item_payload.custom_size,
            custom_shape=item_payload.custom_shape,
            custom_flavor=item_payload.custom_flavor,
            custom_color=item_payload.custom_color,
        )
        db.add(item)

        product.stock -= item_payload.quantity
        total += item.quantity * item.unit_price

    order.total = round(total, 2)

    payment = Payment(order_id=order.id, amount=order.total, status=PaymentStatus.pending)
    db.add(payment)

    initial_event = OrderTrackingEvent(
        order_id=order.id,
        status=OrderStatus.created,
        message="Pedido creado y confirmado",
        eta_minutes=90,
    )
    db.add(initial_event)

    db.commit()

    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.events), joinedload(Order.payment))
        .filter(Order.id == order.id)
        .first()
    )
    return order


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.events), joinedload(Order.payment))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if current_user.role.value == "customer" and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para este pedido")
    order.events.sort(key=lambda event: event.created_at)
    return order


@router.get("/orders", response_model=list[OrderRead])
def list_orders(
    customer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Order).options(joinedload(Order.items), joinedload(Order.events), joinedload(Order.payment))
    if current_user.role.value == "customer":
        query = query.filter(Order.customer_id == current_user.id)
    elif customer_id:
        query = query.filter(Order.customer_id == customer_id)
    orders = query.all()
    for order in orders:
        order.events.sort(key=lambda event: event.created_at)
    return orders


@router.post("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: UpdateOrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    order.status = payload.status
    event = OrderTrackingEvent(
        order_id=order.id,
        status=payload.status,
        message=payload.message,
        eta_minutes=payload.eta_minutes,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(event)
    db.commit()

    message_map = {
        OrderStatus.in_oven: "Tu pastel entró al horno",
        OrderStatus.decorating: "Estamos decorando tu pastel",
        OrderStatus.on_the_way: "¡Tu pedido va en camino!",
        OrderStatus.delivered: "Entregado",
        OrderStatus.created: "Pedido confirmado",
    }
    title = "Actualización de pedido"
    body = message_map.get(payload.status, payload.message)

    tokens = tokens_for_user_ids(db, [order.customer_id])
    send_push_to_tokens(tokens, title=title, body=body, data={"order_id": str(order.id), "status": payload.status.value})

    refreshed = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.events), joinedload(Order.payment))
        .filter(Order.id == order.id)
        .first()
    )
    refreshed.events.sort(key=lambda item: item.created_at)
    return refreshed


@router.post("/payments/intent", response_model=CreatePaymentIntentResponse)
def make_payment_intent(
    payload: CreatePaymentIntentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer_user(current_user)
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order or order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para pagar este pedido")
    payment = db.query(Payment).filter(Payment.order_id == payload.order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    provider_reference, client_secret = create_payment_intent(
        payment.amount,
        metadata={"order_id": str(payload.order_id)},
    )

    payment.provider_reference = provider_reference
    if settings.enable_fake_payments:
        payment.status = PaymentStatus.approved
    db.commit()

    return CreatePaymentIntentResponse(
        payment_id=payment.id,
        provider=payment.provider,
        client_secret=client_secret,
        amount=payment.amount,
        currency=settings.stripe_currency,
    )


@router.post("/payments/{order_id}/confirm")
def confirm_payment(
    order_id: int,
    approved: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    payment.status = PaymentStatus.approved if approved else PaymentStatus.failed
    db.commit()
    return {"order_id": order_id, "payment_status": payment.status}


@router.post("/payments/card")
def pay_with_card(
    payload: CardPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_customer_user(current_user)
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order or order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para pagar este pedido")
    payment = db.query(Payment).filter(Payment.order_id == payload.order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    digits = "".join(char for char in payload.card_number if char.isdigit())
    if len(digits) < 13:
        raise HTTPException(status_code=400, detail="Tarjeta inválida")

    payment.provider_reference = f"card_ending_{digits[-4:]}"
    payment.status = PaymentStatus.approved
    db.commit()
    return {
        "ok": True,
        "order_id": payload.order_id,
        "card_last4": digits[-4:],
        "status": payment.status,
    }


@router.post("/devices/token")
def register_device_token(
    payload: DeviceTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para registrar ese dispositivo")
    token = db.query(DeviceToken).filter(DeviceToken.token == payload.token).first()
    if token:
        token.user_id = payload.user_id
        token.platform = payload.platform
    else:
        token = DeviceToken(user_id=payload.user_id, token=payload.token, platform=payload.platform)
        db.add(token)

    db.commit()
    return {"ok": True}


@router.post("/media/cloudinary/upload-url", response_model=CloudinaryUploadResponse)
def upload_product_image_url(
    payload: CloudinaryUploadRequest,
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    try:
        image_url, public_id = upload_image_from_url(payload.source_url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="No se pudo subir imagen a Cloudinary") from error

    return CloudinaryUploadResponse(image_url=image_url, public_id=public_id)


@router.post("/media/cloudinary/upload-file", response_model=CloudinaryUploadResponse)
async def upload_product_image_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    _require_store_user(current_user)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Archivo inválido: debe ser una imagen")

    try:
        image_url, public_id = upload_image_file(file.file, filename=file.filename, content_type=file.content_type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="No se pudo subir imagen a Cloudinary") from error

    return CloudinaryUploadResponse(image_url=image_url, public_id=public_id)


@router.get("/media/cloudinary/status")
def cloudinary_status(current_user: User = Depends(get_current_user)):
    _require_store_user(current_user)
    return {"configured": is_cloudinary_configured()}
