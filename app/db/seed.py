from sqlalchemy.orm import Session

from app.db.models import Product, ProductOption, User, UserRole
from app.services.auth import hash_password


def seed_data(db: Session) -> None:
    has_users = db.query(User).count() > 0
    if not has_users:
        db.add_all(
            [
                User(
                    name="Cliente Demo",
                    email="cliente@dulce.com",
                    password_hash=hash_password("123456"),
                    role=UserRole.customer,
                ),
                User(
                    name="Tienda Demo",
                    email="tienda@dulce.com",
                    password_hash=hash_password("123456"),
                    role=UserRole.store,
                ),
            ]
        )

    users_without_password = db.query(User).filter((User.password_hash == None) | (User.password_hash == "")).all()
    for user in users_without_password:
        user.password_hash = hash_password("123456")

    has_products = db.query(Product).count() > 0
    if has_products:
        db.commit()
        return

    products = [
        Product(
            name="Pastel Personalizado",
            description="Personaliza ingredientes, sabor, color, tamaño y forma",
            base_price=320,
            stock=12,
            image_url="",
        ),
        Product(
            name="Cupcakes Premium (6)",
            description="Caja de 6 cupcakes decorados",
            base_price=180,
            stock=20,
            image_url="",
        ),
    ]
    db.add_all(products)
    db.flush()

    options = [
        ProductOption(product_id=products[0].id, category="size", value="chico", price_delta=0),
        ProductOption(product_id=products[0].id, category="size", value="mediano", price_delta=90),
        ProductOption(product_id=products[0].id, category="size", value="grande", price_delta=170),
        ProductOption(product_id=products[0].id, category="shape", value="redondo", price_delta=0),
        ProductOption(product_id=products[0].id, category="shape", value="cuadrado", price_delta=30),
        ProductOption(product_id=products[0].id, category="shape", value="corazon", price_delta=50),
        ProductOption(product_id=products[0].id, category="flavor", value="vainilla", price_delta=0),
        ProductOption(product_id=products[0].id, category="flavor", value="chocolate", price_delta=20),
        ProductOption(product_id=products[0].id, category="flavor", value="red_velvet", price_delta=35),
        ProductOption(product_id=products[0].id, category="color", value="blanco", price_delta=0),
        ProductOption(product_id=products[0].id, category="color", value="rosa", price_delta=15),
        ProductOption(product_id=products[0].id, category="color", value="azul", price_delta=15),
        ProductOption(product_id=products[0].id, category="ingredient", value="fresa", price_delta=12),
        ProductOption(product_id=products[0].id, category="ingredient", value="oreo", price_delta=18),
        ProductOption(product_id=products[0].id, category="ingredient", value="nutella", price_delta=25),
    ]
    db.add_all(options)
    db.commit()
