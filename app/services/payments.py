import uuid

import stripe

from app.core.config import settings

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


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
