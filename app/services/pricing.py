from sqlalchemy.orm import Session

from app.db.models import Product, ProductOption


def calculate_custom_price(db: Session, product: Product, customizations: dict[str, str]) -> float:
    total = product.base_price
    for category, value in customizations.items():
        if not value:
            continue
        option = (
            db.query(ProductOption)
            .filter(
                ProductOption.product_id == product.id,
                ProductOption.category == category,
                ProductOption.value == value,
            )
            .first()
        )
        if option:
            total += option.price_delta
    return round(total, 2)
