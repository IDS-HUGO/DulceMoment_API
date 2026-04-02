import uuid

import httpx
import stripe

from app.core.config import settings

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class PaymentGatewayError(Exception):
    def __init__(self, user_message: str, *, status_detail: str = "", gateway_payload: dict | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.status_detail = status_detail
        self.gateway_payload = gateway_payload or {}


def create_payment_intent(amount: float, metadata: dict[str, str]) -> tuple[str, str]:
    amount_cents = int(amount * 100)

    if settings.enable_fake_payments or not settings.stripe_secret_key:
        reference = f"fake_{uuid.uuid4()}"
        client_secret = f"fake_secret_{uuid.uuid4()}"
        return reference, client_secret

    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=settings.stripe_currency,
        payment_method_types=["card"],
        metadata=metadata,
    )
    return intent.id, intent.client_secret


def _guess_payment_method_id(card_number: str) -> str:
    digits = "".join(char for char in card_number if char.isdigit())
    if digits.startswith("4"):
        return "visa"
    if digits.startswith(tuple(str(value) for value in range(51, 56))) or digits.startswith(tuple(str(value) for value in range(2221, 2721))):
        return "master"
    if digits.startswith("34") or digits.startswith("37"):
        return "amex"
    if digits.startswith("6"):
        return "debvisa"
    return "visa"


def create_mercadopago_card_token(
    *,
    public_key: str,
    card_number: str,
    security_code: str,
    expiry_month: int,
    expiry_year: int,
    holder_name: str,
) -> str:
    url = f"https://api.mercadopago.com/v1/card_tokens?public_key={public_key}"
    payload = {
        "card_number": card_number,
        "security_code": security_code,
        "expiration_month": expiry_month,
        "expiration_year": expiry_year,
        "cardholder": {"name": holder_name},
    }
    with httpx.Client(timeout=25.0) as client:
        response = client.post(url, json=payload)
        if response.status_code >= 400:
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            cause = body.get("cause") or []
            first_cause = cause[0] if isinstance(cause, list) and cause else {}
            message = first_cause.get("description") or body.get("message") or "No se pudo tokenizar la tarjeta"
            raise PaymentGatewayError(
                f"No se pudo validar la tarjeta: {message}",
                status_detail=first_cause.get("code", ""),
                gateway_payload=body,
            )
        body = response.json()
    token_id = body.get("id")
    if not token_id:
        raise ValueError("No se pudo tokenizar la tarjeta en Mercado Pago")
    return token_id


def charge_mercadopago_card(
    *,
    access_token: str,
    amount: float,
    order_id: int,
    payer_email: str,
    card_token: str,
    payment_method_id: str,
) -> dict:
    payload = {
        "transaction_amount": round(amount, 2),
        "token": card_token,
        "description": f"DulceMoment pedido #{order_id}",
        "installments": 1,
        "payment_method_id": payment_method_id,
        "payer": {"email": payer_email},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        if response.status_code >= 400:
            cause = body.get("cause") or []
            first_cause = cause[0] if isinstance(cause, list) and cause else {}
            message = first_cause.get("description") or body.get("message") or "No fue posible procesar el pago"
            raise PaymentGatewayError(
                f"Pago rechazado: {message}",
                status_detail=first_cause.get("code", ""),
                gateway_payload=body,
            )
        return body


def get_mercadopago_payment_details(*, access_token: str, payment_id: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(timeout=25.0) as client:
        response = client.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
        if response.status_code >= 400:
            raise PaymentGatewayError("No se pudo consultar el detalle del pago", gateway_payload={"payment_id": payment_id})
        return response.json()


def charge_stripe_card_with_split(
    *,
    amount: float,
    order_id: int,
    payer_email: str,
    card_number: str,
    security_code: str,
    expiry_month: int,
    expiry_year: int,
    holder_name: str,
    connected_account_id: str,
    platform_fee_percent: float,
) -> dict:
    if not settings.stripe_secret_key:
        raise PaymentGatewayError("Pagos con Stripe no configurados")
    if not connected_account_id:
        raise PaymentGatewayError("Cuenta de vendedor Stripe no configurada")

    amount_cents = max(1, int(round(amount * 100)))
    fee_cents = int(round(amount_cents * (platform_fee_percent / 100.0)))
    fee_cents = max(0, min(fee_cents, amount_cents))

    try:
        token = stripe.Token.create(
            card={
                "number": card_number,
                "exp_month": expiry_month,
                "exp_year": expiry_year,
                "cvc": security_code,
                "name": holder_name,
            }
        )

        charge = stripe.Charge.create(
            amount=amount_cents,
            currency=settings.stripe_currency,
            source=token.id,
            description=f"DulceMoment pedido #{order_id}",
            receipt_email=payer_email,
            application_fee_amount=fee_cents,
            transfer_data={"destination": connected_account_id},
            metadata={
                "order_id": str(order_id),
                "platform_fee_percent": str(platform_fee_percent),
            },
        )
    except stripe.error.StripeError as error:
        message = getattr(error, "user_message", None) or str(error)
        raise PaymentGatewayError(f"Pago rechazado: {message}") from error

    return {
        "id": charge.get("id"),
        "status": charge.get("status"),
        "paid": bool(charge.get("paid")),
        "amount": amount_cents,
        "application_fee_amount": fee_cents,
        "destination": connected_account_id,
    }
