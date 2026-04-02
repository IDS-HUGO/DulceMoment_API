import uuid


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
